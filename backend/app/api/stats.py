# Stats API路由
# 提供统计数据相关的API端点

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.signal_service import SignalService
from app.middlewares.auth import get_current_user_optional
from datetime import datetime

router = APIRouter()


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取统计数据

    包括信号总数、按来源/分类/评分的统计等
    """
    service = SignalService(db)
    stats = service.get_signal_stats()

    # 添加调度器信息（从全局变量获取）
    try:
        from app.main import last_run_time, next_run_time
        stats["scheduler"] = {
            "last_run": last_run_time.isoformat() if last_run_time else None,
            "next_run": next_run_time.isoformat() if next_run_time else None,
        }
    except ImportError:
        stats["scheduler"] = {
            "last_run": None,
            "next_run": None,
        }

    return {
        "success": True,
        "data": stats,
    }


@router.get("/health")
async def health_check():
    """
    健康检查端点

    检查数据库、Redis等服务状态
    """
    # 检查数据库连接
    db_status = "ok"
    try:
        from sqlalchemy import text
        from app.database import SessionLocal

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 检查Redis缓存
    redis_status = "disabled"
    try:
        from app.utils.cache import redis_cache

        if redis_cache.is_enabled():
            redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    # 调度器状态
    scheduler_status = "unknown"
    try:
        from app.main import last_run_time, next_run_time
        scheduler_status = "running"
    except ImportError:
        scheduler_status = "not available"

    return {
        "status": "ok",
        "service": "signal-hunter-backend",
        "database": db_status,
        "redis": redis_status,
        "scheduler": scheduler_status,
        "last_run": last_run_time.isoformat() if last_run_time else None,
        "next_run": next_run_time.isoformat() if next_run_time else None,
    }
