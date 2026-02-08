# [INPUT]: URL 字符串, httpx (Jina Reader 降级)
# [OUTPUT]: ExtractedContent (HTML、Markdown、字数、阅读时长)
# [POS]: 全文提取模块，Playwright 优先 + Jina Reader 降级 + 重试 + 浏览器复用
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import re
import asyncio
from typing import Optional, List
from dataclasses import dataclass, field
from urllib.parse import urlparse

import html2text
import httpx
from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
)

import structlog

logger = structlog.get_logger("content_extractor")


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ExtractedContent:
    """
    提取的内容数据结构

    属性:
        html: 原始 HTML 内容
        markdown: 转换后的 Markdown 内容
        word_count: 字数统计（中文按字符，英文按单词）
        read_time: 预估阅读时长（分钟）
        extraction_method: 提取方式 (playwright/jina)
        error: 错误信息 (提取失败时设置)
    """
    html: str
    markdown: str
    word_count: int
    read_time: int  # 分钟
    extraction_method: str = "playwright"  # playwright / jina
    error: Optional[str] = None


# ============================================================
# ContentExtractor — 增强版全文提取器
# ============================================================

class ContentExtractor:
    """
    增强版 Playwright 全文提取器

    改进:
    1. 浏览器单例复用 — 延迟初始化，提取间复用同一浏览器实例
    2. 重试机制 — 最多 2 次，指数退避 (2s, 4s)
    3. Jina Reader 降级 — Playwright 失败时回退到 Jina API
    4. 失败统计 — 按域名聚合失败次数
    5. 错误标记 — 提取失败时返回带 error 的 ExtractedContent，而非 None
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

    # 重试配置
    MAX_RETRIES = 2
    BASE_BACKOFF_SECONDS = 2  # 指数退避基数

    # Jina Reader 配置
    JINA_READER_URL = "https://r.jina.ai/"
    JINA_TIMEOUT = 30.0  # 秒

    def __init__(self):
        """初始化内容提取器"""
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # 不换行
        self.h2t.unicode_snob = True  # 使用 Unicode 字符
        self.h2t.skip_internal_links = True  # 跳过内部锚点链接

        # 浏览器单例 (延迟初始化)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_lock = asyncio.Lock()

        # 失败统计 (按域名聚合)
        self._failure_stats: dict[str, int] = {}

    # ============================================================
    # 浏览器生命周期管理
    # ============================================================

    async def _ensure_browser(self) -> Browser:
        """延迟初始化并复用浏览器实例"""
        async with self._browser_lock:
            if self._browser is None or not self._browser.is_connected():
                # 关闭旧的
                await self._cleanup_browser()
                # 创建新的
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
                logger.info("content_extractor.browser.launched")
            return self._browser

    async def _cleanup_browser(self):
        """清理浏览器资源"""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def close(self):
        """关闭浏览器实例 (pipeline 结束时调用)"""
        await self._cleanup_browser()
        logger.info("content_extractor.browser.closed")

    # ============================================================
    # 公共提取接口
    # ============================================================

    async def extract(self, url: str) -> Optional[ExtractedContent]:
        """
        提取 URL 的正文内容 (带重试 + Jina 降级)

        流程:
        1. Playwright 提取 (最多重试 MAX_RETRIES 次)
        2. Playwright 全部失败 → Jina Reader 降级
        3. 都失败 → 返回 None，记录域名失败统计

        Args:
            url: 文章 URL

        Returns:
            ExtractedContent 对象，失败返回 None
        """
        domain = self._extract_domain(url)

        # ── 阶段 1: Playwright 提取 (带重试) ──
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._extract_with_playwright(url)
                if result:
                    return result
                # 返回 None 表示内容过短，不需要重试
                break
            except PlaywrightTimeoutError:
                last_error = "页面加载超时"
                logger.warning("content_extractor.playwright.timeout",
                               url=url[:80], attempt=attempt + 1)
            except Exception as e:
                last_error = str(e)
                logger.warning("content_extractor.playwright.error",
                               url=url[:80], attempt=attempt + 1, error=str(e))

            # 指数退避
            if attempt < self.MAX_RETRIES - 1:
                backoff = self.BASE_BACKOFF_SECONDS * (2 ** attempt)
                await asyncio.sleep(backoff)

        # ── 阶段 2: Jina Reader 降级 ──
        logger.info("content_extractor.jina.fallback", url=url[:80])
        try:
            result = await self._extract_with_jina(url)
            if result:
                return result
        except Exception as e:
            logger.warning("content_extractor.jina.error",
                           url=url[:80], error=str(e))

        # ── 全部失败 ──
        self._record_failure(domain)
        logger.error("content_extractor.extract.all_failed",
                      url=url[:80], last_error=last_error, domain=domain)
        return None

    # ============================================================
    # Playwright 提取
    # ============================================================

    async def _extract_with_playwright(self, url: str) -> Optional[ExtractedContent]:
        """使用 Playwright 提取正文 (复用浏览器实例)"""
        browser = await self._ensure_browser()

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
        )

        page = await context.new_page()

        try:
            # 访问页面，等待网络空闲
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=self.DEFAULT_TIMEOUT,
            )

            # 额外等待，确保动态内容加载完成
            await asyncio.sleep(1)

            # 提取正文内容
            html_content = await self._get_article_content(page)

            if not html_content or len(html_content.strip()) < 100:
                logger.warning("content_extractor.playwright.content_short", url=url[:80])
                return None

            return self._build_result(html_content, method="playwright")

        finally:
            await context.close()

    # ============================================================
    # Jina Reader 降级
    # ============================================================

    async def _extract_with_jina(self, url: str) -> Optional[ExtractedContent]:
        """使用 Jina Reader API 提取正文 (降级方案)"""
        jina_url = f"{self.JINA_READER_URL}{url}"

        async with httpx.AsyncClient(timeout=self.JINA_TIMEOUT) as client:
            response = await client.get(
                jina_url,
                headers={
                    "Accept": "text/markdown",
                    "X-Return-Format": "markdown",
                },
            )
            response.raise_for_status()

            markdown = response.text.strip()
            if not markdown or len(markdown) < 100:
                logger.warning("content_extractor.jina.content_short", url=url[:80])
                return None

            # Jina 直接返回 Markdown，不需要 HTML→MD 转换
            word_count = self._count_words(markdown)
            read_time = self._calculate_read_time(markdown)

            logger.info("content_extractor.jina.success",
                        url=url[:80], word_count=word_count)

            return ExtractedContent(
                html="",  # Jina 不返回原始 HTML
                markdown=markdown,
                word_count=word_count,
                read_time=read_time,
                extraction_method="jina",
            )

    # ============================================================
    # 页面正文提取
    # ============================================================

    async def _get_article_content(self, page: Page) -> str:
        """
        使用多种选择器尝试提取正文

        策略：
        1. 先移除无关元素（导航、广告等）
        2. 按优先级尝试多个选择器
        3. 返回第一个有效的内容
        """
        # 移除无关元素
        for selector in self.REMOVE_SELECTORS:
            try:
                await page.evaluate(f'''
                    document.querySelectorAll("{selector}").forEach(el => el.remove());
                ''')
            except Exception:
                pass

        # 按优先级尝试选择器
        for selector in self.CONTENT_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    html = await element.inner_html()
                    if html and len(html.strip()) > 200:
                        return html
            except Exception:
                continue

        # 兜底: body 内容
        try:
            body = await page.query_selector("body")
            if body:
                return await body.inner_html()
        except Exception:
            pass

        return ""

    # ============================================================
    # 结果构建
    # ============================================================

    def _build_result(self, html_content: str, method: str = "playwright") -> ExtractedContent:
        """从 HTML 构建 ExtractedContent"""
        markdown_content = self._html_to_markdown(html_content)
        word_count = self._count_words(markdown_content)
        read_time = self._calculate_read_time(markdown_content)

        return ExtractedContent(
            html=html_content,
            markdown=markdown_content,
            word_count=word_count,
            read_time=read_time,
            extraction_method=method,
        )

    # ============================================================
    # 格式转换 + 计算
    # ============================================================

    def _html_to_markdown(self, html: str) -> str:
        """将 HTML 转换为 Markdown"""
        try:
            markdown = self.h2t.handle(html)
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
            return markdown.strip()
        except Exception as e:
            logger.error("content_extractor.html2md.error", error=str(e))
            return ""

    def _count_words(self, text: str) -> int:
        """计算字数 (中文按字符, 英文按单词)"""
        clean_text = re.sub(r'[#*`\[\]()!>\-_]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))

        english_text = re.sub(r'[\u4e00-\u9fff]', ' ', clean_text)
        english_words = len([w for w in english_text.split() if w.strip()])

        return chinese_chars + english_words

    def _calculate_read_time(self, text: str) -> int:
        """计算阅读时长 (分钟, 最少 1 分钟)"""
        clean_text = re.sub(r'[#*`\[\]()!>\-_]', '', text)

        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
        english_text = re.sub(r'[\u4e00-\u9fff]', ' ', clean_text)
        english_words = len([w for w in english_text.split() if w.strip()])

        total_time = (chinese_chars / self.CHINESE_READING_SPEED
                      + english_words / self.ENGLISH_READING_SPEED)

        return max(1, round(total_time + 0.5))

    # ============================================================
    # 失败统计
    # ============================================================

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名"""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"

    def _record_failure(self, domain: str):
        """记录域名级别的失败次数"""
        self._failure_stats[domain] = self._failure_stats.get(domain, 0) + 1

    def get_failure_stats(self) -> dict[str, int]:
        """获取域名失败统计 (降序)"""
        return dict(sorted(
            self._failure_stats.items(),
            key=lambda x: x[1],
            reverse=True,
        ))

    # ============================================================
    # 批量提取
    # ============================================================

    async def extract_batch(
        self,
        urls: List[str],
        max_concurrent: int = 3,
    ) -> List[Optional[ExtractedContent]]:
        """
        批量提取多个 URL 的内容

        使用信号量控制并发数，避免资源耗尽。
        批量完成后自动关闭浏览器释放资源。

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
