# Signal Hunter 主应用入口
# FastAPI应用启动和配置

from datetime import datetime
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    BackgroundScheduler = None  # type: ignore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

# 导入配置
from app.config import config

# 导入数据库
from app.database import SessionLocal, get_db, init_db

# 导入中间件
from app.middlewares.error_handler import register_exception_handlers, PrettyJSONResponse
from app.middlewares.auth import get_current_user_optional

# 导入API路由
from app.api.digest import router as digest_router
from app.api.resources import router as resources_router
from app.api.feeds import router as feeds_router
from app.api.sources import router as sources_router
from app.api.signals import router as signals_router
from app.api.stats import router as stats_router
from app.api.newsletters import router as newsletters_router
from app.api.tasks import router as tasks_router

# 导入任务和服务
from app.tasks.pipeline import run_full_pipeline
from app.utils.cache import redis_cache

# 全局变量（用于健康检查）
last_run_time: Optional[datetime] = None
next_run_time: Optional[datetime] = None

# 创建FastAPI应用
app = FastAPI(
    title="AI Signal Hunter API",
    description="面向超级个体的技术情报分析系统",
    version="0.2.0",  # 更新版本号
    default_response_class=PrettyJSONResponse,
)

# 注册全局异常处理
register_exception_handlers(app)

# 注册API路由
app.include_router(digest_router, prefix="/api", tags=["digest"])
app.include_router(resources_router, prefix="/api", tags=["resources"])
app.include_router(feeds_router, prefix="/api/feeds", tags=["feeds"])
app.include_router(sources_router, prefix="/api/sources", tags=["sources"])
app.include_router(signals_router, prefix="/api", tags=["signals"])
app.include_router(stats_router, prefix="/api", tags=["stats"])
app.include_router(newsletters_router, prefix="/api", tags=["newsletters"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
        "https://signal.felixwithai.com",
        "https://felixwithai.com",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 基础端点
# ============================================================


@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "success": True,
        "message": "Welcome to AI Signal Hunter API",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# 定时任务调度器
# ============================================================

# APScheduler实例
scheduler: Optional[BackgroundScheduler] = None


def scheduled_pipeline(sources: Optional[list[str]] = None):
    """APScheduler调用的同步包装函数"""
    import asyncio

    global last_run_time

    # 在新的事件循环中运行异步任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_full_pipeline(sources=sources))
        last_run_time = datetime.now()
        print(f"[Scheduler] Pipeline completed at {last_run_time}")
    finally:
        loop.close()


def scheduled_twitter_pipeline():
    """Twitter专用调度任务（每小时）"""
    print("[Scheduler] Starting Twitter pipeline...")
    scheduled_pipeline(sources=["twitter"])


def scheduled_main_pipeline():
    """主要数据源调度任务（每12小时）"""
    print("[Scheduler] Starting main pipeline...")
    scheduled_pipeline(
        sources=["hn", "github", "huggingface", "arxiv", "producthunt", "blog"]
    )


def daily_digest_job():
    """每日汇总任务包装"""
    try:
        from app.tasks.digest import generate_daily_digest

        digest = generate_daily_digest()
        print(f"[DailyDigest] Generated for {digest.date}")
    except Exception as e:
        print(f"[DailyDigest] Error: {e}")


def weekly_digest_job():
    """每周汇总任务包装"""
    try:
        from app.tasks.digest import generate_weekly_digest

        digest = generate_weekly_digest()
        print(f"[WeeklyDigest] Generated for {digest.week_start}")
    except Exception as e:
        print(f"[WeeklyDigest] Error: {e}")


def newsletter_job():
    """周刊生成任务包装（同步版本）"""
    try:
        from app.tasks.newsletter import generate_newsletter_sync

        newsletter = generate_newsletter_sync()
        if newsletter:
            print(
                f"[Newsletter] Generated: Week {newsletter.week_number} of {newsletter.year}"
            )
        else:
            print("[Newsletter] Skipped (no content or already exists)")
    except Exception as e:
        print(f"[Newsletter] Error: {e}")


def _generate_resource_deep_research_background(resource_id: int, task_id: str, strategy: str = "lightweight"):
    """
    Resources Deep Research 后台任务处理器

    供 FastAPI BackgroundTasks 调用，在后台异步生成资源深度研究报告
    支持任务状态跟踪和进度更新

    Args:
        resource_id: 资源ID
        task_id: 任务ID（用于更新 TaskStatus）
        strategy: 研究策略 (lightweight/full_agent/auto)

    [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
    """
    import asyncio
    from app.database import SessionLocal
    from app.models.resource import Resource
    from app.models.task import TaskStatus
    from app.services.deep_research_service import DeepResearchService, ResearchStrategy

    db = SessionLocal()
    try:
        # 获取任务记录
        task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
        if not task:
            print(f"[DeepResearch] Task {task_id} not found")
            return

        # 获取资源对象
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            print(f"[DeepResearch] Resource {resource_id} not found")
            task.status = "failed"
            task.error = f"Resource {resource_id} not found"
            db.commit()
            return

        # 更新任务状态为运行中
        task.status = "running"
        task.started_at = datetime.now()
        task.progress = 0
        task.logs = [{"step": "正在初始化研究引擎...", "time": datetime.now().isoformat()}]
        db.commit()

        # 进度回调函数
        def update_progress(progress: float, step: str):
            task.progress = progress
            task.logs = task.logs or []
            task.logs.append({"step": step, "time": datetime.now().isoformat()})
            db.commit()

        # 解析策略
        try:
            research_strategy = ResearchStrategy(strategy)
        except ValueError:
            print(f"[DeepResearch] Unknown strategy '{strategy}', using 'lightweight'")
            research_strategy = ResearchStrategy.LIGHTWEIGHT

        # 创建新事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            service = DeepResearchService()
            service.engines[research_strategy].set_progress_callback(update_progress)

            result = loop.run_until_complete(
                service.generate_research(resource, strategy=research_strategy)
            )

            # 更新任务为成功状态
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            task.result = {
                "content": result.content,
                "sources": result.sources,
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
            }
            task.logs = (task.logs or []) + [{"step": "研究完成！", "time": datetime.now().isoformat()}]
            db.commit()

            print(
                f"[DeepResearch] Completed for resource {resource_id} "
                f"(tokens: {result.tokens_used}, cost: ${result.cost_usd:.4f})"
            )
        finally:
            loop.close()

    except Exception as e:
        print(f"[DeepResearch] Error for resource {resource_id}: {e}")
        # 更新任务为失败状态
        if task:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            db.commit()
    finally:
        db.close()


def _generate_deep_research_background(signal_id: int, strategy: str = "lightweight"):
    """
    Deep Research 后台任务处理器

    供 FastAPI BackgroundTasks 调用，在后台异步生成深度研究报告

    Args:
        signal_id: 信号ID
        strategy: 研究策略 (lightweight/full_agent/auto)

    [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
    """
    import asyncio
    from app.database import SessionLocal
    from app.models.signal import Signal
    from app.services.deep_research_service import DeepResearchService, ResearchStrategy

    db = SessionLocal()
    try:
        # 获取信号对象
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            print(f"[DeepResearch] Signal {signal_id} not found")
            return

        # 解析策略
        try:
            research_strategy = ResearchStrategy(strategy)
        except ValueError:
            print(f"[DeepResearch] Unknown strategy '{strategy}', using 'lightweight'")
            research_strategy = ResearchStrategy.LIGHTWEIGHT

        # 创建新事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            service = DeepResearchService()
            result = loop.run_until_complete(
                service.generate_research(signal, strategy=research_strategy)
            )

            print(
                f"[DeepResearch] Completed for signal {signal_id} "
                f"(tokens: {result.tokens_used}, cost: ${result.cost_usd:.4f})"
            )
        finally:
            loop.close()

    except Exception as e:
        print(f"[DeepResearch] Error for signal {signal_id}: {e}")
    finally:
        db.close()


# ============================================================
# 启动和关闭事件
# ============================================================


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    global scheduler, next_run_time

    print("\n" + "=" * 60)
    print("AI Signal Hunter API Starting...")
    print("=" * 60 + "\n")

    # 初始化数据库
    init_db()
    print("[Startup] Database initialized")

    # 初始化Redis缓存
    await redis_cache.connect()
    if redis_cache.is_enabled():
        print("[Startup] Redis cache connected")
    else:
        print("[Startup] Redis cache disabled (will use database only)")

    # 启动数据抓取调度器
    if SCHEDULER_AVAILABLE:
        scheduler = BackgroundScheduler()

        # Twitter数据源：每小时抓取一次
        scheduler.add_job(
            scheduled_twitter_pipeline,
            trigger="interval",
            hours=1,
            id="twitter_pipeline_job",
            name="Twitter Pipeline (Hourly)",
            replace_existing=True,
        )

        # 主要数据源：每12小时抓取一次
        scheduler.add_job(
            scheduled_main_pipeline,
            trigger="interval",
            hours=12,
            id="main_pipeline_job",
            name="Main Pipeline (12-hourly)",
            replace_existing=True,
        )

        # 添加每日汇总任务 (每天早上 7:00)
        scheduler.add_job(
            daily_digest_job,
            trigger="cron",
            hour=7,
            minute=0,
            id="daily_digest_job",
            name="Daily Digest Generator",
            replace_existing=True,
        )

        # 添加每周汇总任务 (每周一早上 8:00)
        scheduler.add_job(
            weekly_digest_job,
            trigger="cron",
            day_of_week="mon",
            hour=8,
            minute=0,
            id="weekly_digest_job",
            name="Weekly Digest Generator",
            replace_existing=True,
        )

        # 添加周刊生成任务 (每周五下午 5:00)
        scheduler.add_job(
            newsletter_job,
            trigger="cron",
            day_of_week="fri",
            hour=17,
            minute=0,
            id="newsletter_job",
            name="Weekly Newsletter Generator",
            replace_existing=True,
        )

        scheduler.start()

        # 获取下次运行时间
        twitter_job = scheduler.get_job("twitter_pipeline_job")
        main_job = scheduler.get_job("main_pipeline_job")

        print("[Startup] Scheduler started:")
        print(f"  - Twitter: Every 1 hour (next: {twitter_job.next_run_time})")
        print(f"  - Main sources: Every 12 hours (next: {main_job.next_run_time})")
        print(f"  - Daily digest: Every day at 07:00")
        print(f"  - Weekly digest: Every Monday at 08:00")
        print(f"  - Weekly newsletter: Every Friday at 17:00\n")
    else:
        print("[Startup] APScheduler not available - scheduler disabled\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    if SCHEDULER_AVAILABLE and scheduler and scheduler.running:
        print("\n[Shutdown] Stopping scheduler...")
        scheduler.shutdown()
        print("[Shutdown] Scheduler stopped\n")

    # 关闭Redis连接
    await redis_cache.close()
    print("[Shutdown] Redis cache closed")


# ============================================================
# 启动应用
# ============================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
