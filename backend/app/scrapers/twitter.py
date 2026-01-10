# Input: RSS Bridge API (https://rss-bridge.org/bridge01/)
# Output: RawSignal 列表(Twitter账号的最新推文)
# Position: Twitter数据源爬虫,通过RSS Bridge免费抓取指定账号推文
# 更新提醒:一旦我被更新,务必更新我的开头注释,以及所属的文件夹的md

from datetime import datetime
from typing import List, Optional
import httpx
import xml.etree.ElementTree as ET

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class TwitterScraper(BaseScraper):
    """
    Twitter RSS 爬虫

    数据源:RSS Bridge (免费,无需API key)
    规则预筛:
    1. 只抓取配置的账号列表
    2. 排除转发(retweet)
    3. 只保留包含关键词的推文

    RSS Bridge将Twitter账号转换为RSS feed,完全免费
    """

    # RSS Bridge公共实例
    RSS_BRIDGE_URL = "https://rss-bridge.org/bridge01/"

    def __init__(self):
        super().__init__(source_name="twitter")
        self.accounts = config.twitter.accounts  # 从配置读取账号列表
        self.keywords = [kw.lower() for kw in config.twitter.keywords]
        self.max_items_per_account = config.twitter.max_items_per_account

    def _build_rss_url(self, username: str) -> str:
        """
        构建RSS Bridge URL

        Args:
            username: Twitter用户名(不带@)

        Returns:
            RSS Bridge URL
        """
        # RSS Bridge格式: ?action=display&bridge=Twitter&u={username}&format=Atom
        return f"{self.RSS_BRIDGE_URL}?action=display&bridge=Twitter&u={username}&format=Atom"

    def _matches_keywords(self, text: str) -> bool:
        """
        检查推文是否包含关键词

        Args:
            text: 推文内容

        Returns:
            是否匹配
        """
        if not self.keywords:
            return True  # 如果没有配置关键词,全部通过

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def _is_retweet(self, title: str, content: str) -> bool:
        """
        判断是否为转发

        Args:
            title: 推文标题
            content: 推文内容

        Returns:
            是否为转发
        """
        # RSS Bridge中,转发通常以"RT @"开头
        return title.startswith("RT @") or content.startswith("RT @")

    def _parse_rss_feed(self, xml_content: str) -> List[dict]:
        """
        解析RSS Feed XML

        Args:
            xml_content: RSS XML内容

        Returns:
            推文列表
        """
        tweets = []

        try:
            root = ET.fromstring(xml_content)

            # Atom feed格式
            # 命名空间
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            # 解析每个entry
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                link_elem = entry.find("atom:link", ns)
                content_elem = entry.find("atom:content", ns)
                published_elem = entry.find("atom:published", ns)
                author_elem = entry.find("atom:author/atom:name", ns)

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text or ""
                url = link_elem.get("href", "")
                content = content_elem.text if content_elem is not None else ""
                published = published_elem.text if published_elem is not None else None
                author = author_elem.text if author_elem is not None else ""

                tweets.append(
                    {
                        "title": title,
                        "url": url,
                        "content": content,
                        "published": published,
                        "author": author,
                    }
                )

        except Exception as e:
            print(f"[Twitter] Failed to parse RSS feed: {e}")

        return tweets

    def _convert_to_raw_signal(self, tweet: dict, username: str) -> RawSignal:
        """
        转换推文为RawSignal

        Args:
            tweet: 推文数据
            username: Twitter用户名

        Returns:
            RawSignal对象
        """
        # 解析发布时间 (ISO 8601格式)
        created_at = None
        if tweet.get("published"):
            try:
                # RSS Bridge Atom格式: "2025-12-31T10:00:00+00:00"
                created_at = datetime.fromisoformat(
                    tweet["published"].replace("Z", "+00:00")
                )
            except Exception as e:
                print(f"[Twitter] Failed to parse timestamp: {e}")

        # 提取tweet ID (从URL中提取)
        # URL格式: https://twitter.com/{username}/status/{tweet_id}
        tweet_id = tweet["url"].split("/")[-1] if "/" in tweet["url"] else ""

        return RawSignal(
            source=self.source_name,
            source_id=f"twitter_{username}_{tweet_id}",
            url=tweet["url"],
            title=tweet["title"][:200],  # 限制长度
            content=tweet["content"],
            source_created_at=created_at,
            metadata={
                "author": tweet.get("author", username),
                "username": username,
                "tweet_id": tweet_id,
                "is_verified": False,  # RSS Bridge不提供此信息
            },
        )

    async def _scrape_account(
        self, client: httpx.AsyncClient, username: str
    ) -> List[RawSignal]:
        """
        抓取单个账号的推文

        Args:
            client: httpx客户端
            username: Twitter用户名

        Returns:
            RawSignal列表
        """
        signals = []

        try:
            url = self._build_rss_url(username)
            print(f"[Twitter] Fetching @{username}...")

            # 获取RSS feed
            resp = await client.get(url, timeout=30.0)
            resp.raise_for_status()
            xml_content = resp.text

            # 解析RSS
            tweets = self._parse_rss_feed(xml_content)
            print(f"[Twitter] Found {len(tweets)} tweets from @{username}")

            # 规则预筛
            filtered_count = 0
            for tweet in tweets[: self.max_items_per_account]:
                # 排除转发
                if self._is_retweet(tweet.get("title", ""), tweet.get("content", "")):
                    continue

                # 关键词过滤
                full_text = f"{tweet.get('title', '')} {tweet.get('content', '')}"
                if not self._matches_keywords(full_text):
                    continue

                signal = self._convert_to_raw_signal(tweet, username)
                signals.append(signal)
                filtered_count += 1

            print(
                f"[Twitter] @{username}: {filtered_count}/{len(tweets)} passed filter"
            )

        except Exception as e:
            print(f"[Twitter] Failed to scrape @{username}: {e}")

        return signals

    async def scrape(self) -> List[RawSignal]:
        """
        抓取所有配置账号的推文

        流程:
        1. 遍历配置的账号列表
        2. 通过RSS Bridge获取每个账号的RSS feed
        3. 规则预筛(排除转发 + 关键词过滤)
        4. 转换为RawSignal

        Returns:
            RawSignal列表(已通过规则预筛)
        """
        all_signals = []

        async with httpx.AsyncClient() as client:
            for username in self.accounts:
                account_signals = await self._scrape_account(client, username)
                all_signals.extend(account_signals)

                # 避免被RSS Bridge限流
                import asyncio

                await asyncio.sleep(2)

        print(
            f"[Twitter] Total: {len(all_signals)} signals from {len(self.accounts)} accounts"
        )
        return all_signals
