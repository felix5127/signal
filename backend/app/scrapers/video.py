# Input: BestBlog/BestBlogs_RSS_Videos.opml, RSS feeds (YouTube等)
# Output: RawSignal 列表（视频数据，包含视频URL、缩略图、时长）
# Position: 视频采集器，从RSS获取视频元数据
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
from datetime import datetime
from typing import List, Optional

import feedparser
import httpx

from app.scrapers.base import BaseScraper, RawSignal
from app.scrapers.opml_parser import parse_opml


class VideoScraper(BaseScraper):
    """
    视频 RSS 采集器

    从视频 RSS 源采集最新视频内容
    支持的平台：
    - YouTube (https://www.youtube.com/feeds/videos.xml?channel_id=xxx)
    - 其他标准视频 RSS 源

    支持的格式：
    - 标准 RSS 2.0 + YouTube media extension
    """
    # YouTube 专栏表（YouTube 视频ID为11位）
    YOUTUBE_BASE_URL = "https://www.youtube.com/watch?v="

    def __init__(self):
        super().__init__(source_name="video")
        self.max_concurrent = 10  # 最大并发数

    async def scrape(
        self,
        opml_path: Optional[str] = None,
        max_items_per_feed: int = 5
    ) -> List[RawSignal]:
        """
        采集视频内容

        Args:
            opml_path: OPML 文件路径，默认使用 BestBlogs Video 源
            max_items_per_feed: 每个频道最多抓取条数

        Returns:
            RawSignal 列表
        """
        if opml_path is None:
            opml_path = "BestBlog/BestBlogs_RSS_Videos.opml"

        print(f"\n[VideoScraper] Parsing Video OPML from {opml_path}...")

        # 解析 OPML 获取视频 RSS 源列表
        video_feeds = parse_opml(opml_path, feed_type="video")
        print(f"[VideoScraper] Found {len(video_feeds)} video feeds")

        # 限制并发抓取
        signals = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_one(feed):
            async with semaphore:
                feed_signals = await self.scrape_single_feed(
                    feed["url"],
                    feed["name"],
                    max_items_per_feed
                )
                return feed_signals

        # 并发抓取所有源
        tasks = [fetch_one(feed) for feed in video_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ✗ {video_feeds[i]['name']}: {result}")
            else:
                signals.extend(result)
                if result:
                    print(f"  ✓ {video_feeds[i]['name']}: {len(result)} videos")

        print(f"\n[VideoScraper] Total scraped: {len(signals)} videos\n")
        return signals

    async def scrape_single_feed(
        self,
        feed_url: str,
        feed_name: str,
        max_items: int = 5
    ) -> List[RawSignal]:
        """
        抓取单个视频 RSS feed

        Args:
            feed_url: 视频 RSS URL
            feed_name: 频道名称
            max_items: 最多抓取条数

        Returns:
            RawSignal 列表
        """
        try:
            # 获取 RSS feed
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(feed_url)
                response.raise_for_status()

            # 解析 RSS
            feed = feedparser.parse(response.text)

            signals = []
            for entry in feed.entries[:max_items]:
                # 提取视频标题和描述
                title = entry.get("title", "")
                description = entry.get("summary", entry.get("description", ""))

                # 提取视频链接
                video_url = entry.get("link", "")

                # 提取视频ID和缩略图
                video_id = None
                thumbnail_url = None
                duration = 0

                # YouTube 特殊处理
                if "youtube.com" in feed_url:
                    # 从 link 中提取视频 ID
                    if video_url:
                        video_id = self._extract_youtube_video_id(video_url)

                    # 从 media group 提取缩略图和时长
                    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                        # YouTube 通常提供多个缩略图，取最大分辨率
                        thumbnails = entry.media_thumbnail
                        if isinstance(thumbnails, list) and len(thumbnails) > 0:
                            # 选择最后一个（通常最大分辨率）
                            thumbnail_url = thumbnails[-1].get("url", thumbnails[0].get("url"))
                        elif isinstance(thumbnails, dict):
                            thumbnail_url = thumbnails.get("url")

                    # 从 media_content 提取时长（秒）
                    if hasattr(entry, "media_yt_duration"):
                        duration = int(entry.media_yt_duration.seconds)

                # 通用视频缩略图提取
                if not thumbnail_url and hasattr(entry, "media_content"):
                    media_contents = entry.media_content
                    if isinstance(media_contents, list) and len(media_contents) > 0:
                        for media in media_contents:
                            if media.get("type", "").startswith("image"):
                                thumbnail_url = media.get("url")
                                break

                # 提取发布时间
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # 如果没有视频URL，跳过
                if not video_url:
                    continue

                # 构建 RawSignal
                signal = RawSignal(
                    source="video",
                    source_id=video_id or video_url,
                    url=video_url,
                    title=title,
                    content=description,
                    source_created_at=published_at,
                    metadata={
                        "channel_name": feed_name,
                        "video_id": video_id,
                        "thumbnail_url": thumbnail_url,
                        "duration": duration,
                        "type": "video",
                    }
                )

                signals.append(signal)

            return signals

        except Exception as e:
            print(f"  ✗ Error scraping {feed_name}: {e}")
            return []

    @staticmethod
    def _extract_youtube_video_id(url: str) -> Optional[str]:
        """
        从 YouTube URL 提取视频 ID

        Args:
            url: YouTube URL (多种格式)

        Returns:
            视频ID (11位字符)，失败返回 None

        Examples:
            - https://www.youtube.com/watch?v=VIDEO_ID
            - https://youtu.be/VIDEO_ID
            - https://www.youtube.com/embed/VIDEO_ID
        """
        import re

        # 匹配多种 YouTube URL 格式
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def get_youtube_thumbnail_url(video_id: str, quality: str = "high") -> str:
        """
        生成 YouTube 缩略图 URL

        Args:
            video_id: YouTube 视频 ID
            quality: 缩略图质量 (maxres/high/medium/default)

        Returns:
            缩略图 URL
        """
        quality_map = {
            "maxres": "maxresdefault.jpg",
            "high": "hqdefault.jpg",
            "medium": "mqdefault.jpg",
            "default": "default.jpg",
        }

        filename = quality_map.get(quality, "hqdefault.jpg")
        return f"https://img.youtube.com/vi/{video_id}/{filename}"


# 测试代码
async def test_video_scraper():
    """测试 VideoScraper"""
    scraper = VideoScraper()

    # 测试抓取前 3 个视频源
    import xml.etree.ElementTree as ET
    tree = ET.parse("BestBlog/BestBlogs_RSS_Videos.opml")
    test_feeds = []
    for i, outline in enumerate(tree.findall('.//outline[@xmlUrl]')[:3]):
        test_feeds.append({
            "name": outline.get('text', ''),
            "url": outline.get('xmlUrl')
        })

    print(f"\n测试抓取 {len(test_feeds)} 个视频源...")
    signals = []
    for feed in test_feeds:
        feed_signals = await scraper.scrape_single_feed(feed["url"], feed["name"], max_items=3)
        signals.extend(feed_signals)

    print(f"\n总共抓取: {len(signals)} 条视频")
    if signals:
        print(f"\n示例视频:")
        for i, signal in enumerate(signals[:3]):
            print(f"\n{i+1}. {signal.title}")
            print(f"   频道: {signal.metadata.get('channel_name')}")
            print(f"   时长: {signal.metadata.get('duration')} 秒")
            print(f"   视频: {signal.url[:80]}...")
            if signal.metadata.get('thumbnail_url'):
                print(f"   缩略图: {signal.metadata.get('thumbnail_url')[:80]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_video_scraper())
