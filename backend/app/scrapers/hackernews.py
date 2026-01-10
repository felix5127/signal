# Input: HN Firebase API (https://hacker-news.firebaseio.com/v0/)
# Output: RawSignal 列表（经规则预筛的 HN 热门内容）
# Position: HN 数据源爬虫，实现规则预筛（Score + 关键词）
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime
from typing import List, Optional

import httpx

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class HackerNewsScraper(BaseScraper):
    """
    Hacker News 爬虫

    数据源：HN Firebase API
    规则预筛：
    1. Score > threshold (default: 80)
    2. 标题包含关键词（AI, LLM, GPT, ML, model, neural 等）

    这一步过滤掉约 70% 的噪音，减少后续 LLM 调用成本
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        super().__init__(source_name="hn")
        self.score_threshold = config.hackernews.score_threshold
        self.keywords = [kw.lower() for kw in config.hackernews.keywords]
        self.max_items = config.hackernews.max_items

    async def _fetch_item(self, client: httpx.AsyncClient, item_id: int) -> Optional[dict]:
        """
        获取单个 HN Item

        Args:
            client: httpx 客户端
            item_id: HN item ID

        Returns:
            Item 数据字典，失败返回 None
        """
        url = f"{self.BASE_URL}/item/{item_id}.json"

        async def _fetch():
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

        try:
            return await self.fetch_with_retry(_fetch)
        except Exception as e:
            print(f"[HN] Failed to fetch item {item_id}: {e}")
            return None

    def _matches_keywords(self, text: str) -> bool:
        """
        检查文本是否包含关键词

        Args:
            text: 标题或内容

        Returns:
            是否匹配
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    def _passes_rule_filter(self, item: dict) -> bool:
        """
        规则预筛逻辑

        条件（AND）：
        1. 类型为 story
        2. Score >= threshold
        3. 标题包含关键词
        4. 有 URL（排除 Ask HN/Show HN 类纯文本帖）

        Args:
            item: HN item 数据

        Returns:
            是否通过规则过滤
        """
        if item.get("type") != "story":
            return False

        if item.get("score", 0) < self.score_threshold:
            return False

        title = item.get("title", "")
        if not self._matches_keywords(title):
            return False

        # 必须有 URL（排除 Ask HN 类帖子）
        if not item.get("url"):
            return False

        return True

    def _convert_to_raw_signal(self, item: dict) -> RawSignal:
        """
        转换 HN item 为 RawSignal

        Args:
            item: HN item 数据

        Returns:
            RawSignal 对象
        """
        # HN 时间戳是 Unix 时间戳（秒）
        created_at = None
        if item.get("time"):
            created_at = datetime.fromtimestamp(item["time"])

        return RawSignal(
            source=self.source_name,
            source_id=str(item["id"]),
            url=item["url"],
            title=item["title"],
            content=item.get("text"),  # Ask HN 类帖子可能有 text 字段
            source_created_at=created_at,
            metadata={
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),  # 评论数
                "author": item.get("by", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
            },
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取 HN Top Stories 并规则预筛

        流程：
        1. 获取 Top Stories ID 列表（获取更多，确保过滤后有足够数据）
        2. 并发获取详情（获取 max_items * 3 倍数量）
        3. 规则预筛（Score + 关键词）
        4. 按 score 排序，取前 max_items 条
        5. 转换为 RawSignal

        Returns:
            RawSignal 列表（已通过规则预筛，按评分排序）
        """
        signals = []

        async with httpx.AsyncClient() as client:
            # 1. 获取 Top Stories ID 列表
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/topstories.json", timeout=10.0
                )
                resp.raise_for_status()
                top_story_ids = resp.json()
            except Exception as e:
                print(f"[HN] Failed to fetch top stories: {e}")
                return []

            # 2. 获取更多数据，确保过滤后有足够的高质量内容
            fetch_limit = self.max_items * 5  # 获取5倍数量，充分过滤
            story_ids = top_story_ids[:fetch_limit]
            print(f"[HN] Fetching up to {len(story_ids)} stories from Top Stories...")

            # 3. 并发获取详情并筛选
            candidates = []  # 存储 (score, signal) 元组用于排序

            for story_id in story_ids:
                item = await self._fetch_item(client, story_id)
                if not item:
                    continue

                # 4. 规则预筛
                if self._passes_rule_filter(item):
                    signal = self._convert_to_raw_signal(item)
                    score = item.get("score", 0)
                    candidates.append((score, signal))

            # 5. 按 score 降序排序，取前 max_items 条
            candidates.sort(key=lambda x: x[0], reverse=True)
            signals = [signal for _, signal in candidates[:self.max_items]]

            print(
                f"[HN] Found {len(candidates)} items passing filter, "
                f"returning top {len(signals)} by score "
                f"(score range: {candidates[0][0] if candidates else 0} - "
                f"{candidates[-1][0] if candidates else 0})"
            )

        return signals
