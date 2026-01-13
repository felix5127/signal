"""
[INPUT]: 依赖 database.get_db, models/resource, services/source_service, middlewares/auth, BackgroundTasks
[OUTPUT]: 对外提供 /sources 热门来源 + 信号源管理 + 手动触发采集 API
[POS]: API 路由层，热门来源统计 + 信号源状态查询/配置管理/采集记录/手动触发
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.middlewares.auth import get_current_user_optional
from app.models.resource import Resource
from app.services.source_service import SourceService
from app.models.source_config import SOURCE_TYPES


router = APIRouter()


# ========== 响应模型 ==========


class HotSourceItem(BaseModel):
    """热门来源项"""

    name: str = Field(..., description="来源名称")
    icon: str = Field(..., description="来源图标 URL")
    totalCount: int = Field(..., description="总文章数")
    qualifiedCount: int = Field(..., description="高分文章数（score >= 85）")


class HotSourcesResponse(BaseModel):
    """热门来源列表响应"""

    items: List[HotSourceItem]


# ========== API 端点 ==========


@router.get("/hot", response_model=HotSourcesResponse)
def get_hot_sources(
    type: Literal["article", "podcast", "tweet", "video"] = Query(
        default="article", description="内容类型"
    ),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    minScore: float = Query(default=8.5, ge=0, le=10, description="最低评分"),
    db: Session = Depends(get_db),
):
    """
    获取热门来源列表

    按文章数量排序，返回指定类型下的热门来源

    Args:
        type: 内容类型（article/podcast/tweet/video）
        limit: 返回数量（1-50）
        minScore: 最低评分（用于计算合格文章数）
        db: 数据库会话

    Returns:
        热门来源列表

    Example:
        GET /api/sources/hot?type=article&limit=10&minScore=8.5

        Response:
        {
            "items": [
                {
                    "name": "Hacker News",
                    "icon": "https://icons.duckduckgo.com/ip3/news.ycombinator.com.ico",
                    "totalCount": 150,
                    "qualifiedCount": 45
                }
            ]
        }
    """
    # 查询当前类型下文章最多的来源
    # 注意：评分是 0-100，需要将 minScore (0-10) 转换为 0-100
    min_score_scaled = minScore * 10

    # 子查询：获取每个来源的统计信息（只按 source_name 分组）
    subquery = (
        db.query(
            Resource.source_name.label("name"),
            func.max(Resource.source_icon_url).label("icon"),  # 取该来源最常用的图标
            func.count(Resource.id).label("total_count"),
            func.count(Resource.id)
            .filter(Resource.score >= min_score_scaled)
            .label("qualified_count"),
        )
        .filter(Resource.type == type, Resource.status == "published")
        .group_by(Resource.source_name)
        .order_by(func.count(Resource.id).desc())
        .limit(limit)
        .subquery()
    )

    # 主查询：从子查询获取结果
    results = (
        db.query(subquery)
        .all()
    )

    items = [
        HotSourceItem(
            name=row.name or "Unknown",
            icon=row.icon or "",
            totalCount=row.total_count,
            qualifiedCount=row.qualified_count,
        )
        for row in results
    ]

    return HotSourcesResponse(items=items)


# ========== 信号源管理 API ==========


@router.get("/status")
async def get_all_sources_status(
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取所有信号源的状态概览

    返回 9 个信号源的：
    - 启用状态
    - 健康状态 (healthy/warning/error/disabled)
    - 最近一次采集信息
    - 24h 统计
    """
    service = SourceService(db)
    statuses = service.get_all_status()

    return {
        "success": True,
        "data": {
            "sources": statuses,
            "source_types": SOURCE_TYPES,
        },
    }


@router.get("/funnel")
async def get_funnel_stats(
    hours: int = Query(default=24, ge=1, le=168, description="统计时间范围（小时）"),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取聚合的采集漏斗统计

    漏斗阶段：
    - fetched: 原始抓取
    - rule_filtered: 规则过滤后
    - dedup_filtered: 去重后
    - llm_filtered: LLM 过滤后
    - saved: 最终存储
    """
    service = SourceService(db)
    funnel = service.get_funnel_stats(hours=hours)

    return {
        "success": True,
        "data": funnel,
    }


@router.get("/runs")
async def get_all_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取所有信号源的采集历史（分页）
    """
    service = SourceService(db)
    result = service.get_runs(page=page, page_size=page_size)

    return {
        "success": True,
        "data": result,
    }


@router.get("/detail/{source_type}")
async def get_source_detail(
    source_type: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取单个信号源的详细信息

    包含：
    - 配置信息 (yaml + override)
    - 最近 10 次采集记录
    - 24h 统计
    """
    if source_type not in SOURCE_TYPES:
        return {
            "success": False,
            "error": f"Unknown source type: {source_type}. Valid types: {SOURCE_TYPES}",
        }

    service = SourceService(db)
    detail = service.get_source_detail(source_type)

    return {
        "success": True,
        "data": detail,
    }


@router.post("/toggle/{source_type}")
async def toggle_source(
    source_type: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    切换信号源的启用/禁用状态
    """
    if source_type not in SOURCE_TYPES:
        return {
            "success": False,
            "error": f"Unknown source type: {source_type}. Valid types: {SOURCE_TYPES}",
        }

    service = SourceService(db)
    config = service.toggle_source(source_type)

    return {
        "success": True,
        "data": config,
        "message": f"Source {source_type} is now {'enabled' if config['enabled'] else 'disabled'}",
    }


@router.get("/runs/{source_type}")
async def get_source_runs(
    source_type: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取指定信号源的采集历史（分页）
    """
    if source_type not in SOURCE_TYPES:
        return {
            "success": False,
            "error": f"Unknown source type: {source_type}. Valid types: {SOURCE_TYPES}",
        }

    service = SourceService(db)
    result = service.get_runs(source_type=source_type, page=page, page_size=page_size)

    return {
        "success": True,
        "data": result,
    }


@router.get("/feeds/{source_type}")
async def get_source_feeds(
    source_type: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取 OPML 中的 feed 列表

    仅适用于使用 OPML 的信号源：twitter, blog, podcast, video
    """
    opml_sources = ["twitter", "blog", "podcast", "video"]
    if source_type not in opml_sources:
        return {
            "success": False,
            "error": f"Source type {source_type} does not use OPML. OPML sources: {opml_sources}",
        }

    service = SourceService(db)
    result = service.get_feeds(source_type)

    if "error" in result:
        return {
            "success": False,
            "error": result["error"],
        }

    return {
        "success": True,
        "data": result,
    }


# ========== 手动触发采集 API ==========


def _run_pipeline_in_background(source_type: str):
    """
    在后台线程运行对应的 pipeline

    支持的 source_type:
    - hackernews: HackerNews
    - github: GitHub Trending
    - huggingface: HuggingFace
    - twitter: Twitter (XGoing)
    - arxiv: arXiv 论文
    - producthunt: Product Hunt
    - blog: Blog RSS
    - podcast: Podcast RSS
    - video: Video/YouTube RSS
    """
    import structlog
    from app.config import config
    from app.tasks.pipeline import (
        run_article_pipeline,
        run_twitter_pipeline,
        run_full_pipeline,
    )

    logger = structlog.get_logger()
    logger.info(f"[Trigger] Starting {source_type} pipeline in background")

    # 创建新的事件循环来运行异步任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if source_type == "twitter":
            loop.run_until_complete(run_twitter_pipeline())
        elif source_type == "blog":
            # 使用 blog 配置中的 OPML 路径
            opml_path = getattr(config.blog, 'opml_path', None)
            loop.run_until_complete(run_article_pipeline(opml_path=opml_path))
        elif source_type == "podcast":
            opml_path = getattr(config.podcast, 'opml_path', None)
            loop.run_until_complete(run_article_pipeline(opml_path=opml_path))
        elif source_type == "video":
            opml_path = getattr(config.video, 'opml_path', None)
            loop.run_until_complete(run_article_pipeline(opml_path=opml_path))
        elif source_type in ["hackernews", "github", "huggingface", "arxiv", "producthunt"]:
            # 这些是 full_pipeline 的子类型
            loop.run_until_complete(run_full_pipeline(source_types=[source_type]))
        else:
            logger.warning(f"[Trigger] Unknown source type: {source_type}")
    except Exception as e:
        logger.error(f"[Trigger] Pipeline {source_type} failed: {e}")
    finally:
        loop.close()

    logger.info(f"[Trigger] {source_type} pipeline completed")


@router.post("/trigger/{source_type}")
async def trigger_source_pipeline(
    source_type: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    手动触发指定信号源的采集

    注意：
    - 采集在后台异步运行
    - 立即返回触发成功响应
    - 可通过 /status 或 /runs 查看采集结果
    """
    from app.models.source_config import SourceConfig

    if source_type not in SOURCE_TYPES:
        return {
            "success": False,
            "error": f"Unknown source type: {source_type}. Valid types: {SOURCE_TYPES}",
        }

    # 检查是否启用
    config = SourceConfig.get_or_create(db, source_type)

    if not config.enabled:
        return {
            "success": False,
            "error": f"Source {source_type} is disabled. Enable it first.",
        }

    # 在后台线程运行 pipeline
    background_tasks.add_task(_run_pipeline_in_background, source_type)

    return {
        "success": True,
        "message": f"Pipeline {source_type} triggered successfully. Check /runs for results.",
    }
