"""
[INPUT]: 依赖 database 的 get_db, services/signal_service 的 SignalService, APScheduler
[OUTPUT]: 对外提供 /stats 统计 + /scheduler 调度器状态 + /system 系统健康端点
[POS]: API 路由层，系统统计数据查询接口，调度器状态，系统健康监控
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import get_db
from app.services.signal_service import SignalService
from app.middlewares.auth import get_current_user_optional
from datetime import datetime, timedelta

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
    last_run_time = None
    next_run_time = None
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


# ========== 调度器状态 API ==========


@router.get("/stats/scheduler")
async def get_scheduler_status(
    user: str = Depends(get_current_user_optional),
):
    """
    获取调度器详细状态

    返回所有定时任务的：
    - 任务名称
    - 触发规则（cron 或 interval）
    - 上次运行时间
    - 下次运行时间
    - 运行状态
    """
    jobs = []

    try:
        from app.main import scheduler

        if scheduler and scheduler.running:
            for job in scheduler.get_jobs():
                # 解析触发器信息
                trigger_str = str(job.trigger)
                next_run = job.next_run_time

                jobs.append({
                    "id": job.id,
                    "name": job.name or job.id,
                    "trigger": trigger_str,
                    "next_run": next_run.isoformat() if next_run else None,
                    "next_run_human": _format_time_human(next_run) if next_run else "未调度",
                })

            return {
                "success": True,
                "data": {
                    "status": "running",
                    "jobs": jobs,
                },
            }
        else:
            return {
                "success": True,
                "data": {
                    "status": "stopped",
                    "jobs": [],
                },
            }
    except ImportError:
        return {
            "success": True,
            "data": {
                "status": "not_available",
                "jobs": [],
                "message": "Scheduler not initialized",
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _format_time_human(dt: datetime) -> str:
    """格式化时间为人类可读形式"""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = dt - now

    if diff.total_seconds() < 0:
        return "已过期"
    elif diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}秒后"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)}分钟后"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)}小时后"
    else:
        return f"{int(diff.total_seconds() / 86400)}天后"


# ========== 系统健康 API ==========


@router.get("/stats/system")
async def get_system_health(
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user_optional),
):
    """
    获取系统健康详细信息

    包括：
    - 数据库状态（连接数、大小、表统计）
    - Redis 状态（内存使用、键数量）
    - 存储统计（各表记录数、7天新增）
    """
    result = {
        "database": _check_database_health(db),
        "redis": _check_redis_health(),
        "storage": _get_storage_stats(db),
    }

    return {
        "success": True,
        "data": result,
    }


def _check_database_health(db: Session) -> dict:
    """检查数据库健康状态"""
    try:
        # 测试连接
        db.execute(text("SELECT 1"))

        # 获取数据库大小（PostgreSQL）
        try:
            size_result = db.execute(
                text("SELECT pg_database_size(current_database())")
            ).fetchone()
            db_size = size_result[0] if size_result else 0
            db_size_mb = round(db_size / (1024 * 1024), 2)
        except Exception:
            db_size_mb = None

        # 获取活跃连接数（PostgreSQL）
        try:
            conn_result = db.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            ).fetchone()
            active_connections = conn_result[0] if conn_result else 0
        except Exception:
            active_connections = None

        return {
            "status": "healthy",
            "message": "连接正常",
            "size_mb": db_size_mb,
            "active_connections": active_connections,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def _check_redis_health() -> dict:
    """检查 Redis 健康状态"""
    try:
        from app.utils.cache import redis_cache

        if not redis_cache.is_enabled():
            return {
                "status": "disabled",
                "message": "Redis 未启用",
            }

        # 获取 Redis 信息
        info = redis_cache.client.info()

        return {
            "status": "healthy",
            "message": "连接正常",
            "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
            "keys_count": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else 0,
            "connected_clients": info.get("connected_clients", 0),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def _get_storage_stats(db: Session) -> dict:
    """获取存储统计"""
    from app.models.resource import Resource
    from app.models.source_run import SourceRun

    try:
        # 各表记录数
        resource_count = db.query(func.count(Resource.id)).scalar() or 0
        source_run_count = db.query(func.count(SourceRun.id)).scalar() or 0

        # 7天新增
        seven_days_ago = datetime.now() - timedelta(days=7)
        new_resources_7d = (
            db.query(func.count(Resource.id))
            .filter(Resource.created_at >= seven_days_ago)
            .scalar()
            or 0
        )

        # 按类型统计
        type_stats = (
            db.query(Resource.type, func.count(Resource.id))
            .group_by(Resource.type)
            .all()
        )
        type_counts = {t: c for t, c in type_stats}

        return {
            "resources_total": resource_count,
            "source_runs_total": source_run_count,
            "new_resources_7d": new_resources_7d,
            "by_type": type_counts,
        }
    except Exception as e:
        return {
            "error": str(e),
        }
