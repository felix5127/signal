"""
[INPUT]: 依赖 scheduler_jobs 的所有定时任务函数, database 的 init_db, utils/cache 的 redis_cache
[OUTPUT]: 对外提供 register_startup_events 函数
[POS]: 应用启动/关闭事件处理，调度器初始化
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    BackgroundScheduler = None  # type: ignore

from fastapi import FastAPI

# 全局变量
scheduler: Optional[BackgroundScheduler] = None
next_run_time: Optional[datetime] = None


def register_startup_events(app: FastAPI):
    """
    注册应用启动和关闭事件

    Args:
        app: FastAPI 应用实例
    """

    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        global scheduler, next_run_time

        from app.database import init_db
        from app.utils.cache import redis_cache
        from app.scheduler_jobs import (
            scheduled_twitter_pipeline,
            scheduled_main_pipeline,
            daily_digest_job,
            weekly_digest_job,
            newsletter_job,
        )

        print("\n" + "=" * 60)
        print("Signal API Starting...")
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
        from app.utils.cache import redis_cache

        if SCHEDULER_AVAILABLE and scheduler and scheduler.running:
            print("\n[Shutdown] Stopping scheduler...")
            scheduler.shutdown()
            print("[Shutdown] Scheduler stopped\n")

        # 关闭Redis连接
        await redis_cache.close()
        print("[Shutdown] Redis cache closed")
