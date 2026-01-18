"""
[INPUT]: 依赖 FastAPI, database.py (get_db), services/source_manage_service.py, services/stats_service.py
[OUTPUT]: 对外提供数据源管理 API 端点
[POS]: API 路由层，Admin 数据源管理
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.source_manage_service import SourceManageService
from app.services.stats_service import StatsService
from app.models.resource import Resource


router = APIRouter()


# ========== 请求/响应模型 ==========

class SourceCreateRequest(BaseModel):
    """创建数据源请求"""
    name: str
    type: str  # blog/twitter/podcast/video
    url: str
    is_whitelist: bool = False


class SourceUpdateRequest(BaseModel):
    """更新数据源请求"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    is_whitelist: Optional[bool] = None


class SourceStatsResponse(BaseModel):
    """数据源统计"""
    total_collected: int
    total_approved: int
    total_rejected: int
    approval_rate: float
    avg_llm_score: float


class SourceResponse(BaseModel):
    """数据源响应"""
    id: int
    name: str
    type: str
    url: str
    enabled: bool
    is_whitelist: bool
    stats: SourceStatsResponse
    last_collected_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class SourceDetailResponse(BaseModel):
    """数据源详情响应"""
    source: SourceResponse
    score_distribution: dict
    recent_items: List[dict]


# ========== API 端点 ==========

@router.get("", response_model=List[SourceResponse])
async def get_sources(
    type: Optional[str] = Query(None, description="类型筛选: blog/twitter/podcast/video"),
    enabled: Optional[bool] = Query(None, description="启用状态"),
    is_whitelist: Optional[bool] = Query(None, description="白名单状态"),
    db: Session = Depends(get_db),
):
    """
    获取数据源列表

    - 支持按类型、启用状态、白名单筛选
    """
    service = SourceManageService(db)
    stats_service = StatsService(db)

    sources = service.get_all_sources(
        source_type=type,
        enabled=enabled,
        is_whitelist=is_whitelist,
    )

    # 获取统计数据
    source_stats = stats_service.get_source_stats()
    stats_map = {s["id"]: s for s in source_stats}

    result = []
    for source in sources:
        stats = stats_map.get(source.id, {}).get("stats", {})
        result.append({
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "url": source.url,
            "enabled": source.enabled,
            "is_whitelist": source.is_whitelist,
            "stats": {
                "total_collected": stats.get("total_collected", 0),
                "total_approved": stats.get("total_approved", 0),
                "total_rejected": stats.get("total_rejected", 0),
                "approval_rate": stats.get("approval_rate", 0),
                "avg_llm_score": stats.get("avg_llm_score", 0),
            },
            "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "created_at": source.created_at.isoformat() if source.created_at else None,
        })

    return result


@router.post("", response_model=SourceResponse)
async def create_source(
    request: SourceCreateRequest,
    db: Session = Depends(get_db),
):
    """
    添加数据源

    - type 必须是 blog/twitter/podcast/video
    - url 必须唯一
    """
    if request.type not in ["blog", "twitter", "podcast", "video"]:
        raise HTTPException(status_code=400, detail="Invalid type, use blog/twitter/podcast/video")

    service = SourceManageService(db)

    # 检查 URL 是否已存在
    existing = service.get_source_by_url(request.url)
    if existing:
        raise HTTPException(status_code=400, detail="URL already exists")

    source = service.create_source(
        name=request.name,
        source_type=request.type,
        url=request.url,
        is_whitelist=request.is_whitelist,
    )

    return {
        "id": source.id,
        "name": source.name,
        "type": source.type,
        "url": source.url,
        "enabled": source.enabled,
        "is_whitelist": source.is_whitelist,
        "stats": {
            "total_collected": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "approval_rate": 0,
            "avg_llm_score": 0,
        },
        "last_collected_at": None,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    request: SourceUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    更新数据源

    - 可更新 name、enabled、is_whitelist
    """
    service = SourceManageService(db)

    source = service.update_source(
        source_id=source_id,
        name=request.name,
        enabled=request.enabled,
        is_whitelist=request.is_whitelist,
    )

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # 获取统计
    stats_service = StatsService(db)
    source_stats = stats_service.get_source_stats(source_id=source_id)
    stats = source_stats[0]["stats"] if source_stats else {}

    return {
        "id": source.id,
        "name": source.name,
        "type": source.type,
        "url": source.url,
        "enabled": source.enabled,
        "is_whitelist": source.is_whitelist,
        "stats": {
            "total_collected": stats.get("total_collected", 0),
            "total_approved": stats.get("total_approved", 0),
            "total_rejected": stats.get("total_rejected", 0),
            "approval_rate": stats.get("approval_rate", 0),
            "avg_llm_score": stats.get("avg_llm_score", 0),
        },
        "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }


@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    删除数据源
    """
    service = SourceManageService(db)

    success = service.delete_source(source_id)

    if not success:
        raise HTTPException(status_code=404, detail="Source not found")

    return {"success": True, "source_id": source_id}


@router.get("/{source_id}/stats", response_model=SourceDetailResponse)
async def get_source_detail_stats(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    获取数据源详情统计

    - 基本信息
    - 评分分布
    - 最近采集的内容
    """
    service = SourceManageService(db)
    stats_service = StatsService(db)

    source = service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # 获取统计
    source_stats = stats_service.get_source_stats(source_id=source_id)
    stats = source_stats[0]["stats"] if source_stats else {}

    # 获取评分分布
    score_distribution = stats_service.get_score_distribution(source_id=source_id)

    # 获取最近 10 条内容
    recent_resources = (
        db.query(Resource)
        .filter(Resource.source_name == source.name)
        .order_by(Resource.created_at.desc())
        .limit(10)
        .all()
    )

    recent_items = [
        {
            "id": r.id,
            "title": r.title,
            "url": r.url,
            "score": r.score,
            "llm_score": r.llm_score,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "published_at": r.published_at.isoformat() if r.published_at else None,
        }
        for r in recent_resources
    ]

    return {
        "source": {
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "url": source.url,
            "enabled": source.enabled,
            "is_whitelist": source.is_whitelist,
            "stats": {
                "total_collected": stats.get("total_collected", 0),
                "total_approved": stats.get("total_approved", 0),
                "total_rejected": stats.get("total_rejected", 0),
                "approval_rate": stats.get("approval_rate", 0),
                "avg_llm_score": stats.get("avg_llm_score", 0),
            },
            "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "created_at": source.created_at.isoformat() if source.created_at else None,
        },
        "score_distribution": score_distribution,
        "recent_items": recent_items,
    }
