# Input: RSS Feed URLs (config.yaml)
# Output: RawSignal 列表(博客/播客文章)
# Position: 博客/播客数据源爬虫,通过RSS订阅抓取优质内容
# 更新提醒:一旦我被更新,务必更新我的开头注释,以及所属的文件夹的md

from datetime import datetime, timezone
from typing import List
import httpx
import feedparser
from html import unescape
import re

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class BlogScraper(BaseScraper):
    """
    博客/播客 RSS 爬虫

    数据源:RSS Feed (完全免费,标准化协议)
    优势:
    1. 稳定可靠 - RSS 协议标准化,不易失效
    2. 内容质量高 - 博主/播主通常会写深度内容
    3. 完全免费 - 无需 API key
    4. 易于扩展 - 只需添加 RSS URL 即可

    支持:
    - 博客文章 RSS (如个人博客、技术博客)
    - 播客 RSS (如小宇宙、Apple Podcasts)
    - 微信公众号 RSS (通过 RSSHub 转换)
    """

    def __init__(self):
        super().__init__(source_name="blog")
        self.feeds = config.blog.feeds if hasattr(config, 'blog') else []
        self.keywords = [kw.lower() for kw in config.blog.keywords] if hasattr(config.blog, 'keywords') else []
        self.max_items_per_feed = config.blog.max_items_per_feed if hasattr(config.blog, 'max_items_per_feed') else 10

    def _clean_html(self, html_text: str) -> str:
        """
        清理 HTML 标签,提取纯文本

        Args:
            html_text: HTML 文本

        Returns:
            纯文本
        """
        if not html_text:
            return ""

        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html_text)
        # HTML 实体解码
        text = unescape(text)
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _matches_keywords(self, title: str, content: str) -> bool:
        """
        检查文章是否包含关键词

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            是否匹配
        """
        if not self.keywords:
            return True  # 如果没有配置关键词,全部通过

        text = f"{title} {content}".lower()
        return any(keyword in text for keyword in self.keywords)

    def _parse_date(self, date_str: str) -> datetime:
        """
        解析 RSS feed 中的日期

        Args:
            date_str: 日期字符串

        Returns:
            datetime 对象
        """
        try:
            # feedparser 已经解析了日期为 time.struct_time
            # 我们需要将其转换为 datetime
            import time
            if isinstance(date_str, time.struct_time):
                return datetime(*date_str[:6], tzinfo=timezone.utc)
            elif isinstance(date_str, str):
                # 尝试解析常见的日期格式
                from dateutil import parser
                return parser.parse(date_str)
            else:
                return datetime.now(timezone.utc)
        except Exception as e:
            print(f"[Blog] Failed to parse date '{date_str}': {e}")
            return datetime.now(timezone.utc)

    def _convert_to_raw_signal(self, entry: dict, feed_info: dict) -> RawSignal:
        """
        转换 RSS entry 为 RawSignal

        Args:
            entry: feedparser entry 对象
            feed_info: RSS feed 元信息

        Returns:
            RawSignal 对象
        """
        # 提取标题
        title = entry.get('title', 'No title')

        # 提取内容 (优先级: content > summary > description)
        content = ""
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].get('value', '')
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description

        # 清理 HTML
        clean_content = self._clean_html(content)

        # 提取发布时间
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = self._parse_date(entry.published_parsed)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = self._parse_date(entry.updated_parsed)

        # 提取 URL
        url = entry.get('link', '')

        # 提取作者
        author = entry.get('author', feed_info.get('title', 'Unknown'))

        # 生成唯一 ID
        entry_id = entry.get('id', url)

        return RawSignal(
            source=self.source_name,
            source_id=f"blog_{entry_id}",
            url=url,
            title=title[:500],  # 限制长度
            content=clean_content[:5000],  # 限制长度,只取前5000字符
            source_created_at=published,
            metadata={
                "author": author,
                "feed_title": feed_info.get('title', ''),
                "feed_url": feed_info.get('url', ''),
                "entry_id": entry_id,
            },
        )

    async def _scrape_feed(self, client: httpx.AsyncClient, feed_url: str) -> List[RawSignal]:
        """
        抓取单个 RSS feed

        Args:
            client: httpx 客户端
            feed_url: RSS feed URL

        Returns:
            RawSignal 列表
        """
        signals = []

        try:
            print(f"[Blog] Fetching feed: {feed_url}")

            # 获取 RSS feed
            resp = await client.get(feed_url, timeout=30.0, follow_redirects=True)
            resp.raise_for_status()

            # 解析 RSS
            feed = feedparser.parse(resp.text)

            if feed.bozo:
                # RSS 解析错误
                print(f"[Blog] Feed parsing error: {feed.bozo_exception}")
                return signals

            feed_info = {
                'title': feed.feed.get('title', 'Unknown Feed'),
                'url': feed_url,
            }

            print(f"[Blog] Found {len(feed.entries)} entries from '{feed_info['title']}'")

            # 规则预筛
            filtered_count = 0
            for entry in feed.entries[:self.max_items_per_feed]:
                # 提取标题和内容
                title = entry.get('title', '')
                content = ""
                if hasattr(entry, 'summary'):
                    content = self._clean_html(entry.summary)

                # 关键词过滤
                if not self._matches_keywords(title, content):
                    continue

                signal = self._convert_to_raw_signal(entry, feed_info)
                signals.append(signal)
                filtered_count += 1

            print(f"[Blog] {feed_info['title']}: {filtered_count}/{len(feed.entries)} passed filter")

        except Exception as e:
            print(f"[Blog] Failed to scrape feed {feed_url}: {e}")

        return signals

    async def scrape(self) -> List[RawSignal]:
        """
        抓取所有配置的 RSS feeds

        流程:
        1. 遍历配置的 RSS feed 列表
        2. 使用 feedparser 解析每个 feed
        3. 规则预筛(关键词过滤)
        4. 转换为 RawSignal

        Returns:
            RawSignal 列表(已通过规则预筛)
        """
        all_signals = []

        async with httpx.AsyncClient() as client:
            for feed_url in self.feeds:
                feed_signals = await self._scrape_feed(client, feed_url)
                all_signals.extend(feed_signals)

                # 避免请求过快
                import asyncio
                await asyncio.sleep(1)

        print(f"[Blog] Total: {len(all_signals)} signals from {len(self.feeds)} feeds")
        return all_signals
