"""
[INPUT]: 依赖 tasks/pipeline 的 run_full_pipeline, tasks/digest 的 generate_daily/weekly_digest, tasks/newsletter 的 generate_newsletter_sync
[OUTPUT]: 对外提供 scheduled_pipeline, scheduled_twitter_pipeline, scheduled_main_pipeline, daily_digest_job, weekly_digest_job, newsletter_job
[OUTPUT]: 对外提供 pipeline_state 全局状态对象（供 API 查询）
[POS]: 定时任务函数定义，被 startup.py 的调度器配置引用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class PipelineState:
    """
    Pipeline 运行状态追踪

    用于 Admin Dashboard 实时展示：
    - is_running: 是否正在运行
    - current_source: 当前正在处理的数据源
    - started_at: 本次运行开始时间
    - last_run_finished_at: 上次运行结束时间
    - last_run_status: 上次运行状态 (success/failed/partial)
    - last_run_saved_count: 上次运行保存数量
    """
    is_running: bool = False
    current_source: Optional[str] = None
    started_at: Optional[datetime] = None
    last_run_finished_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_saved_count: int = 0
    sources_to_run: List[str] = field(default_factory=list)
    sources_completed: List[str] = field(default_factory=list)


# 全局状态对象（用于 API 查询）
pipeline_state = PipelineState()

# 兼容旧代码的全局变量
last_run_time: Optional[datetime] = None


def scheduled_pipeline(sources: Optional[list[str]] = None):
    """
    APScheduler 调用的同步包装函数

    在新的事件循环中运行异步任务
    更新全局 pipeline_state 供 Admin Dashboard 查询
    """
    from app.tasks.pipeline import run_full_pipeline

    global last_run_time, pipeline_state

    # 更新状态：开始运行
    pipeline_state.is_running = True
    pipeline_state.started_at = datetime.now()
    pipeline_state.sources_to_run = sources or []
    pipeline_state.sources_completed = []
    pipeline_state.current_source = sources[0] if sources else "all"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_full_pipeline(sources=sources))
        last_run_time = datetime.now()
        pipeline_state.last_run_status = "success"
        print(f"[Scheduler] Pipeline completed at {last_run_time}")
    except Exception as e:
        pipeline_state.last_run_status = "failed"
        print(f"[Scheduler] Pipeline failed: {e}")
        raise
    finally:
        # 更新状态：运行结束
        pipeline_state.is_running = False
        pipeline_state.current_source = None
        pipeline_state.last_run_finished_at = datetime.now()
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
