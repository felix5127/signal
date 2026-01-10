# Input: OPML 文件路径、feedparser 库、httpx 异步客户端
# Output: RawSignal 列表（RSS 源的文章元数据）
# Position: RSS 数据源爬虫，解析 OPML 获取 Feed 列表并抓取最新内容
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import feedparser
import httpx

from app.scrapers.base import BaseScraper, RawSignal


def parse_opml(file_path: str) -> List[Dict[str, str]]:
    """
    解析 OPML 文件，返回 RSS 源列表

    Args:
        file_path: OPML 文件路径

    Returns:
        [{"name": "源名称", "url": "https://..."}]
    """
    feeds = []
    try:
        tree = ElementTree.parse(file_path)
        root = tree.getroot()

        # OPML 2.0 结构: opml -> body -> outline (可嵌套)
        # 查找所有带 xmlUrl 属性的 outline 元素
        for outline in root.findall('.//outline[@xmlUrl]'):
            xml_url = outline.get('xmlUrl')
            if xml_url:
                feeds.append({
                    "name": outline.get('title') or outline.get('text', ''),
                    "url": xml_url,
                    "type": outline.get('type', 'rss')
                })
    except Exception as e:
        print(f"[RSS] 解析 OPML 文件失败 {file_path}: {e}")

    return feeds


class RSSScraper(BaseScraper):
    """
    RSS 源爬虫

    功能：
    1. 解析 OPML 文件获取 RSS 源列表
    2. 异步并发抓取所有 RSS 源
    3. 将 feed entry 转换为 RawSignal 格式
    4. 支持增量更新（通过 URL 去重）

    特性：
    - 并发控制（避免被封）
    - 超时处理
    - 错误容忍（单个 feed 失败不影响整体）
    """

    # 默认 OPML 文件路径（相对于项目根目录）
    DEFAULT_OPML_PATH = "BestBlog/BestBlogs_RSS_Articles.opml"

    # 并发控制
    MAX_CONCURRENT_REQUESTS = 10  # 最大并发数
    REQUEST_TIMEOUT = 30.0  # 单个请求超时（秒）

    def __init__(self, opml_path: Optional[str] = None):
        """
        初始化 RSS 爬虫

        Args:
            opml_path: OPML 文件路径，默认使用 BestBlogs 文章源
        """
        super().__init__(source_name="rss")
        self.opml_path = opml_path or self.DEFAULT_OPML_PATH
        self.feeds: List[Dict[str, str]] = []
        self._seen_urls: set = set()  # 用于 URL 去重

    def _load_feeds(self) -> List[Dict[str, str]]:
        """
        加载 OPML 文件中的 RSS 源列表

        Returns:
            RSS 源列表
        """
        # 尝试多个可能的路径
        possible_paths = [
            self.opml_path,
            Path(__file__).parent.parent.parent.parent / self.opml_path,  # 从 backend 目录
            Path.cwd() / self.opml_path,  # 从当前工作目录
        ]

        for path in possible_paths:
            path = Path(path)
            if path.exists():
                print(f"[RSS] 加载 OPML 文件: {path}")
                feeds = parse_opml(str(path))
                print(f"[RSS] 发现 {len(feeds)} 个 RSS 源")
                return feeds

        print(f"[RSS] 警告: 未找到 OPML 文件，尝试的路径: {possible_paths}")
        return []

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        feed_url: str,
        feed_name: str
    ) -> List[dict]:
        """
        获取单个 RSS feed 的条目

        Args:
            client: httpx 异步客户端
            feed_url: RSS feed URL
            feed_name: RSS 源名称（用于日志）

        Returns:
            feed 条目列表
        """
        async def _do_fetch():
            resp = await client.get(
                feed_url,
                timeout=self.REQUEST_TIMEOUT,
                follow_redirects=True
            )
            resp.raise_for_status()
            return resp.text

        try:
            content = await self.fetch_with_retry(_do_fetch)
            # feedparser 是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(
                None,
                lambda: feedparser.parse(content)
            )

            if parsed.bozo and not parsed.entries:
                # bozo 表示解析有问题，但如果有 entries 可能只是警告
                print(f"[RSS] 解析警告 {feed_name}: {parsed.bozo_exception}")
                return []

            return parsed.entries

        except httpx.TimeoutException:
            print(f"[RSS] 超时 {feed_name}: {feed_url}")
            return []
        except httpx.HTTPStatusError as e:
            print(f"[RSS] HTTP 错误 {feed_name}: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"[RSS] 抓取失败 {feed_name}: {e}")
            return []

    def _parse_datetime(self, entry: dict) -> Optional[datetime]:
        """
        解析 feed entry 的发布时间

        Args:
            entry: feedparser entry 对象

        Returns:
            datetime 对象，解析失败返回 None
        """
        # feedparser 会将时间解析为 time.struct_time
        time_fields = ['published_parsed', 'updated_parsed', 'created_parsed']

        for field in time_fields:
            time_struct = entry.get(field)
            if time_struct:
                try:
                    return datetime(*time_struct[:6])
                except (TypeError, ValueError):
                    continue

        return None

    def _to_raw_signal(self, entry: dict, source_name: str) -> Optional[RawSignal]:
        """
        将 feed entry 转换为 RawSignal

        Args:
            entry: feedparser entry 对象
            source_name: RSS 源名称

        Returns:
            RawSignal 对象，URL 重复或缺失则返回 None
        """
        # 获取 URL（必需字段）
        url = entry.get('link', '')
        if not url:
            return None

        # URL 去重
        if url in self._seen_urls:
            return None
        self._seen_urls.add(url)

        # 获取标题（必需字段）
        title = entry.get('title', '').strip()
        if not title:
            return None

        # 获取内容/摘要
        content = ''
        if entry.get('content'):
            # content 是一个列表，取第一个
            content = entry['content'][0].get('value', '')
        elif entry.get('summary'):
            content = entry['summary']
        elif entry.get('description'):
            content = entry['description']

        # 获取作者
        author = entry.get('author', '')
        if not author and entry.get('authors'):
            authors = entry['authors']
            if authors and isinstance(authors, list):
                author = authors[0].get('name', '')

        # 获取发布时间
        published_at = self._parse_datetime(entry)

        # 构建元数据
        metadata: Dict[str, Any] = {
            "source_name": source_name,
            "author": author,
        }

        # 添加标签（如果有）
        if entry.get('tags'):
            tags = [tag.get('term', '') for tag in entry['tags'] if tag.get('term')]
            if tags:
                metadata["tags"] = tags

        # 添加 feed ID（如果有）
        if entry.get('id'):
            metadata["feed_id"] = entry['id']

        return RawSignal(
            source=self.source_name,
            source_id=entry.get('id', url),  # 优先使用 entry id，否则用 URL
            url=url,
            title=title,
            content=content if content else None,
            source_created_at=published_at,
            metadata=metadata
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取所有 RSS 源的最新内容

        流程：
        1. 加载 OPML 文件获取 RSS 源列表
        2. 使用信号量控制并发数
        3. 异步抓取所有 feed
        4. 转换为 RawSignal 格式
        5. URL 去重

        Returns:
            RawSignal 列表
        """
        # 重置去重集合
        self._seen_urls.clear()

        # 加载 RSS 源列表
        self.feeds = self._load_feeds()
        if not self.feeds:
            print("[RSS] 没有可用的 RSS 源")
            return []

        signals: List[RawSignal] = []
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

        async def fetch_with_semaphore(
            client: httpx.AsyncClient,
            feed: Dict[str, str]
        ) -> List[RawSignal]:
            """带信号量控制的抓取"""
            async with semaphore:
                entries = await self._fetch_feed(
                    client,
                    feed["url"],
                    feed["name"]
                )
                feed_signals = []
                for entry in entries:
                    signal = self._to_raw_signal(entry, feed["name"])
                    if signal:
                        feed_signals.append(signal)
                return feed_signals

        # 统计信息
        total_feeds = len(self.feeds)
        success_count = 0
        error_count = 0
        total_entries = 0

        print(f"[RSS] 开始抓取 {total_feeds} 个 RSS 源...")

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; SignalHunter/1.0; RSS Reader)"
            }
        ) as client:
            # 创建所有任务
            tasks = [
                fetch_with_semaphore(client, feed)
                for feed in self.feeds
            ]

            # 并发执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    print(f"[RSS] 异常 {self.feeds[i]['name']}: {result}")
                elif isinstance(result, list):
                    if result:
                        success_count += 1
                        total_entries += len(result)
                        signals.extend(result)
                    else:
                        # 空结果也算成功（可能是没有新内容）
                        success_count += 1

        print(
            f"[RSS] 抓取完成: {success_count}/{total_feeds} 成功, "
            f"{error_count} 错误, {len(signals)} 条目 (去重后)"
        )

        return signals

    async def scrape_single_feed(self, feed_url: str, feed_name: str = "Unknown") -> List[RawSignal]:
        """
        抓取单个 RSS 源（用于测试或手动添加源）

        Args:
            feed_url: RSS feed URL
            feed_name: RSS 源名称

        Returns:
            RawSignal 列表
        """
        signals = []
        self._seen_urls.clear()

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; SignalHunter/1.0; RSS Reader)"
            }
        ) as client:
            entries = await self._fetch_feed(client, feed_url, feed_name)
            for entry in entries:
                signal = self._to_raw_signal(entry, feed_name)
                if signal:
                    signals.append(signal)

        print(f"[RSS] 单源抓取: {feed_name} -> {len(signals)} 条目")
        return signals
