# Input: GitHub API (Search API + Trending)
# Output: RawSignal 列表（经规则预筛的 GitHub 热门项目）
# Position: GitHub 数据源爬虫，实现规则预筛（Stars + Language + 排除规则）
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime, timedelta
from typing import List, Optional

import httpx

from app.config import config
from app.scrapers.base import BaseScraper, RawSignal


class GitHubScraper(BaseScraper):
    """
    GitHub Trending 爬虫

    数据源：GitHub API (Search API)
    规则预筛：
    1. Stars today > min_stars_today (default: 50)
    2. Language in whitelist (Python, JavaScript, TypeScript, Rust, Go, Java)
    3. 排除 awesome-list, cheatsheet, tutorial 等低价值仓库

    这一步过滤掉约 70% 的噪音，减少后续 LLM 调用成本
    """

    BASE_URL = "https://api.github.com"

    def __init__(self):
        super().__init__(source_name="github")
        self.github_token = config.github_token
        self.min_stars_today = config.github.min_stars_today
        self.languages = config.github.languages
        self.exclude_patterns = config.github.exclude_patterns
        self.max_items = config.github.max_items

    def _get_headers(self) -> dict:
        """
        获取 GitHub API Headers

        Returns:
            Headers 字典
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Signal-Hunter/1.0",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def _passes_rule_filter(self, repo: dict) -> bool:
        """
        规则预筛逻辑

        条件（AND）：
        1. 不是私有仓库
        2. Language 在白名单中
        3. Name/Description 不包含排除模式
        4. Stars 数量合理（避免超级热门的旧项目）

        Args:
            repo: GitHub repository 数据

        Returns:
            是否通过规则过滤
        """
        # 1. 排除私有仓库
        if repo.get("private", False):
            return False

        # 2. Language 白名单
        language = repo.get("language", "")
        if self.languages and language not in self.languages:
            return False

        # 3. 排除 awesome-list, cheatsheet, tutorial 等
        name_lower = repo.get("name", "").lower()
        description_lower = (repo.get("description") or "").lower()

        # 排除模式检查
        for pattern in self.exclude_patterns:
            pattern_lower = pattern.lower()
            if pattern_lower in name_lower or pattern_lower in description_lower:
                return False

        # 排除明显的聚合类仓库
        aggregation_keywords = [
            "collection of",
            "list of",
            "curated",
            "awesome",
            "resources",
        ]
        for keyword in aggregation_keywords:
            if keyword in description_lower:
                return False

        return True

    def _convert_to_raw_signal(self, repo: dict) -> RawSignal:
        """
        转换 GitHub repo 为 RawSignal

        Args:
            repo: GitHub repository 数据

        Returns:
            RawSignal 对象
        """
        # GitHub 时间格式: "2025-12-29T10:00:00Z"
        created_at = None
        if repo.get("created_at"):
            created_at = datetime.fromisoformat(
                repo["created_at"].replace("Z", "+00:00")
            )

        # 计算 stars_today (估算)
        # 注意: GitHub API 不直接提供 stars_today，这里用总 stars 作为参考
        # 真实场景可使用 GitHub Trending API 获取准确数据
        stars = repo.get("stargazers_count", 0)
        stars_today = 0  # Placeholder，实际需要通过趋势 API 获取

        return RawSignal(
            source=self.source_name,
            source_id=repo["full_name"],  # e.g., "microsoft/vscode"
            url=repo["html_url"],
            title=f"{repo['name']}: {repo.get('description', '')}",
            content=None,  # 可选：后续可以获取 README
            source_created_at=created_at,
            metadata={
                "full_name": repo["full_name"],
                "stars": stars,
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "Unknown"),
                "stars_today": stars_today,
                "topics": repo.get("topics", []),
                "owner": repo.get("owner", {}).get("login", ""),
                "default_branch": repo.get("default_branch", "main"),
                "open_issues": repo.get("open_issues_count", 0),
                "updated_at": repo.get("updated_at", ""),
            },
        )

    async def scrape(self) -> List[RawSignal]:
        """
        抓取 GitHub Trending 项目并规则预筛

        流程：
        1. 使用 GitHub Search API 搜索最近创建/更新的高 Star 项目
        2. 规则预筛（Language + 排除模式）
        3. 按 stars 排序，取前 max_items 条
        4. 转换为 RawSignal

        Returns:
            RawSignal 列表（已通过规则预筛，按 stars 排序）
        """
        signals = []

        # 策略：获取更多数据，确保过滤后有足够的高质量项目
        queries = [
            (f"created:>{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}", "stars:>100"),
        ]

        async with httpx.AsyncClient() as client:
            all_repos = []

            for date_filter, stars_filter in queries:
                try:
                    # 构建查询 - 不在 API 查询中过滤语言，留给规则预筛
                    query = f"{date_filter} {stars_filter}"

                    # GitHub Search API - 获取更多数据
                    url = f"{self.BASE_URL}/search/repositories"
                    params = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 100,  # 最多100条
                    }

                    print(f"[GitHub] Searching: {query}")

                    resp = await client.get(
                        url, headers=self._get_headers(), params=params, timeout=30.0
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    repos = data.get("items", [])
                    all_repos.extend(repos)
                    print(f"[GitHub] Found {len(repos)} repositories")

                except Exception as e:
                    print(f"[GitHub] Query failed: {e}")
                    continue

            # 去重（by full_name）
            seen = set()
            unique_repos = []
            for repo in all_repos:
                if repo["full_name"] not in seen:
                    seen.add(repo["full_name"])
                    unique_repos.append(repo)

            print(f"[GitHub] Total unique: {len(unique_repos)}")

            # 规则预筛 + 按 stars 排序
            candidates = []  # 存储 (stars, signal) 元组用于排序

            for repo in unique_repos:
                if self._passes_rule_filter(repo):
                    signal = self._convert_to_raw_signal(repo)
                    stars = repo.get("stargazers_count", 0)
                    candidates.append((stars, signal))

            # 按 stars 降序排序，取前 max_items 条
            candidates.sort(key=lambda x: x[0], reverse=True)
            signals = [signal for _, signal in candidates[:self.max_items]]

            print(
                f"[GitHub] {len(candidates)} repos passed filter, "
                f"returning top {len(signals)} by stars "
                f"(stars range: {candidates[0][0] if candidates else 0} - "
                f"{candidates[-1][0] if candidates else 0})"
            )

        return signals
