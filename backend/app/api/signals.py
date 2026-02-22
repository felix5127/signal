# Signals API路由
# 提供信号相关的API端点

from typing import Optional
from fastapi import APIRouter, Depends, Query
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


