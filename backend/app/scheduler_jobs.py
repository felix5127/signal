"""
[INPUT]: 依赖 tasks/pipeline 的 run_full_pipeline, tasks/digest 的 generate_daily/weekly_digest, tasks/newsletter 的 generate_newsletter_sync
[OUTPUT]: 对外提供 scheduled_pipeline, scheduled_twitter_pipeline, scheduled_main_pipeline, daily_digest_job, weekly_digest_job, newsletter_job
[POS]: 定时任务函数定义，被 startup.py 的调度器配置引用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
from datetime import datetime
from typing import Optional

# 全局变量（用于健康检查）
last_run_time: Optional[datetime] = None


def scheduled_pipeline(sources: Optional[list[str]] = None):
    """
    APScheduler 调用的同步包装函数

    在新的事件循环中运行异步任务
    """
    from app.tasks.pipeline import run_full_pipeline

    global last_run_time

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_full_pipeline(sources=sources))
        last_run_time = datetime.now()
        print(f"[Scheduler] Pipeline completed at {last_run_time}")
    finally:
        loop.close()


def scheduled_twitter_pipeline():
    """Twitter 专用调度任务（每小时）"""
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
