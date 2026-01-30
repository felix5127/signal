"""
[INPUT]: 依赖 FastAPI, database.py (get_db), services/stats_service.py
[OUTPUT]: 对外提供统计 API 端点
[OUTPUT]: 新增 pipeline-status, today-funnel 端点
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


# ========== 数据质量监控 API (新增) ==========

class ContentQualityStats(BaseModel):
    """单类型内容质量统计"""
    total: int
    completeness_rate: float


class DataQualityResponse(BaseModel):
    """数据质量响应"""
    podcast_quality: dict
    video_quality: dict
    article_quality: dict
    overall_completeness: float


class SourceHealthItem(BaseModel):
    """数据源健康状态项"""
    id: int
    name: str
    type: str
    url: str
    collection_success_rate: float
    field_completeness: dict
    health_status: str
    last_collected_at: Optional[str]
    last_error: Optional[str]


class SourceHealthSummary(BaseModel):
    """数据源健康汇总"""
    healthy: int
    degraded: int
    failing: int


class SourceHealthResponse(BaseModel):
    """数据源健康响应"""
    sources: List[SourceHealthItem]
    summary: SourceHealthSummary


class TranscriptionTypeStats(BaseModel):
    """单类型转写统计"""
    with_audio: Optional[int] = None
    total: Optional[int] = None
    transcribed: int
    success_rate: float
    pending: int


class RecentFailure(BaseModel):
    """最近失败记录"""
    resource_id: int
    title: str
    source_name: str
    created_at: Optional[str]


class TranscriptionResponse(BaseModel):
    """转写统计响应"""
    podcast: dict
    video: dict
    recent_failures: List[RecentFailure]


@router.get("/data-quality", response_model=DataQualityResponse)
async def get_data_quality_stats(
    db: Session = Depends(get_db),
):
    """
    获取内容完整率统计

    - 按内容类型统计关键字段的填充率
    - podcast: audio_url, transcript, chapters
    - video: transcript, chapters
    - article: content_markdown, summary
    """
    service = StatsService(db)
    return service.get_data_quality_stats()


@router.get("/source-health", response_model=SourceHealthResponse)
async def get_source_health_stats(
    db: Session = Depends(get_db),
):
    """
    获取 RSS 源健康状态

    - 基于最近 7 天采集成功率评估
    - healthy: 成功率 >= 80%
    - degraded: 成功率 50-80%
    - failing: 成功率 < 50% 或无采集
    """
    service = StatsService(db)
    return service.get_source_health_stats()


@router.get("/transcription", response_model=TranscriptionResponse)
async def get_transcription_stats(
    db: Session = Depends(get_db),
):
    """
    获取转写成功率统计

    - 播客: 有音频 URL 但无转录的记录
    - 视频: 无转录的记录
    - 包含最近失败的记录列表
    """
    service = StatsService(db)
    return service.get_transcription_stats()


# ========== Pipeline 状态 API (新增) ==========

class PipelineInfo(BaseModel):
    """Pipeline 当前状态"""
    is_running: bool
    current_source: Optional[str]
    started_at: Optional[str]


class LastRunInfo(BaseModel):
    """上次运行信息"""
    finished_at: Optional[str]
    status: Optional[str]
    saved_count: int
    source_type: Optional[str]


class NextRunInfo(BaseModel):
    """下次运行信息"""
    scheduled_at: Optional[str]
    countdown_seconds: Optional[int]


class QueueStats(BaseModel):
    """处理队列统计"""
    pending_translation: int
    pending_transcription: int


class PipelineStatusResponse(BaseModel):
    """Pipeline 状态响应"""
    pipeline: PipelineInfo
    last_run: LastRunInfo
    next_run: NextRunInfo
    queue: QueueStats


class TodayFunnelResponse(BaseModel):
    """今日漏斗响应"""
    fetched: int
    rule_filtered: int
    dedup_filtered: int
    llm_filtered: int
    saved: int


@router.get("/pipeline-status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    db: Session = Depends(get_db),
):
    """
    获取 Pipeline 实时运行状态

    返回数据供 Admin Dashboard 展示：
    - pipeline: 当前运行状态 (is_running, current_source, started_at)
    - last_run: 上次运行信息 (finished_at, status, saved_count)
    - next_run: 下次运行信息 (scheduled_at, countdown_seconds)
    - queue: 处理队列统计 (pending_translation, pending_transcription)
    """
    service = StatsService(db)
    return service.get_pipeline_status()


@router.get("/today-funnel", response_model=TodayFunnelResponse)
async def get_today_funnel_stats(
    db: Session = Depends(get_db),
):
    """
    获取今日采集漏斗统计

    汇总今日所有 SourceRun 的漏斗数据：
    - fetched: 总抓取数
    - rule_filtered: 规则过滤后
    - dedup_filtered: 去重后
    - llm_filtered: LLM 过滤后
    - saved: 最终保存
    """
    service = StatsService(db)
    return service.get_today_funnel_stats()
