# Signals API路由
# 提供信号相关的API端点

from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.signal_service import SignalService
from app.middlewares.validation import SignalFilter, PaginationParams
from app.middlewares.error_handler import NotFoundException
from app.middlewares.auth import get_current_user_optional

router = APIRouter()


@router.get("/signals")
async def get_signals(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: Optional[int] = Query(default=None, ge=1, le=5),
    source: Optional[str] = Query(default=None),
    sources: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at", regex="^(created_at|final_score)$"),
    db: Session = Depends(get_db),
    user: Optional[str] = Depends(get_current_user_optional),
):
    """
    获取信号列表

    支持多种筛选条件和分页
    """
    # 构建筛选器
    filters = SignalFilter(
        min_score=min_score,
        source=source,
        sources=sources,
        category=category,
        search=search,
        sort_by=sort_by,
    )

    # 创建服务实例
    service = SignalService(db)

    # 获取数据
    items, total = service.get_signals(filters, limit, offset)

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """
    获取单个信号详情
    """
    service = SignalService(db)
    signal = service.get_signal_by_id(signal_id)

    if not signal:
        raise NotFoundException(f"Signal {signal_id} not found")

    return {
        "success": True,
        "data": signal,
    }


@router.get("/signals/{signal_id}/deep-research")
async def get_deep_research(signal_id: int, db: Session = Depends(get_db)):
    """
    获取信号的深度研究报告
    """
    service = SignalService(db)
    research = service.get_deep_research(signal_id)

    if not research:
        raise NotFoundException(f"Deep research for signal {signal_id} not found")

    return {
        "success": True,
        "data": research,
    }


@router.post("/signals/{signal_id}/deep-research")
async def generate_deep_research(
    signal_id: int,
    background_tasks: BackgroundTasks,
    strategy: str = Query(default="lightweight", pattern="^(lightweight|full_agent|auto)$"),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    生成深度研究报告（后台异步执行）

    Args:
        signal_id: 信号ID
        background_tasks: FastAPI后台任务
        strategy: 研究策略 (lightweight/full_agent/auto)
        force: 强制重新生成，忽略缓存

    Returns:
        任务状态信息
    """
    from datetime import datetime
    from app.config import config

    service = SignalService(db)
    signal = service.get_signal_by_id(signal_id)

    if not signal:
        raise NotFoundException(f"Signal {signal_id} not found")

    # 检查缓存（需要从原始数据库模型获取）
    from app.models.signal import Signal as SignalModel
    signal_model = db.query(SignalModel).filter(SignalModel.id == signal_id).first()

    if signal_model and not force and signal_model.deep_dive and signal_model.deep_dive_generated_at:
        cache_age = datetime.now() - signal_model.deep_dive_generated_at
        cache_hours = config.deep_research.cache_duration_hours

        if cache_age.total_seconds() < cache_hours * 3600:
            return {
                "success": True,
                "data": {
                    "status": "cached",
                    "message": "Report already exists and is still fresh",
                    "signal_id": signal_id,
                    "generated_at": signal_model.deep_dive_generated_at.isoformat(),
                    "cache_age_hours": cache_age.total_seconds() / 3600,
                }
            }

    # 添加后台任务
    from app.main import _generate_deep_research_background
    background_tasks.add_task(_generate_deep_research_background, signal_id, strategy)

    return {
        "success": True,
        "data": {
            "status": "processing",
            "message": "Deep research report generation started in background",
            "signal_id": signal_id,
            "strategy": strategy,
            "estimated_time_seconds": "60-120",
        }
    }
