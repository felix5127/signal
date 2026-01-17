"""
[INPUT]: 依赖 FastAPI, database.py (get_db), services/stats_service.py
[OUTPUT]: 对外提供统计 API 端点
[POS]: API 路由层，Admin 统计数据
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stats_service import StatsService


router = APIRouter()


# ========== 响应模型 ==========

class StatusStats(BaseModel):
    """状态统计"""
    pending: int
    approved: int
    rejected: int
    published: int


class TodayStats(BaseModel):
    """今日统计"""
    total: int
    published: int


class SourcesStats(BaseModel):
    """数据源统计"""
    total: int
    whitelist: int


class OverviewStatsResponse(BaseModel):
    """整体统计概览响应"""
    total: int
    by_status: StatusStats
    today: TodayStats
    avg_llm_score: float
    sources: SourcesStats


class DailyStatsItem(BaseModel):
    """每日统计项"""
    date: Optional[str]
    total: int
    published: int
    rejected: int
    avg_score: float


class SourceStatsItem(BaseModel):
    """数据源统计项"""
    id: int
    name: str
    type: str
    url: str
    enabled: bool
    is_whitelist: bool
    stats: dict
    last_collected_at: Optional[str]


# ========== API 端点 ==========

@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    db: Session = Depends(get_db),
):
    """
    获取整体统计概览

    - 总数
    - 各状态数量
    - 今日统计
    - 平均 LLM 评分
    - 数据源统计
    """
    service = StatsService(db)
    return service.get_overview_stats()


@router.get("/daily", response_model=List[DailyStatsItem])
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db),
):
    """
    获取每日统计

    - 默认最近 7 天
    - 最多 30 天
    """
    service = StatsService(db)
    return service.get_daily_stats(days=days)


@router.get("/sources", response_model=List[SourceStatsItem])
async def get_sources_stats(
    source_id: Optional[int] = Query(None, description="指定数据源 ID"),
    db: Session = Depends(get_db),
):
    """
    获取数据源统计

    - 按数据源分组
    - 可指定单个数据源
    """
    service = StatsService(db)
    return service.get_source_stats(source_id=source_id)


@router.get("/score-distribution", response_model=Dict[int, int])
async def get_score_distribution(
    source_id: Optional[int] = Query(None, description="指定数据源 ID"),
    db: Session = Depends(get_db),
):
    """
    获取 LLM 评分分布

    - 返回 0-5 分各档数量
    - 可按数据源筛选
    """
    service = StatsService(db)
    return service.get_score_distribution(source_id=source_id)
