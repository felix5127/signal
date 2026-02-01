# 定时任务调度器
# 管理所有APScheduler定时任务

from datetime import datetime
from typing import Optional
import asyncio


class TaskScheduler:
    """任务调度器管理类"""

    def __init__(self, scheduler):
        """
        初始化调度器

        Args:
            scheduler: APScheduler实例
        """
        self.scheduler = scheduler
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None

    def register_all_jobs(self):
        """注册所有定时任务"""
        # Twitter数据源：每小时抓取一次
        self.scheduler.add_job(
            self.scheduled_twitter_pipeline,
            trigger="interval",
            hours=1,
            id="twitter_pipeline_job",
            name="Twitter Pipeline (Hourly)",
            replace_existing=True,
        )

        # 主要数据源：每12小时抓取一次
        self.scheduler.add_job(
            self.scheduled_main_pipeline,
            trigger="interval",
            hours=12,
            id="main_pipeline_job",
            name="Main Pipeline (12-hourly)",
            replace_existing=True,
        )

        # 添加每日汇总任务 (每天早上 7:00)
        self.scheduler.add_job(
            self.daily_digest_job,
            trigger="cron",
            hour=7,
            minute=0,
            id="daily_digest_job",
            name="Daily Digest Generator",
            replace_existing=True,
        )

        # 添加每周汇总任务 (每周一早上 8:00)
        self.scheduler.add_job(
            self.weekly_digest_job,
            trigger="cron",
            day_of_week="mon",
            hour=8,
            minute=0,
            id="weekly_digest_job",
            name="Weekly Digest Generator",
            replace_existing=True,
        )

        # 添加周刊生成任务 (每周五下午 5:00)
        self.scheduler.add_job(
            self.newsletter_job,
            trigger="cron",
            day_of_week="fri",
            hour=17,
            minute=0,
            id="newsletter_job",
            name="Weekly Newsletter Generator",
            replace_existing=True,
        )

        # 更新下次运行时间
        self._update_next_run_time()

        print("[Scheduler] All jobs registered successfully")

    def _update_next_run_time(self):
        """更新下次运行时间"""
        try:
            twitter_job = self.scheduler.get_job("twitter_pipeline_job")
            if twitter_job:
                self.next_run_time = twitter_job.next_run_time
        except Exception as e:
            print(f"[Scheduler] Warning: Could not get next run time: {e}")

    def scheduled_pipeline(self, sources: Optional[list[str]] = None):
        """APScheduler调用的同步包装函数"""
        from app.tasks.pipeline import run_full_pipeline

        global last_run_time

        # 在新的事件循环中运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_full_pipeline(sources=sources))
            self.last_run_time = datetime.now()
            print(f"[Scheduler] Pipeline completed at {self.last_run_time}")
        finally:
            loop.close()

    def scheduled_twitter_pipeline(self):
        """Twitter专用调度任务（每小时）"""
        print("[Scheduler] Starting Twitter pipeline...")
        self.scheduled_pipeline(sources=["twitter"])

    def scheduled_main_pipeline(self):
        """主要数据源调度任务（每12小时）"""
        print("[Scheduler] Starting main pipeline...")
        # 已移除: hn, github, huggingface, arxiv, producthunt (scraper 已删除)
        self.scheduled_pipeline(
            sources=["blog", "podcast"]
        )

    def daily_digest_job(self):
        """每日汇总任务包装"""
        try:
            from app.tasks.digest import generate_daily_digest

            digest = generate_daily_digest()
            print(f"[DailyDigest] Generated for {digest.date}")
        except Exception as e:
            print(f"[DailyDigest] Error: {e}")

    def weekly_digest_job(self):
        """每周汇总任务包装"""
        try:
            from app.tasks.digest import generate_weekly_digest

            digest = generate_weekly_digest()
            print(f"[WeeklyDigest] Generated for {digest.week_start}")
        except Exception as e:
            print(f"[WeeklyDigest] Error: {e}")

    def newsletter_job(self):
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

    def get_job_info(self) -> dict:
        """
        获取所有任务信息

        Returns:
            任务信息字典
        """
        jobs = self.scheduler.get_jobs()

        return {
            "total_jobs": len(jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in jobs
            ],
            "last_run": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run": self.next_run_time.isoformat() if self.next_run_time else None,
        }


# 全局调度器实例
task_scheduler: Optional[TaskScheduler] = None
last_run_time: Optional[datetime] = None
next_run_time: Optional[datetime] = None


def initialize_scheduler(scheduler) -> TaskScheduler:
    """
    初始化调度器

    Args:
        scheduler: APScheduler实例

    Returns:
        TaskScheduler实例
    """
    global task_scheduler, last_run_time, next_run_time

    task_scheduler = TaskScheduler(scheduler)
    task_scheduler.register_all_jobs()

    # 更新全局变量（保持向后兼容）
    last_run_time = task_scheduler.last_run_time
    next_run_time = task_scheduler.next_run_time

    return task_scheduler


def get_scheduler() -> Optional[TaskScheduler]:
    """获取全局调度器实例"""
    return task_scheduler
