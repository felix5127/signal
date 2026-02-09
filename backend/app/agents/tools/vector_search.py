"""
[INPUT]: 依赖 embeddings/bailian_embedding, database.py, models/research.py
[OUTPUT]: 对外提供 VectorSearchTool 类，支持向量相似度搜索
[POS]: agents/tools/ 的向量搜索工具，被 research/tools.py 和 ResearchSDKService 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.embeddings.bailian_embedding import embedding_service

logger = logging.getLogger(__name__)


# ============================================================
# 搜索结果类型
# ============================================================
@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    source_id: UUID
    chunk_index: int
    chunk_text: str
    similarity: float
    source_title: Optional[str] = None
    source_type: Optional[str] = None


@dataclass
class VectorSearchResponse:
    """搜索响应"""
    query: str
    results: List[VectorSearchResult] = field(default_factory=list)
    total_chunks_searched: int = 0


# ============================================================
# 工具定义
# ============================================================
VECTOR_SEARCH_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "vector_search",
        "description": "在研究项目的材料中搜索相关内容。基于语义相似度，能找到意思相近但措辞不同的内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询。描述你想找的内容。"
                },
                "project_id": {
                    "type": "string",
                    "description": "研究项目 ID。限定搜索范围。"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量，1-20。默认 5。"
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "相似度阈值，0-1。默认 0.7。越高越严格。"
                }
            },
            "required": ["query"]
        }
    }
}


# ============================================================
# 向量搜索工具
# ============================================================
class VectorSearchTool:
    """
    向量相似度搜索工具

    功能:
    - 语义搜索
    - 项目范围限定
    - 相似度阈值
    - RRF 融合排序 (可选)

    使用示例:
    ```python
    tool = VectorSearchTool()

    # 搜索项目内容
    results = await tool.search(
        query="Transformer 注意力机制",
        project_id="uuid",
        limit=10,
    )
    ```
    """

    def __init__(self):
        """初始化工具"""
        self.embedding_service = embedding_service

    @property
    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.embedding_service.is_available

    @property
    def tool_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return VECTOR_SEARCH_TOOL_DEFINITION

    async def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        db: Optional[Session] = None,
    ) -> VectorSearchResponse:
        """
        执行向量搜索

        Args:
            query: 查询文本
            project_id: 项目 ID (可选)
            limit: 结果数量
            similarity_threshold: 相似度阈值
            db: 数据库会话

        Returns:
            VectorSearchResponse
        """
        # 获取数据库会话
        if db is None:
            db = next(get_db())
            should_close = True
        else:
            should_close = False

        try:
            # 1. 生成查询向量
            query_embedding = await self.embedding_service.embed_query(query)

            # 2. 构建 SQL 查询
            # 使用 pgvector 的余弦相似度
            sql = text("""
                SELECT
                    se.source_id,
                    se.chunk_index,
                    se.chunk_text,
                    1 - (se.embedding <=> :query_embedding::vector) AS similarity,
                    rs.title AS source_title,
                    rs.source_type
                FROM source_embeddings se
                JOIN research_sources rs ON se.source_id = rs.id
                WHERE 1 - (se.embedding <=> :query_embedding::vector) >= :threshold
                  AND (:project_id IS NULL OR rs.project_id = :project_id::uuid)
                ORDER BY se.embedding <=> :query_embedding::vector
                LIMIT :limit
            """)

            # 3. 执行查询
            result = db.execute(sql, {
                "query_embedding": str(query_embedding),
                "threshold": similarity_threshold,
                "project_id": project_id,
                "limit": limit,
            })

            # 4. 解析结果
            results = []
            for row in result:
                results.append(VectorSearchResult(
                    source_id=row.source_id,
                    chunk_index=row.chunk_index,
                    chunk_text=row.chunk_text,
                    similarity=float(row.similarity),
                    source_title=row.source_title,
                    source_type=row.source_type,
                ))

            logger.info(f"Vector search: '{query}' -> {len(results)} results")

            return VectorSearchResponse(
                query=query,
                results=results,
                total_chunks_searched=len(results),
            )

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            raise

        finally:
            if should_close:
                db.close()

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具调用

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
                project_id=kwargs.get("project_id"),
                limit=kwargs.get("limit", 5),
                similarity_threshold=kwargs.get("similarity_threshold", 0.7),
            )

            return {
                "query": response.query,
                "results": [
                    {
                        "text": r.chunk_text,
                        "similarity": round(r.similarity, 3),
                        "source_title": r.source_title,
                        "source_type": r.source_type,
                    }
                    for r in response.results
                ],
            }

        except Exception as e:
            return {"error": str(e)}

    def format_results_for_context(self, response: VectorSearchResponse) -> str:
        """
        格式化结果为上下文文本

        Args:
            response: 搜索响应

        Returns:
            格式化文本
        """
        parts = [f"## 相关材料: {response.query}\n"]

        for i, result in enumerate(response.results, 1):
            parts.append(f"### [{i}] {result.source_title or '未命名'} (相似度: {result.similarity:.2f})")
            parts.append(result.chunk_text)
            parts.append("")

        return "\n".join(parts)


# ============================================================
# RRF 融合排序
# ============================================================
def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion 融合多个排序结果

    Args:
        rankings: 多个排序列表，每个元素是 (id, score) 元组
        k: RRF 参数，默认 60

    Returns:
        融合后的排序列表
    """
    scores = {}

    for ranking in rankings:
        for rank, (item_id, _) in enumerate(ranking, 1):
            if item_id not in scores:
                scores[item_id] = 0
            scores[item_id] += 1 / (k + rank)

    # 按分数排序
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_items


# ============================================================
# 全局实例
# ============================================================
vector_search_tool = VectorSearchTool()
