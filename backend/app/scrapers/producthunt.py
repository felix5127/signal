# Input: Product Hunt API (https://api.producthunt.com/v2/api/graphql)
# Output: RawSignal 列表(最新产品发布)
# Position: Product Hunt数据源爬虫,实现规则预筛(点赞数+分类)
# 更新提醒:一旦我被更新,务必更新我的开头注释,以及所属的文件夹的md

from datetime import datetime, timedelta
from typing import List, Optional
import httpx

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class ProductHuntScraper(BaseScraper):
    """
    Product Hunt 爬虫

    数据源:Product Hunt GraphQL API (需要API key)
    规则预筛:
    1. 点赞数阈值(upvotes > threshold)
    2. 分类过滤(AI, Developer Tools等)
    3. 时间过滤(最近N天)

    需要在 .env 中配置 PRODUCTHUNT_API_KEY
    申请地址: https://www.producthunt.com/v2/oauth/applications
    """

    API_URL = "https://api.producthunt.com/v2/api/graphql"

    def __init__(self):
        super().__init__(source_name="producthunt")
        self.api_key = config.producthunt_api_key
        self.min_upvotes = config.producthunt.min_upvotes
        self.categories = config.producthunt.categories
        self.days_back = config.producthunt.days_back
        self.max_results = config.producthunt.max_results

    def _get_headers(self) -> dict:
        """
        获取Product Hunt API Headers

        Returns:
            Headers字典
        """
        if not self.api_key:
            raise ValueError("PRODUCTHUNT_API_KEY not configured in .env")

        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_graphql_query(self, cursor: Optional[str] = None) -> dict:
        """
        构建GraphQL查询

        Args:
            cursor: 分页游标

        Returns:
            GraphQL查询字典
        """
        # GraphQL查询获取今日热门产品
        query = """
        query($cursor: String) {
          posts(first: 20, after: $cursor, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                votesCount
                commentsCount
                url
                website
                createdAt
                featuredAt
                productLinks {
                  type
                  url
                }
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
                thumbnail {
                  url
                }
                user {
                  name
                  username
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
        """

        variables = {}
        if cursor:
            variables["cursor"] = cursor

        return {"query": query, "variables": variables}

    def _is_recent(self, created_at: datetime) -> bool:
        """
        检查产品是否在最近N天内发布

        Args:
            created_at: 发布日期

        Returns:
            是否为最近产品
        """
        from datetime import timezone
        # 使用UTC时间进行比较，确保时区一致
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        # 如果 created_at 没有时区信息，假设为 UTC
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return created_at >= cutoff_date

    def _matches_categories(self, topics: List[str]) -> bool:
        """
        检查产品分类是否匹配

        Args:
            topics: 产品标签列表

        Returns:
            是否匹配
        """
        if not self.categories:
            return True

        # 不区分大小写匹配
        topics_lower = [t.lower() for t in topics]
        categories_lower = [c.lower() for c in self.categories]

        return any(cat in topics_lower for cat in categories_lower)

    def _convert_to_raw_signal(self, product: dict) -> RawSignal:
        """
        转换产品为RawSignal

        Args:
            product: 产品数据

        Returns:
            RawSignal对象
        """
        # 解析发布时间
        created_at = None
        if product.get("createdAt"):
            try:
                # ISO 8601格式
                created_at = datetime.fromisoformat(
                    product["createdAt"].replace("Z", "+00:00")
                )
            except Exception as e:
                print(f"[ProductHunt] Failed to parse timestamp: {e}")

        # 提取话题标签
        topics = []
        if product.get("topics", {}).get("edges"):
            topics = [
                edge["node"]["name"] for edge in product["topics"]["edges"] if edge.get("node")
            ]

        # 提取产品链接
        product_links = []
        if product.get("productLinks"):
            product_links = [
                {"type": link["type"], "url": link["url"]}
                for link in product["productLinks"]
            ]

        return RawSignal(
            source=self.source_name,
            source_id=f"ph_{product['id']}",
            url=product["url"],
            title=f"{product['name']}: {product.get('tagline', '')}",
            content=product.get("description", ""),
            source_created_at=created_at,
            metadata={
                "product_id": product["id"],
                "upvotes": product.get("votesCount", 0),
                "comments": product.get("commentsCount", 0),
                "website": product.get("website", ""),
                "featured_at": product.get("featuredAt", ""),
                "topics": topics,
                "product_links": product_links,
                "thumbnail": product.get("thumbnail", {}).get("url", ""),
                "maker": product.get("user", {}).get("name", ""),
                "maker_username": product.get("user", {}).get("username", ""),
            },
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取Product Hunt最新产品

        流程:
        1. 调用GraphQL API获取产品列表（获取更多数据）
        2. 规则预筛(点赞数+分类+时间)
        3. 按upvotes排序，取前max_results条
        4. 转换为RawSignal

        Returns:
            RawSignal列表(已通过规则预筛，按upvotes排序)
        """
        candidates = []  # 存储 (upvotes, signal) 元组用于排序

        if not self.api_key:
            print("[ProductHunt] API key not configured, skipping")
            return []

        async with httpx.AsyncClient() as client:
            try:
                cursor = None
                total_fetched = 0

                # 获取更多数据，确保过滤后有足够的高质量产品
                fetch_limit = self.max_results * 3

                # 分页获取产品
                while total_fetched < fetch_limit:
                    # 构建查询
                    payload = self._build_graphql_query(cursor)

                    # 调用API
                    resp = await client.post(
                        self.API_URL,
                        headers=self._get_headers(),
                        json=payload,
                        timeout=30.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    # 解析响应
                    if "errors" in data:
                        print(f"[ProductHunt] API error: {data['errors']}")
                        break

                    posts = data.get("data", {}).get("posts", {}).get("edges", [])
                    page_info = data.get("data", {}).get("posts", {}).get("pageInfo", {})

                    print(f"[ProductHunt] Fetched {len(posts)} products")

                    # 规则预筛
                    for edge in posts:
                        product = edge.get("node")
                        if not product:
                            continue

                        total_fetched += 1

                        # 点赞数过滤
                        upvotes = product.get("votesCount", 0)
                        if upvotes < self.min_upvotes:
                            continue

                        # 时间过滤
                        if product.get("createdAt"):
                            try:
                                created_at = datetime.fromisoformat(
                                    product["createdAt"].replace("Z", "+00:00")
                                )
                                if not self._is_recent(created_at):
                                    continue
                            except Exception:
                                continue

                        # 分类过滤
                        topics = []
                        if product.get("topics", {}).get("edges"):
                            topics = [
                                edge["node"]["name"]
                                for edge in product["topics"]["edges"]
                                if edge.get("node")
                            ]

                        if not self._matches_categories(topics):
                            continue

                        signal = self._convert_to_raw_signal(product)
                        candidates.append((upvotes, signal))

                    # 检查是否还有下一页
                    if not page_info.get("hasNextPage"):
                        break

                    cursor = page_info.get("endCursor")

                # 按 upvotes 降序排序，取前 max_results 条
                candidates.sort(key=lambda x: x[0], reverse=True)
                signals = [signal for _, signal in candidates[:self.max_results]]

                print(
                    f"[ProductHunt] {len(candidates)}/{total_fetched} products passed filter, "
                    f"returning top {len(signals)} by upvotes "
                    f"(upvotes range: {candidates[0][0] if candidates else 0} - "
                    f"{candidates[-1][0] if candidates else 0})"
                    if total_fetched > 0
                    else "[ProductHunt] No products fetched"
                )

            except Exception as e:
                print(f"[ProductHunt] Scraping failed: {e}")
                import traceback

                traceback.print_exc()

        return signals
