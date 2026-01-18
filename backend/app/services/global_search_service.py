"""
[INPUT]: 依赖 embeddings/bailian_embedding, models/research, database
[OUTPUT]: 对外提供全局搜索服务 (向量 + BM25 + RRF)
[POS]: services/ 的全局搜索服务，被 api/search.py 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.embeddings.bailian_embedding import embedding_service

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class SearchScope(str, Enum):
    """搜索范围"""
    ALL = "all"              # 全局搜索
    PROJECTS = "projects"    # 仅项目
    SOURCES = "sources"      # 仅源材料
    OUTPUTS = "outputs"      # 仅研究输出
    RESOURCES = "resources"  # 仅资源库


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    type: str  # project, source, output, resource
    title: str
    content_preview: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    total: int
    results: List[SearchResult]
    scope: str


# ============================================================
# 全局搜索服务
# ============================================================

class GlobalSearchService:
    """
    全局搜索服务

    功能:
    - 向量搜索 (语义相似度)
    - BM25 搜索 (关键词匹配)
    - RRF 融合排序 (Reciprocal Rank Fusion)
    - 跨项目/源材料/输出搜索

    使用示例:
    ```python
    service = GlobalSearchService()

    results = await service.search(
        query="AI Agent 开发",
        scope=SearchScope.ALL,
        limit=20,
    )

    for result in results.results:
        print(f"{result.type}: {result.title} ({result.score:.3f})")
    ```
    """

    # RRF 融合参数
    RRF_K = 60  # 融合常数

    def __init__(self):
        """初始化服务"""
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        scope: SearchScope = SearchScope.ALL,
        project_id: Optional[str] = None,
        limit: int = 20,
        use_hybrid: bool = True,
    ) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询
            scope: 搜索范围
            project_id: 限定项目 ID (可选)
            limit: 返回数量
            use_hybrid: 是否使用混合搜索

        Returns:
            搜索响应
        """
        results = []

        # 获取数据库会话
        db = next(get_db())

        try:
            if use_hybrid:
                # 混合搜索: 向量 + BM25 + RRF
                vector_results = await self._vector_search(
                    db, query, scope, project_id, limit * 2
                )
                keyword_results = await self._keyword_search(
                    db, query, scope, project_id, limit * 2
                )
                results = self._rrf_fusion(vector_results, keyword_results, limit)
            else:
                # 仅向量搜索
                results = await self._vector_search(
                    db, query, scope, project_id, limit
                )

        finally:
            db.close()

        return SearchResponse(
            query=query,
            total=len(results),
            results=results,
            scope=scope.value,
        )

    async def _vector_search(
        self,
        db: Session,
        query: str,
        scope: SearchScope,
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """向量搜索"""
        results = []

        # 生成查询向量
        try:
            query_embedding = await self.embedding_service.embed_text(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return results

        # 构建查询
        if scope in [SearchScope.ALL, SearchScope.SOURCES]:
            # 搜索源材料
            source_results = self._search_sources_by_vector(
                db, query_embedding, project_id, limit
            )
            results.extend(source_results)

        if scope in [SearchScope.ALL, SearchScope.OUTPUTS]:
            # 搜索研究输出
            output_results = self._search_outputs_by_vector(
                db, query_embedding, project_id, limit
            )
            results.extend(output_results)

        if scope in [SearchScope.ALL, SearchScope.RESOURCES]:
            # 搜索资源库
            resource_results = self._search_resources_by_vector(
                db, query_embedding, limit
            )
            results.extend(resource_results)

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def _search_sources_by_vector(
        self,
        db: Session,
        query_embedding: List[float],
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """向量搜索源材料"""
        results = []

        sql = """
        SELECT
            s.id::text,
            s.title,
            s.content,
            s.source_type,
            s.project_id::text,
            1 - (c.embedding <=> :embedding) as similarity
        FROM research_source_chunks c
        JOIN research_sources s ON c.source_id = s.id
        WHERE 1=1
        """

        params = {"embedding": str(query_embedding), "limit": limit}

        if project_id:
            sql += " AND s.project_id = :project_id"
            params["project_id"] = project_id

        sql += " ORDER BY similarity DESC LIMIT :limit"

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="source",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[5]) if row[5] else 0.0,
                    metadata={
                        "source_type": row[3],
                        "project_id": row[4],
                    },
                ))
        except Exception as e:
            logger.error(f"Vector search sources failed: {e}")

        return results

    def _search_outputs_by_vector(
        self,
        db: Session,
        query_embedding: List[float],
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """向量搜索研究输出"""
        results = []

        sql = """
        SELECT
            o.id::text,
            o.title,
            o.content,
            o.output_type,
            o.project_id::text,
            1 - (o.embedding <=> :embedding) as similarity
        FROM research_outputs o
        WHERE o.embedding IS NOT NULL
        """

        params = {"embedding": str(query_embedding), "limit": limit}

        if project_id:
            sql += " AND o.project_id = :project_id"
            params["project_id"] = project_id

        sql += " ORDER BY similarity DESC LIMIT :limit"

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="output",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[5]) if row[5] else 0.0,
                    metadata={
                        "output_type": row[3],
                        "project_id": row[4],
                    },
                ))
        except Exception as e:
            logger.error(f"Vector search outputs failed: {e}")

        return results

    def _search_resources_by_vector(
        self,
        db: Session,
        query_embedding: List[float],
        limit: int,
    ) -> List[SearchResult]:
        """向量搜索资源库"""
        results = []

        # 注: 假设 resources 表有 embedding 列
        # 如果没有，此搜索会返回空结果
        sql = """
        SELECT
            r.id::text,
            r.title,
            r.summary,
            r.resource_type,
            1 - (r.embedding <=> :embedding) as similarity
        FROM resources r
        WHERE r.embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT :limit
        """

        params = {"embedding": str(query_embedding), "limit": limit}

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="resource",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[4]) if row[4] else 0.0,
                    metadata={"resource_type": row[3]},
                ))
        except Exception as e:
            logger.debug(f"Vector search resources: {e}")

        return results

    async def _keyword_search(
        self,
        db: Session,
        query: str,
        scope: SearchScope,
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """关键词搜索 (BM25 风格)"""
        results = []

        # 简化的关键词搜索 (使用 ILIKE)
        # 生产环境建议使用 PostgreSQL Full-Text Search 或 Elasticsearch

        if scope in [SearchScope.ALL, SearchScope.SOURCES]:
            source_results = self._search_sources_by_keyword(
                db, query, project_id, limit
            )
            results.extend(source_results)

        if scope in [SearchScope.ALL, SearchScope.OUTPUTS]:
            output_results = self._search_outputs_by_keyword(
                db, query, project_id, limit
            )
            results.extend(output_results)

        if scope in [SearchScope.ALL, SearchScope.RESOURCES]:
            resource_results = self._search_resources_by_keyword(
                db, query, limit
            )
            results.extend(resource_results)

        return results[:limit]

    def _search_sources_by_keyword(
        self,
        db: Session,
        query: str,
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """关键词搜索源材料"""
        results = []

        sql = """
        SELECT
            id::text,
            title,
            content,
            source_type,
            project_id::text,
            CASE
                WHEN title ILIKE :pattern THEN 0.8
                WHEN content ILIKE :pattern THEN 0.5
                ELSE 0.3
            END as score
        FROM research_sources
        WHERE title ILIKE :pattern OR content ILIKE :pattern
        """

        params = {"pattern": f"%{query}%", "limit": limit}

        if project_id:
            sql += " AND project_id = :project_id"
            params["project_id"] = project_id

        sql += " ORDER BY score DESC LIMIT :limit"

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="source",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[5]),
                    metadata={
                        "source_type": row[3],
                        "project_id": row[4],
                    },
                ))
        except Exception as e:
            logger.error(f"Keyword search sources failed: {e}")

        return results

    def _search_outputs_by_keyword(
        self,
        db: Session,
        query: str,
        project_id: Optional[str],
        limit: int,
    ) -> List[SearchResult]:
        """关键词搜索研究输出"""
        results = []

        sql = """
        SELECT
            id::text,
            title,
            content,
            output_type,
            project_id::text,
            CASE
                WHEN title ILIKE :pattern THEN 0.8
                WHEN content ILIKE :pattern THEN 0.5
                ELSE 0.3
            END as score
        FROM research_outputs
        WHERE title ILIKE :pattern OR content ILIKE :pattern
        """

        params = {"pattern": f"%{query}%", "limit": limit}

        if project_id:
            sql += " AND project_id = :project_id"
            params["project_id"] = project_id

        sql += " ORDER BY score DESC LIMIT :limit"

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="output",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[5]),
                    metadata={
                        "output_type": row[3],
                        "project_id": row[4],
                    },
                ))
        except Exception as e:
            logger.error(f"Keyword search outputs failed: {e}")

        return results

    def _search_resources_by_keyword(
        self,
        db: Session,
        query: str,
        limit: int,
    ) -> List[SearchResult]:
        """关键词搜索资源库"""
        results = []

        sql = """
        SELECT
            id::text,
            title,
            summary,
            resource_type,
            CASE
                WHEN title ILIKE :pattern THEN 0.8
                WHEN summary ILIKE :pattern THEN 0.5
                ELSE 0.3
            END as score
        FROM resources
        WHERE title ILIKE :pattern OR summary ILIKE :pattern
        ORDER BY score DESC
        LIMIT :limit
        """

        params = {"pattern": f"%{query}%", "limit": limit}

        try:
            rows = db.execute(text(sql), params).fetchall()
            for row in rows:
                results.append(SearchResult(
                    id=row[0],
                    type="resource",
                    title=row[1] or "无标题",
                    content_preview=(row[2] or "")[:200],
                    score=float(row[4]),
                    metadata={"resource_type": row[3]},
                ))
        except Exception as e:
            logger.debug(f"Keyword search resources: {e}")

        return results

    def _rrf_fusion(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        limit: int,
    ) -> List[SearchResult]:
        """
        RRF (Reciprocal Rank Fusion) 融合

        将向量搜索和关键词搜索结果融合，
        使用 RRF 算法计算综合分数。
        """
        # 构建结果映射
        result_map: Dict[str, SearchResult] = {}
        rrf_scores: Dict[str, float] = {}

        # 处理向量搜索结果
        for rank, result in enumerate(vector_results, 1):
            key = f"{result.type}:{result.id}"
            result_map[key] = result
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (self.RRF_K + rank)

        # 处理关键词搜索结果
        for rank, result in enumerate(keyword_results, 1):
            key = f"{result.type}:{result.id}"
            if key not in result_map:
                result_map[key] = result
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (self.RRF_K + rank)

        # 按 RRF 分数排序
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        # 返回融合结果
        fused_results = []
        for key in sorted_keys[:limit]:
            result = result_map[key]
            result.score = rrf_scores[key]
            fused_results.append(result)

        return fused_results


# ============================================================
# 单例
# ============================================================

global_search_service = GlobalSearchService()
