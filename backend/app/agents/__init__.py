"""
[INPUT]: 各子模块的 Agent 组件
[OUTPUT]: 统一导出 Agent 相关类和函数
[POS]: agents 包入口，聚合所有 Agent 组件供外部导入
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.llm.kimi_client import KimiClient, kimi_client
from app.agents.tools.tavily_search import TavilySearchTool
from app.agents.embeddings.bailian_embedding import BailianEmbeddingService, embedding_service
from app.agents.multimodal.tingwu_client import TingwuClient, tingwu_client
from app.agents.podcast.synthesizer import PodcastSynthesizer, podcast_synthesizer
from app.agents.podcast.cosyvoice_client import CosyVoiceClient, cosyvoice_client
from app.agents.mindmap.agent import MindmapAgent, mindmap_agent

__all__ = [
    # LLM 客户端
    "KimiClient",
    "kimi_client",
    # 工具
    "TavilySearchTool",
    # 嵌入服务
    "BailianEmbeddingService",
    "embedding_service",
    # 多模态处理
    "TingwuClient",
    "tingwu_client",
    # 播客生成
    "PodcastSynthesizer",
    "podcast_synthesizer",
    "CosyVoiceClient",
    "cosyvoice_client",
    # 概念图
    "MindmapAgent",
    "mindmap_agent",
]
