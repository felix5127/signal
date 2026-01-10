# Input: config, LLM client, Search provider
# Output: 抽象接口定义
# Position: Deep Research基础抽象类,保证V1/V2接口兼容性

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.resource import Resource


class ResearchResult(BaseModel):
    """研究结果统一数据结构"""

    content: str = Field(..., description="Markdown格式的研究报告")
    sources: List[str] = Field(default_factory=list, description="引用的URL列表")
    tokens_used: int = Field(default=0, description="总Token消耗")
    cost_usd: float = Field(default=0.0, description="成本(美元)")
    research_steps: List[Dict] = Field(
        default_factory=list, description="研究步骤记录,用于调试和分析"
    )
    metadata: Dict = Field(
        default_factory=dict, description="扩展字段,如version, strategy等"
    )
    generated_at: datetime = Field(default_factory=datetime.now)


class BaseResearchEngine(ABC):
    """
    研究引擎抽象基类

    所有研究引擎(V1 Lightweight, V2 Full Agent)都必须实现此接口,
    保证API层可以无缝切换不同实现。
    """

    @abstractmethod
    async def research(
        self, resource: Resource, max_cost: float = 0.05
    ) -> ResearchResult:
        """
        执行深度研究

        Args:
            resource: 要研究的资源对象
            max_cost: 最大成本限制(美元),超过则提前终止

        Returns:
            ResearchResult: 统一的研究结果对象

        Raises:
            ValueError: 如果预估成本超过max_cost
            RuntimeError: 如果研究过程出错
        """
        pass

    @abstractmethod
    async def estimate_cost(self, resource: Resource) -> float:
        """
        估算研究成本

        Args:
            resource: 要研究的资源对象

        Returns:
            float: 预估成本(美元)
        """
        pass


class SearchResult(BaseModel):
    """搜索结果统一数据结构"""

    title: str
    url: str
    snippet: str  # 搜索结果摘要
    content: Optional[str] = None  # 可选的完整内容(V2可能需要)
    score: Optional[float] = None  # 可选的相关性评分


class BaseSearchProvider(ABC):
    """
    搜索提供商抽象基类

    支持不同的搜索实现(Tavily, Jina, Google等),
    保证可切换性。
    """

    @abstractmethod
    async def search(
        self, query: str, max_results: int = 3
    ) -> List[SearchResult]:
        """
        执行搜索

        Args:
            query: 搜索查询
            max_results: 最大返回结果数

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否正常
        """
        pass
