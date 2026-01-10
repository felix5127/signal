# Input: BestBlogs Podcast OPML, RSS feeds
# Output: RawSignal 列表（播客数据，包含音频URL）
# Position: 播客采集器，从RSS获取播客元数据
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
from datetime import datetime
from typing import List, Optional

import feedparser
import httpx

from app.scrapers.base import BaseScraper, RawSignal
from app.scrapers.opml_parser import parse_opml


class PodcastScraper(BaseScraper):
    """
    播客 RSS 采集器

    从播客 RSS 源采集最新播客节目
    支持的格式：标准 RSS 2.0 + iTunes podcast extension
    """

    def __init__(self):
        super().__init__(source_name="podcast")
        self.max_concurrent = 10  # 最大并发数

    async def scrape(
        self,
        opml_path: Optional[str] = None,
        max_items_per_feed: int = 5
    ) -> List[RawSignal]:
        """
        采集播客内容

        Args:
            opml_path: OPML 文件路径，默认使用 BestBlogs Podcast 源
            max_items_per_feed: 每个播客最多抓取条数

        Returns:
            RawSignal 列表
        """
        if opml_path is None:
            opml_path = "BestBlog/BestBlogs_RSS_Podcasts.opml"

        print(f"\n[PodcastScraper] Parsing Podcast OPML from {opml_path}...")

        # 解析 OPML 获取播客 RSS 源列表
        podcast_feeds = parse_opml(opml_path, feed_type="podcast")
        print(f"[PodcastScraper] Found {len(podcast_feeds)} podcast feeds")

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
        tasks = [fetch_one(feed) for feed in podcast_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ✗ {podcast_feeds[i]['name']}: {result}")
            else:
                signals.extend(result)
                if result:
                    print(f"  ✓ {podcast_feeds[i]['name']}: {len(result)} episodes")

        print(f"\n[PodcastScraper] Total scraped: {len(signals)} podcast episodes\n")
        return signals

    async def scrape_single_feed(
        self,
        feed_url: str,
        feed_name: str,
        max_items: int = 5
    ) -> List[RawSignal]:
        """
        抓取单个播客 RSS feed

        Args:
            feed_url: Podcast RSS URL
            feed_name: 播客名称
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
                # 提取播客标题和描述
                title = entry.get("title", "")
                description = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")

                # 提取音频 URL 和时长
                audio_url = None
                duration = 0

                # 从 enclosure 获取音频文件
                if hasattr(entry, "enclosures") and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if enclosure.get("type", "").startswith("audio"):
                            audio_url = enclosure.get("href", enclosure.get("url"))
                            break

                # 从 iTunes extension 获取时长
                if hasattr(entry, "itunes_duration"):
                    duration_str = entry.itunes_duration
                    duration = self._parse_duration(duration_str)

                # 提取发布时间
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # 如果没有音频URL，跳过
                if not audio_url:
                    continue

                # 构建 RawSignal
                signal = RawSignal(
                    source="podcast",
                    source_id=link or audio_url,
                    url=link or audio_url,
                    title=title,
                    content=description,
                    source_created_at=published_at,
                    metadata={
                        "podcast_name": feed_name,
                        "audio_url": audio_url,
                        "duration": duration,
                        "type": "podcast",
                    }
                )

                signals.append(signal)

            return signals

        except Exception as e:
            print(f"  ✗ Error scraping {feed_name}: {e}")
            return []

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """
        解析播客时长

        Args:
            duration_str: 时长字符串，格式：HH:MM:SS 或 秒数

        Returns:
            时长（秒）
        """
        if not duration_str:
            return 0

        try:
            # 如果是纯数字，直接返回
            if duration_str.isdigit():
                return int(duration_str)

            # 解析 HH:MM:SS 或 MM:SS 格式
            parts = duration_str.split(":")
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 1:  # SS
                return int(parts[0])

        except Exception:
            pass

        return 0


# 测试代码
async def test_podcast_scraper():
    """测试 PodcastScraper"""
    scraper = PodcastScraper()

    # 测试抓取前 3 个播客源
    import xml.etree.ElementTree as ET
    tree = ET.parse("BestBlog/BestBlogs_RSS_Podcasts.opml")
    test_feeds = []
    for i, outline in enumerate(tree.findall('.//outline[@xmlUrl]')[:3]):
        test_feeds.append({
            "name": outline.get('text', ''),
            "url": outline.get('xmlUrl')
        })

    print(f"\n测试抓取 {len(test_feeds)} 个播客源...")
    signals = []
    for feed in test_feeds:
        feed_signals = await scraper.scrape_single_feed(feed["url"], feed["name"], max_items=3)
        signals.extend(feed_signals)

    print(f"\n总共抓取: {len(signals)} 条播客")
    if signals:
        print(f"\n示例播客:")
        for i, signal in enumerate(signals[:3]):
            print(f"\n{i+1}. {signal.title}")
            print(f"   播客: {signal.metadata.get('podcast_name')}")
            print(f"   时长: {signal.metadata.get('duration')} 秒")
            print(f"   音频: {signal.metadata.get('audio_url')[:80]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_podcast_scraper())
