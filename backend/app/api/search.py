"""
[INPUT]: 依赖 services/global_search_service
[OUTPUT]: 对外提供全局搜索 API 端点
[POS]: api/ 的搜索路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.global_search_service import (
    global_search_service,
    SearchScope,
    SearchResult as SearchResultModel,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["全局搜索"])


# ============================================================
# Pydantic 模型
# ============================================================

class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: str
    type: str
    title: str
    content_preview: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool
    query: str
    total: int
    scope: str
    results: List[SearchResultItem]


# ============================================================
# API 端点
# ============================================================

@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1, max_length=200, description="搜索查询"),
    scope: str = Query("all", description="搜索范围: all, projects, sources, outputs, resources"),
    project_id: Optional[str] = Query(None, description="限定项目 ID"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    hybrid: bool = Query(True, description="是否使用混合搜索"),
):
    """
    全局搜索

    支持跨项目、源材料、研究输出的混合搜索。
    使用向量搜索 (语义) + 关键词搜索 (BM25) + RRF 融合排序。
    """
    try:
        # 解析搜索范围
        try:
            search_scope = SearchScope(scope)
        except ValueError:
            search_scope = SearchScope.ALL

        response = await global_search_service.search(
            query=q,
            scope=search_scope,
            project_id=project_id,
            limit=limit,
            use_hybrid=hybrid,
        )

        return SearchResponse(
            success=True,
            query=response.query,
            total=response.total,
            scope=response.scope,
            results=[
                SearchResultItem(
                    id=r.id,
                    type=r.type,
                    title=r.title,
                    content_preview=r.content_preview,
                    score=r.score,
                    metadata=r.metadata,
                )
                for r in response.results
            ],
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return SearchResponse(
            success=False,
            query=q,
            total=0,
            scope=scope,
            results=[],
        )


@router.get("/suggest")
async def search_suggest(
    q: str = Query(..., min_length=1, max_length=100, description="搜索前缀"),
    limit: int = Query(5, ge=1, le=20, description="建议数量"),
):
    """
    搜索建议

    返回匹配的标题建议 (用于自动补全)。
    """
    try:
        response = await global_search_service.search(
            query=q,
            scope=SearchScope.ALL,
            limit=limit,
            use_hybrid=False,  # 仅向量搜索，更快
        )

        suggestions = [
            {"title": r.title, "type": r.type, "id": r.id}
            for r in response.results
        ]

        return {"success": True, "suggestions": suggestions}

    except Exception as e:
        logger.error(f"Suggest failed: {e}")
        return {"success": False, "suggestions": []}


@router.get("/scopes")
async def list_search_scopes():
    """获取支持的搜索范围"""
    return {
        "scopes": [
            {"id": "all", "name": "全部", "description": "搜索所有内容"},
            {"id": "projects", "name": "项目", "description": "搜索研究项目"},
            {"id": "sources", "name": "源材料", "description": "搜索源材料"},
            {"id": "outputs", "name": "研究输出", "description": "搜索研究报告"},
            {"id": "resources", "name": "资源库", "description": "搜索资源库"},
        ],
        "default": "all",
    }
