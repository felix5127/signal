# Input: 搜索查询
# Output: SearchResult列表
# Position: 搜索提供商实现,支持Tavily/Jina切换

import os
import httpx
from typing import List
from .base import BaseSearchProvider, SearchResult

# 简单日志工具
def logger_warning(msg: str):
    """简化日志输出"""
    print(f"[WARNING] {msg}")


class TavilySearchProvider(BaseSearchProvider):
    """
    Tavily搜索实现

    Tavily是专为AI应用设计的搜索API,提供高质量搜索结果。
    定价: $0.005/次搜索

    文档: https://docs.tavily.com/
    """

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")

        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_url = "https://api.tavily.com/search"

    async def search(
        self, query: str, max_results: int = 3
    ) -> List[SearchResult]:
        """
        执行Tavily搜索

        Args:
            query: 搜索查询
            max_results: 最大返回结果数 (1-10)

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        try:
            response = await self.client.post(
                self.api_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": min(max_results, 10),
                    "search_depth": "basic",  # basic | advanced
                    "include_raw_content": False,  # V1不需要完整内容
                    "include_answer": False,  # V1不需要AI答案
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        score=item.get("score"),
                    )
                )

            return results

        except httpx.HTTPError as e:
            print(f"[Tavily] HTTP error: {e}")
            return []
        except Exception as e:
            print(f"[Tavily] Unexpected error: {e}")
            return []

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 执行一次简单搜索测试
            results = await self.search("test", max_results=1)
            return len(results) > 0
        except Exception as e:
            logger_warning(f"Health check failed for {self.__class__.__name__}: {e}")
            return False

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class JinaSearchProvider(BaseSearchProvider):
    """
    Jina Reader实现 - 备用方案

    使用Google搜索 + Jina Reader解析内容
    适用于Tavily不可用或成本敏感的场景
    """

    async def search(
        self, query: str, max_results: int = 3
    ) -> List[SearchResult]:
        """TODO: 实现Google + Jina方案"""
        raise NotImplementedError("Jina search provider coming soon...")

    async def health_check(self) -> bool:
        """TODO: 实现健康检查"""
        return False
