# Input: BestBlogs Twitter OPML, XGo.ing RSS API
# Output: RawSignal 列表（推文数据）
# Position: Twitter 采集器，通过 XGo.ing 服务将 Twitter 转为 RSS
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
from datetime import datetime
from typing import List, Optional

import feedparser
import httpx

from app.scrapers.base import BaseScraper, RawSignal
from app.scrapers.opml_parser import parse_opml


class XGoingScraper(BaseScraper):
    """
    通过 XGo.ing 服务采集 Twitter 推文

    XGo.ing 是一个将 Twitter 账号转换为 RSS feed 的服务
    URL 格式: https://api.xgo.ing/rss/user/{user_id}
    """

    def __init__(self):
        super().__init__(source_name="twitter")
        self.max_concurrent = 10  # 最大并发数

    async def scrape(
        self,
        opml_path: Optional[str] = None,
        max_items_per_feed: int = 10
    ) -> List[RawSignal]:
        """
        采集 Twitter 推文

        Args:
            opml_path: OPML 文件路径，默认使用 BestBlogs Twitter 源
            max_items_per_feed: 每个账号最多抓取条数

        Returns:
            RawSignal 列表
        """
        if opml_path is None:
            opml_path = "/app/data/BestBlogs_RSS_Twitters.opml"

        print(f"\n[XGoingScraper] Parsing Twitter OPML from {opml_path}...")

        # 解析 OPML 获取 XGo.ing RSS 源列表
        twitter_feeds = parse_opml(opml_path, feed_type="twitter")
        print(f"[XGoingScraper] Found {len(twitter_feeds)} Twitter accounts")

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
        tasks = [fetch_one(feed) for feed in twitter_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ✗ {twitter_feeds[i]['name']}: {result}")
            else:
                signals.extend(result)
                if result:
                    print(f"  ✓ {twitter_feeds[i]['name']}: {len(result)} tweets")

        print(f"\n[XGoingScraper] Total scraped: {len(signals)} tweets\n")
        return signals

    async def scrape_single_feed(
        self,
        feed_url: str,
        feed_name: str,
        max_items: int = 10
    ) -> List[RawSignal]:
        """
        抓取单个 XGo.ing RSS feed

        Args:
            feed_url: XGo.ing RSS URL
            feed_name: Twitter 账号名称
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
                # 提取推文内容
                tweet_text = entry.get("summary", entry.get("description", ""))
                tweet_link = entry.get("link", "")
                tweet_title = entry.get("title", tweet_text[:100])

                # 提取发布时间
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # 构建 RawSignal
                signal = RawSignal(
                    source="twitter",
                    source_id=tweet_link.split("/")[-1] if "/" in tweet_link else None,
                    url=tweet_link,
                    title=tweet_title,
                    content=tweet_text,
                    source_created_at=published_at,
                    metadata={
                        "account": feed_name,
                        "type": "tweet",
                    }
                )

                signals.append(signal)

            return signals

        except Exception as e:
            print(f"  ✗ Error scraping {feed_name}: {e}")
            return []


# 测试代码
async def test_xgoing_scraper():
    """测试 XGoingScraper"""
    scraper = XGoingScraper()

    # 只抓取前 3 个账号，每个账号 5 条推文
    import xml.etree.ElementTree as ET
    tree = ET.parse("BestBlog/BestBlogs_RSS_Twitters.opml")
    test_feeds = []
    for i, outline in enumerate(tree.findall('.//outline[@xmlUrl]')[:3]):
        test_feeds.append({
            "name": outline.get('text', ''),
            "url": outline.get('xmlUrl')
        })

    print(f"\n测试抓取 {len(test_feeds)} 个 Twitter 账号...")
    signals = []
    for feed in test_feeds:
        feed_signals = await scraper.scrape_single_feed(feed["url"], feed["name"], max_items=5)
        signals.extend(feed_signals)

    print(f"\n总共抓取: {len(signals)} 条推文")
    if signals:
        print(f"\n示例推文:")
        for i, signal in enumerate(signals[:3]):
            print(f"\n{i+1}. {signal.title[:80]}...")
            print(f"   来源: {signal.metadata.get('account')}")
            print(f"   链接: {signal.url}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_xgoing_scraper())
