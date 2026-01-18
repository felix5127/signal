"""
[INPUT]: bailian_embedding 模块
[OUTPUT]: 导出 BailianEmbeddingService
[POS]: embeddings 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.embeddings.bailian_embedding import BailianEmbeddingService, embedding_service

__all__ = ["BailianEmbeddingService", "embedding_service"]
