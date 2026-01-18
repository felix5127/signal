"""
[INPUT]: 各子模块的 Agent 组件
[OUTPUT]: 统一导出 Agent 相关类和函数
[POS]: agents 包入口，聚合所有 Agent 组件供外部导入
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.llm.kimi_client import KimiClient, kimi_client
from app.agents.tools.tavily_search import TavilySearchTool
from app.agents.tools.vector_search import VectorSearchTool
from app.agents.embeddings.bailian_embedding import BailianEmbeddingService, embedding_service
from app.agents.research.agent import ResearchAgent

__all__ = [
    # LLM 客户端
    "KimiClient",
    "kimi_client",
    # 工具
    "TavilySearchTool",
    "VectorSearchTool",
    # 嵌入服务
    "BailianEmbeddingService",
    "embedding_service",
    # Agent
    "ResearchAgent",
]
