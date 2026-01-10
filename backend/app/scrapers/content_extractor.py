# Input: URL 字符串
# Output: ExtractedContent (HTML、Markdown、字数、阅读时长)
# Position: 全文提取模块，使用 Playwright 抓取页面内容并转换为 Markdown
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import re
import asyncio
from typing import Optional, List
from dataclasses import dataclass

import html2text
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

import structlog

logger = structlog.get_logger()


@dataclass
class ExtractedContent:
    """
    提取的内容数据结构

    属性:
        html: 原始 HTML 内容
        markdown: 转换后的 Markdown 内容
        word_count: 字数统计（中文按字符，英文按单词）
        read_time: 预估阅读时长（分钟）
    """
    html: str
    markdown: str
    word_count: int
    read_time: int  # 分钟


class ContentExtractor:
    """
    Playwright 全文提取器

    功能：
    - 使用 Playwright 访问文章 URL（支持 JavaScript 渲染页面）
    - 智能选择器提取正文内容
    - HTML 转 Markdown
    - 计算字数和阅读时长

    使用示例：
        extractor = ContentExtractor()
        content = await extractor.extract("https://example.com/article")
        if content:
            print(content.markdown)
    """

    # 正文提取的选择器优先级列表
    CONTENT_SELECTORS: List[str] = [
        "article",
        "main article",
        ".post-content",
        ".article-content",
        ".entry-content",
        ".content-body",
        ".blog-post-content",
        ".markdown-body",
        "[role='main'] article",
        "#content article",
        "#main-content",
        "#article-content",
        "main",
        "#content",
        ".post",
        ".article",
    ]

    # 需要移除的无关元素选择器
    REMOVE_SELECTORS: List[str] = [
        "nav",
        "header",
        "footer",
        ".sidebar",
        ".comments",
        ".comment-section",
        ".related-posts",
        ".advertisement",
        ".ads",
        ".social-share",
        ".author-bio",
        ".newsletter-signup",
        "script",
        "style",
        "noscript",
        "iframe",
    ]

    # 阅读速度（每分钟）
    CHINESE_READING_SPEED = 400  # 中文：400字/分钟
    ENGLISH_READING_SPEED = 200  # 英文：200词/分钟

    # 超时设置
    DEFAULT_TIMEOUT = 30000  # 30秒（毫秒）

    def __init__(self):
        """初始化内容提取器"""
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # 不换行
        self.h2t.unicode_snob = True  # 使用 Unicode 字符
        self.h2t.skip_internal_links = True  # 跳过内部锚点链接

    async def extract(self, url: str) -> Optional[ExtractedContent]:
        """
        提取 URL 的正文内容

        Args:
            url: 文章 URL

        Returns:
            ExtractedContent 对象，失败返回 None
        """
        try:
            async with async_playwright() as p:
                # 启动浏览器（无头模式）
                browser = await p.chromium.launch(headless=True)

                # 创建上下文，模拟真实浏览器
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                )

                page = await context.new_page()

                try:
                    # 访问页面，等待网络空闲
                    await page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.DEFAULT_TIMEOUT
                    )

                    # 额外等待，确保动态内容加载完成
                    await asyncio.sleep(1)

                    # 提取正文内容
                    html_content = await self._get_article_content(page)

                    if not html_content or len(html_content.strip()) < 100:
                        logger.warning("提取内容过短或为空", url=url)
                        return None

                    # 转换为 Markdown
                    markdown_content = self._html_to_markdown(html_content)

                    # 计算字数和阅读时长
                    word_count = self._count_words(markdown_content)
                    read_time = self._calculate_read_time(markdown_content)

                    logger.info(
                        "内容提取成功",
                        url=url,
                        word_count=word_count,
                        read_time=read_time
                    )

                    return ExtractedContent(
                        html=html_content,
                        markdown=markdown_content,
                        word_count=word_count,
                        read_time=read_time
                    )

                except PlaywrightTimeoutError:
                    logger.error("页面加载超时", url=url)
                    return None

                finally:
                    await browser.close()

        except Exception as e:
            logger.error("内容提取失败", url=url, error=str(e))
            return None

    async def _get_article_content(self, page: Page) -> str:
        """
        使用多种选择器尝试提取正文

        策略：
        1. 先移除无关元素（导航、广告等）
        2. 按优先级尝试多个选择器
        3. 返回第一个有效的内容

        Args:
            page: Playwright Page 对象

        Returns:
            正文 HTML 字符串
        """
        # 移除无关元素
        for selector in self.REMOVE_SELECTORS:
            try:
                await page.evaluate(f'''
                    document.querySelectorAll("{selector}").forEach(el => el.remove());
                ''')
            except Exception:
                pass  # 忽略移除失败的情况

        # 按优先级尝试选择器
        for selector in self.CONTENT_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    html = await element.inner_html()
                    # 检查内容是否有意义（至少 200 字符）
                    if html and len(html.strip()) > 200:
                        logger.debug("找到正文", selector=selector)
                        return html
            except Exception:
                continue

        # 如果所有选择器都失败，尝试获取 body 内容
        try:
            body = await page.query_selector("body")
            if body:
                return await body.inner_html()
        except Exception:
            pass

        return ""

    def _html_to_markdown(self, html: str) -> str:
        """
        将 HTML 转换为 Markdown

        Args:
            html: HTML 字符串

        Returns:
            Markdown 字符串
        """
        try:
            markdown = self.h2t.handle(html)
            # 清理多余空行
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
            return markdown.strip()
        except Exception as e:
            logger.error("HTML 转 Markdown 失败", error=str(e))
            return ""

    def _count_words(self, text: str) -> int:
        """
        计算字数

        规则：
        - 中文：按字符数计算
        - 英文：按空格分隔的单词数计算

        Args:
            text: 文本内容

        Returns:
            字数
        """
        # 移除 Markdown 标记
        clean_text = re.sub(r'[#*`\[\]()!>\-_]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))

        # 计算英文单词数（移除中文后按空格分割）
        english_text = re.sub(r'[\u4e00-\u9fff]', ' ', clean_text)
        english_words = len([w for w in english_text.split() if w.strip()])

        return chinese_chars + english_words

    def _calculate_read_time(self, text: str) -> int:
        """
        计算阅读时长

        规则：
        - 中文：400字/分钟
        - 英文：200词/分钟
        - 混合内容：分别计算后加和

        Args:
            text: 文本内容

        Returns:
            阅读时长（分钟），最少 1 分钟
        """
        # 移除 Markdown 标记
        clean_text = re.sub(r'[#*`\[\]()!>\-_]', '', text)

        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))

        # 计算英文单词数
        english_text = re.sub(r'[\u4e00-\u9fff]', ' ', clean_text)
        english_words = len([w for w in english_text.split() if w.strip()])

        # 计算阅读时长
        chinese_time = chinese_chars / self.CHINESE_READING_SPEED
        english_time = english_words / self.ENGLISH_READING_SPEED

        total_time = chinese_time + english_time

        # 至少 1 分钟，向上取整
        return max(1, round(total_time + 0.5))

    async def extract_batch(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[Optional[ExtractedContent]]:
        """
        批量提取多个 URL 的内容

        使用信号量控制并发数，避免资源耗尽

        Args:
            urls: URL 列表
            max_concurrent: 最大并发数

        Returns:
            ExtractedContent 列表（与 urls 顺序对应）
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_limit(url: str) -> Optional[ExtractedContent]:
            async with semaphore:
                return await self.extract(url)

        tasks = [extract_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return list(results)
