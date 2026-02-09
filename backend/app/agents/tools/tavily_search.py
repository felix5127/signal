"""
[INPUT]: 依赖 tavily-python, config.py
[OUTPUT]: 对外提供 TavilySearchTool 类，支持网络搜索
[POS]: agents/tools/ 的搜索工具，被 research/tools.py 和 ResearchSDKService 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from tavily import TavilyClient

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 搜索结果类型
# ============================================================
@dataclass
class SearchResult:
    """单条搜索结果"""
    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: Optional[str] = None
    raw_content: Optional[str] = None  # 原始内容 (如果请求了)


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: List[SearchResult] = field(default_factory=list)
    answer: Optional[str] = None  # Tavily 生成的答案摘要
    follow_up_questions: List[str] = field(default_factory=list)
    response_time: float = 0.0


# ============================================================
# 工具定义 (OpenAI Tool Calling 格式)
# ============================================================
TAVILY_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "tavily_search",
        "description": "搜索互联网获取最新信息。适用于需要实时数据、新闻、研究资料的场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题。建议使用具体、明确的查询。"
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "搜索深度。basic 快速返回，advanced 更深入但较慢。默认 basic。"
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回结果数量，1-10。默认 5。"
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "是否生成答案摘要。默认 true。"
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "限定搜索域名列表，如 ['arxiv.org', 'github.com']"
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "排除的域名列表"
                }
            },
            "required": ["query"]
        }
    }
}


# ============================================================
# Tavily 搜索工具
# ============================================================
class TavilySearchTool:
    """
    Tavily 网络搜索工具

    功能:
    - 网络搜索
    - 答案生成
    - 域名过滤
    - 深度搜索

    使用示例:
    ```python
    tool = TavilySearchTool()

    # 基础搜索
    results = await tool.search("Transformer 架构最新进展")

    # 高级搜索
    results = await tool.search(
        query="AI Agent 框架对比",
        search_depth="advanced",
        max_results=10,
        include_domains=["github.com", "arxiv.org"]
    )
    ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化工具

        Args:
            api_key: Tavily API Key，默认从环境变量读取
        """
        self.api_key = api_key or config.tavily_api_key or ""
        self._client: Optional[TavilyClient] = None

    def _ensure_client(self) -> TavilyClient:
        """懒加载客户端"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Tavily API key not configured. Set TAVILY_API_KEY environment variable.")
            self._client = TavilyClient(api_key=self.api_key)
        return self._client

    @property
    def is_available(self) -> bool:
        """检查工具是否可用"""
        return bool(self.api_key)

    @property
    def tool_definition(self) -> Dict[str, Any]:
        """获取工具定义 (用于 LLM Tool Calling)"""
        return TAVILY_TOOL_DEFINITION

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询
            search_depth: 搜索深度 (basic/advanced)
            max_results: 最大结果数 (1-10)
            include_answer: 是否生成答案摘要
            include_raw_content: 是否包含原始内容
            include_domains: 限定域名
            exclude_domains: 排除域名

        Returns:
            SearchResponse
        """
        client = self._ensure_client()

        try:
            import time
            start_time = time.time()

            # 构建请求参数
            params = {
                "query": query,
                "search_depth": search_depth,
                "max_results": min(max(1, max_results), 10),
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
            }

            if include_domains:
                params["include_domains"] = include_domains
            if exclude_domains:
                params["exclude_domains"] = exclude_domains

            # 执行搜索 (Tavily SDK 是同步的)
            response = client.search(**params)

            elapsed = time.time() - start_time

            # 解析结果
            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    published_date=item.get("published_date"),
                    raw_content=item.get("raw_content"),
                ))

            search_response = SearchResponse(
                query=query,
                results=results,
                answer=response.get("answer"),
                follow_up_questions=response.get("follow_up_questions", []),
                response_time=elapsed,
            )

            logger.info(f"Tavily search completed: '{query}' -> {len(results)} results in {elapsed:.2f}s")

            return search_response

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            raise

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具调用 (LLM Tool Calling 入口)

        Args:
            **kwargs: 工具参数

        Returns:
            格式化的结果
        """
        query = kwargs.get("query", "")
        if not query:
            return {"error": "Missing required parameter: query"}

        try:
            response = await self.search(
                query=query,
                search_depth=kwargs.get("search_depth", "basic"),
                max_results=kwargs.get("max_results", 5),
                include_answer=kwargs.get("include_answer", True),
                include_domains=kwargs.get("include_domains"),
                exclude_domains=kwargs.get("exclude_domains"),
            )

            # 格式化为 LLM 友好的输出
            output = {
                "query": response.query,
                "answer": response.answer,
                "sources": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "snippet": r.content[:500] if r.content else "",
                    }
                    for r in response.results
                ],
            }

            return output

        except Exception as e:
            return {"error": str(e)}

    def format_results_for_context(self, response: SearchResponse) -> str:
        """
        格式化搜索结果为上下文文本

        Args:
            response: 搜索响应

        Returns:
            格式化的文本
        """
        parts = [f"## 搜索结果: {response.query}\n"]

        if response.answer:
            parts.append(f"### 摘要\n{response.answer}\n")

        parts.append("### 来源\n")
        for i, result in enumerate(response.results, 1):
            parts.append(f"**[{i}] {result.title}**")
            parts.append(f"URL: {result.url}")
            parts.append(f"{result.content}\n")

        return "\n".join(parts)


# ============================================================
# 全局实例
# ============================================================
tavily_tool = TavilySearchTool()
