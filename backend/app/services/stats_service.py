"""
[INPUT]: 依赖 database.py (SessionLocal), models/resource.py (Resource), models/source.py (Source)
[OUTPUT]: 对外提供 StatsService 类
[POS]: 服务层，统计数据业务逻辑
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import func, desc, cast, Date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.resource import Resource
from app.models.source import Source


class StatsService:
    """
    统计服务

    支持：
    - 整体统计
    - 按数据源统计
    - 按时间统计
    - LLM 评分分布
    """

    def __init__(self, db: Optional[Session] = None):
        """
        初始化服务

        Args:
            db: 数据库 Session（可选）
        """
        self._db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        """获取数据库 Session"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _close_db(self):
        """关闭自己创建的 Session"""
        if self._owns_session and self._db is not None:
            self._db.close()
            self._db = None

    def get_overview_stats(self) -> Dict[str, Any]:
        """
        获取整体统计概览

        Returns:
            整体统计数据
        """
        db = self._get_db()
        try:
            # 总数统计
            total = db.query(func.count(Resource.id)).scalar() or 0

            # 按状态统计
            status_stats = db.query(
                Resource.status,
                func.count(Resource.id)
            ).group_by(Resource.status).all()

            stats_by_status = {s: c for s, c in status_stats}

            # 今日统计
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            today_total = db.query(func.count(Resource.id)).filter(
                Resource.created_at >= today_start
            ).scalar() or 0

            today_published = db.query(func.count(Resource.id)).filter(
                Resource.created_at >= today_start,
                Resource.status == "published"
            ).scalar() or 0

            # 平均 LLM 评分
            avg_score = db.query(func.avg(Resource.llm_score)).filter(
                Resource.llm_score.isnot(None)
            ).scalar() or 0

            # 数据源数量
            source_count = db.query(func.count(Source.id)).scalar() or 0
            whitelist_count = db.query(func.count(Source.id)).filter(
                Source.is_whitelist == True
            ).scalar() or 0

            return {
                "total": total,
                "by_status": {
                    "pending": stats_by_status.get("pending", 0),
                    "approved": stats_by_status.get("approved", 0),
                    "rejected": stats_by_status.get("rejected", 0),
                    "published": stats_by_status.get("published", 0),
                },
                "today": {
                    "total": today_total,
                    "published": today_published,
                },
                "avg_llm_score": round(float(avg_score), 2),
                "sources": {
                    "total": source_count,
                    "whitelist": whitelist_count,
                },
            }
        finally:
            if self._owns_session:
                self._close_db()

    def get_source_stats(self, source_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取数据源统计

        Args:
            source_id: 指定数据源 ID（可选，不传则返回所有）

        Returns:
            数据源统计列表
        """
        db = self._get_db()
        try:
            query = db.query(Source)

            if source_id:
                query = query.filter(Source.id == source_id)

            sources = query.all()

            result = []
            for source in sources:
                # 计算实时统计（如果数据库统计字段未更新）
                collected = db.query(func.count(Resource.id)).filter(
                    Resource.source_id == source.id
                ).scalar() or 0

                approved = db.query(func.count(Resource.id)).filter(
                    Resource.source_id == source.id,
                    Resource.status.in_(["approved", "published"])
                ).scalar() or 0

                rejected = db.query(func.count(Resource.id)).filter(
                    Resource.source_id == source.id,
                    Resource.status == "rejected"
                ).scalar() or 0

                avg_score = db.query(func.avg(Resource.llm_score)).filter(
                    Resource.source_id == source.id,
                    Resource.llm_score.isnot(None)
                ).scalar() or 0

                result.append({
                    "id": source.id,
                    "name": source.name,
                    "type": source.type,
                    "url": source.url,
                    "enabled": source.enabled,
                    "is_whitelist": source.is_whitelist,
                    "stats": {
                        "total_collected": collected,
                        "total_approved": approved,
                        "total_rejected": rejected,
                        "approval_rate": round(approved / collected, 2) if collected > 0 else 0,
                        "avg_llm_score": round(float(avg_score), 2),
                    },
                    "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
                })

            return result
        finally:
            if self._owns_session:
                self._close_db()

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日统计

        Args:
            days: 统计天数

        Returns:
            每日统计列表
        """
        db = self._get_db()
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days - 1)
            start_datetime = datetime.combine(start_date, datetime.min.time())

            # 按日期分组统计
            daily_stats = db.query(
                cast(Resource.created_at, Date).label("date"),
                func.count(Resource.id).label("total"),
                func.count(Resource.id).filter(Resource.status == "published").label("published"),
                func.count(Resource.id).filter(Resource.status == "rejected").label("rejected"),
                func.avg(Resource.llm_score).label("avg_score"),
            ).filter(
                Resource.created_at >= start_datetime
            ).group_by(
                cast(Resource.created_at, Date)
            ).order_by(
                cast(Resource.created_at, Date)
            ).all()

            result = []
            for stat in daily_stats:
                result.append({
                    "date": stat.date.isoformat() if stat.date else None,
                    "total": stat.total or 0,
                    "published": stat.published or 0,
                    "rejected": stat.rejected or 0,
                    "avg_score": round(float(stat.avg_score or 0), 2),
                })

            return result
        finally:
            if self._owns_session:
                self._close_db()

    def get_score_distribution(self, source_id: Optional[int] = None) -> Dict[int, int]:
        """
        获取 LLM 评分分布

        Args:
            source_id: 数据源 ID（可选）

        Returns:
            评分分布 {0: N, 1: N, 2: N, 3: N, 4: N, 5: N}
        """
        db = self._get_db()
        try:
            query = db.query(
                Resource.llm_score,
                func.count(Resource.id)
            ).filter(
                Resource.llm_score.isnot(None)
            )

            if source_id:
                query = query.filter(Resource.source_id == source_id)

            stats = query.group_by(Resource.llm_score).all()

            # 初始化所有分数
            distribution = {i: 0 for i in range(6)}
            for score, count in stats:
                if score is not None and 0 <= score <= 5:
                    distribution[score] = count

            return distribution
        finally:
            if self._owns_session:
                self._close_db()


    # ========== 数据质量监控 (新增) ==========

    def get_data_quality_stats(self) -> Dict[str, Any]:
        """
        获取内容完整率统计

        按内容类型统计关键字段的填充率：
        - podcast: audio_url, transcript, chapters
        - video: transcript, chapters
        - article: content_markdown, summary

        Returns:
            各类型内容的完整率统计
        """
        db = self._get_db()
        try:
            # 播客质量统计
            podcast_total = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast"
            ).scalar() or 0

            podcast_has_audio = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast",
                Resource.audio_url.isnot(None),
                Resource.audio_url != ""
            ).scalar() or 0

            podcast_has_transcript = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast",
                Resource.transcript.isnot(None),
                Resource.transcript != ""
            ).scalar() or 0

            podcast_has_chapters = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast",
                Resource.chapters.isnot(None)
            ).scalar() or 0

            # 视频质量统计
            video_total = db.query(func.count(Resource.id)).filter(
                Resource.type == "video"
            ).scalar() or 0

            video_has_transcript = db.query(func.count(Resource.id)).filter(
                Resource.type == "video",
                Resource.transcript.isnot(None),
                Resource.transcript != ""
            ).scalar() or 0

            video_has_chapters = db.query(func.count(Resource.id)).filter(
                Resource.type == "video",
                Resource.chapters.isnot(None)
            ).scalar() or 0

            # 文章质量统计
            article_total = db.query(func.count(Resource.id)).filter(
                Resource.type == "article"
            ).scalar() or 0

            article_has_content = db.query(func.count(Resource.id)).filter(
                Resource.type == "article",
                Resource.content_markdown.isnot(None),
                Resource.content_markdown != ""
            ).scalar() or 0

            article_has_summary = db.query(func.count(Resource.id)).filter(
                Resource.type == "article",
                Resource.summary.isnot(None),
                Resource.summary != ""
            ).scalar() or 0

            # 计算完整率
            def calc_rate(count: int, total: int) -> float:
                return round(count / total * 100, 1) if total > 0 else 0.0

            podcast_completeness = calc_rate(podcast_has_audio, podcast_total)
            video_completeness = calc_rate(video_has_transcript, video_total)
            article_completeness = calc_rate(article_has_content, article_total)

            # 整体完整率 (加权平均)
            total_items = podcast_total + video_total + article_total
            if total_items > 0:
                overall = (
                    podcast_has_audio + video_has_transcript + article_has_content
                ) / total_items * 100
            else:
                overall = 0.0

            return {
                "podcast_quality": {
                    "total": podcast_total,
                    "has_audio_url": podcast_has_audio,
                    "has_transcript": podcast_has_transcript,
                    "has_chapters": podcast_has_chapters,
                    "completeness_rate": podcast_completeness,
                },
                "video_quality": {
                    "total": video_total,
                    "has_transcript": video_has_transcript,
                    "has_chapters": video_has_chapters,
                    "completeness_rate": video_completeness,
                },
                "article_quality": {
                    "total": article_total,
                    "has_content": article_has_content,
                    "has_summary": article_has_summary,
                    "completeness_rate": article_completeness,
                },
                "overall_completeness": round(overall, 1),
            }
        finally:
            if self._owns_session:
                self._close_db()

    def get_source_health_stats(self) -> Dict[str, Any]:
        """
        获取 RSS 源健康状态

        根据最近 7 天的采集记录评估数据源健康：
        - healthy: 成功率 >= 80%
        - degraded: 成功率 50-80%
        - failing: 成功率 < 50% 或最近 3 天无采集

        Returns:
            数据源健康状态统计
        """
        db = self._get_db()
        try:
            from app.models.source_run import SourceRun

            # 获取所有启用的数据源
            sources = db.query(Source).filter(Source.enabled == True).all()

            # 最近 7 天
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            three_days_ago = datetime.utcnow() - timedelta(days=3)

            result_sources = []
            summary = {"healthy": 0, "degraded": 0, "failing": 0}

            for source in sources:
                # 获取最近 7 天的采集记录
                runs = db.query(SourceRun).filter(
                    SourceRun.source_type == source.type,
                    SourceRun.started_at >= seven_days_ago
                ).all()

                total_runs = len(runs)
                success_runs = len([r for r in runs if r.status == "success"])

                # 最近一次采集时间
                latest_run = db.query(SourceRun).filter(
                    SourceRun.source_type == source.type
                ).order_by(desc(SourceRun.started_at)).first()

                # 计算成功率
                success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0

                # 判断健康状态
                if total_runs == 0:
                    health_status = "failing"
                elif latest_run and latest_run.started_at < three_days_ago:
                    health_status = "failing"
                elif success_rate >= 80:
                    health_status = "healthy"
                elif success_rate >= 50:
                    health_status = "degraded"
                else:
                    health_status = "failing"

                summary[health_status] += 1

                # 计算字段完整率
                field_completeness = {}
                if source.type in ["podcast", "video"]:
                    resources = db.query(Resource).filter(
                        Resource.source_id == source.id
                    ).all()
                    total_resources = len(resources)
                    if total_resources > 0:
                        if source.type == "podcast":
                            has_audio = len([r for r in resources if r.audio_url])
                            has_transcript = len([r for r in resources if r.transcript])
                            field_completeness = {
                                "audio_url": round(has_audio / total_resources * 100, 1),
                                "transcript": round(has_transcript / total_resources * 100, 1),
                            }
                        else:  # video
                            has_transcript = len([r for r in resources if r.transcript])
                            field_completeness = {
                                "transcript": round(has_transcript / total_resources * 100, 1),
                            }

                result_sources.append({
                    "id": source.id,
                    "name": source.name,
                    "type": source.type,
                    "url": source.url,
                    "collection_success_rate": round(success_rate, 1),
                    "field_completeness": field_completeness,
                    "health_status": health_status,
                    "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
                    "last_error": source.last_error,
                })

            # 按健康状态排序（failing 优先显示）
            status_order = {"failing": 0, "degraded": 1, "healthy": 2}
            result_sources.sort(key=lambda x: status_order.get(x["health_status"], 3))

            return {
                "sources": result_sources,
                "summary": summary,
            }
        finally:
            if self._owns_session:
                self._close_db()

    def get_transcription_stats(self) -> Dict[str, Any]:
        """
        获取转写成功率统计

        统计有音频但无转录的记录，计算转写成功率

        Returns:
            转写成功率统计
        """
        db = self._get_db()
        try:
            # 播客转写统计
            podcast_with_audio = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast",
                Resource.audio_url.isnot(None),
                Resource.audio_url != ""
            ).scalar() or 0

            podcast_transcribed = db.query(func.count(Resource.id)).filter(
                Resource.type == "podcast",
                Resource.audio_url.isnot(None),
                Resource.audio_url != "",
                Resource.transcript.isnot(None),
                Resource.transcript != ""
            ).scalar() or 0

            podcast_pending = podcast_with_audio - podcast_transcribed

            # 视频转写统计 (假设视频都需要转写)
            video_total = db.query(func.count(Resource.id)).filter(
                Resource.type == "video"
            ).scalar() or 0

            video_transcribed = db.query(func.count(Resource.id)).filter(
                Resource.type == "video",
                Resource.transcript.isnot(None),
                Resource.transcript != ""
            ).scalar() or 0

            video_pending = video_total - video_transcribed

            # 获取最近失败的记录 (有音频无转录，最近创建的)
            recent_failures = db.query(Resource).filter(
                Resource.type == "podcast",
                Resource.audio_url.isnot(None),
                Resource.audio_url != "",
                (Resource.transcript.is_(None)) | (Resource.transcript == "")
            ).order_by(desc(Resource.created_at)).limit(5).all()

            recent_failures_list = [
                {
                    "resource_id": r.id,
                    "title": r.title[:50] + "..." if len(r.title) > 50 else r.title,
                    "source_name": r.source_name,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recent_failures
            ]

            return {
                "podcast": {
                    "with_audio": podcast_with_audio,
                    "transcribed": podcast_transcribed,
                    "success_rate": round(podcast_transcribed / podcast_with_audio * 100, 1) if podcast_with_audio > 0 else 0.0,
                    "pending": podcast_pending,
                },
                "video": {
                    "total": video_total,
                    "transcribed": video_transcribed,
                    "success_rate": round(video_transcribed / video_total * 100, 1) if video_total > 0 else 0.0,
                    "pending": video_pending,
                },
                "recent_failures": recent_failures_list,
            }
        finally:
            if self._owns_session:
                self._close_db()


    # ========== Pipeline 状态与处理队列 (新增) ==========

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        获取 Pipeline 实时运行状态

        返回数据供 Admin Dashboard 展示：
        - pipeline: 当前运行状态 (is_running, current_source, started_at)
        - last_run: 上次运行信息 (finished_at, status, saved_count)
        - next_run: 下次运行信息 (scheduled_at, countdown_seconds)
        - queue: 处理队列统计 (pending_translation, pending_transcription)

        Returns:
            Pipeline 状态数据
        """
        from app.scheduler_jobs import pipeline_state
        from app.startup import scheduler

        # 获取调度器下次运行时间
        next_run_info = {"scheduled_at": None, "countdown_seconds": None}
        if scheduler and scheduler.running:
            # 获取最近的下次运行时间 (Twitter 每小时, Main 每 12 小时)
            twitter_job = scheduler.get_job("twitter_pipeline_job")
            main_job = scheduler.get_job("main_pipeline_job")

            next_times = []
            if twitter_job and twitter_job.next_run_time:
                next_times.append(twitter_job.next_run_time)
            if main_job and main_job.next_run_time:
                next_times.append(main_job.next_run_time)

            if next_times:
                # 取最近的下次运行时间
                next_run = min(next_times)
                next_run_info["scheduled_at"] = next_run.isoformat()
                # 计算倒计时秒数
                from datetime import timezone
                now = datetime.now(timezone.utc) if next_run.tzinfo else datetime.now()
                countdown = (next_run - now).total_seconds()
                next_run_info["countdown_seconds"] = max(0, int(countdown))

        # 从 SourceRun 获取上次运行的详细信息
        db = self._get_db()
        try:
            from app.models.source_run import SourceRun
            from sqlalchemy import desc

            last_run = db.query(SourceRun).order_by(
                desc(SourceRun.finished_at)
            ).first()

            last_run_info = {
                "finished_at": None,
                "status": None,
                "saved_count": 0,
                "source_type": None,
            }
            if last_run:
                last_run_info = {
                    "finished_at": last_run.finished_at.isoformat() if last_run.finished_at else None,
                    "status": last_run.status,
                    "saved_count": last_run.saved_count or 0,
                    "source_type": last_run.source_type,
                }

            # 获取处理队列统计
            queue_stats = self._get_processing_queue_stats(db)

            return {
                "pipeline": {
                    "is_running": pipeline_state.is_running,
                    "current_source": pipeline_state.current_source,
                    "started_at": pipeline_state.started_at.isoformat() if pipeline_state.started_at else None,
                },
                "last_run": last_run_info,
                "next_run": next_run_info,
                "queue": queue_stats,
            }
        finally:
            if self._owns_session:
                self._close_db()

    def _get_processing_queue_stats(self, db: Session) -> Dict[str, int]:
        """
        获取处理队列统计

        统计待处理的内容数量：
        - pending_translation: 需要翻译的内容 (非中文且无翻译)
        - pending_transcription: 需要转写的内容 (有音频无转录)

        Args:
            db: 数据库 Session

        Returns:
            队列统计数据
        """
        # 待翻译: 非中文的文章和播客，且没有中文摘要
        # 注意：推文(tweet)和视频(video)不计入待翻译统计
        # - 推文设计为原文展示，不需要翻译
        # - 视频功能已禁用
        pending_translation = db.query(func.count(Resource.id)).filter(
            Resource.language != "zh",
            Resource.type.in_(["article", "podcast"]),  # 仅统计文章和播客
            Resource.status == "published",
            (Resource.summary_zh.is_(None)) | (Resource.summary_zh == "")
        ).scalar() or 0

        # 待转写: 播客有音频但无转录
        pending_transcription_podcast = db.query(func.count(Resource.id)).filter(
            Resource.type == "podcast",
            Resource.audio_url.isnot(None),
            Resource.audio_url != "",
            (Resource.transcript.is_(None)) | (Resource.transcript == "")
        ).scalar() or 0

        # 视频功能已禁用，不再统计视频转写
        # pending_transcription_video = 0

        return {
            "pending_translation": pending_translation,
            "pending_transcription": pending_transcription_podcast,  # 仅统计播客
        }

    def get_today_funnel_stats(self) -> Dict[str, int]:
        """
        获取今日采集漏斗统计

        汇总今日所有 SourceRun 的漏斗数据：
        - fetched: 总抓取数
        - rule_filtered: 规则过滤后
        - dedup_filtered: 去重后
        - llm_filtered: LLM 过滤后
        - saved: 最终保存

        Returns:
            今日漏斗统计
        """
        db = self._get_db()
        try:
            from app.models.source_run import SourceRun

            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            runs = db.query(SourceRun).filter(
                SourceRun.started_at >= today_start
            ).all()

            funnel = {
                "fetched": 0,
                "rule_filtered": 0,
                "dedup_filtered": 0,
                "llm_filtered": 0,
                "saved": 0,
            }

            for run in runs:
                funnel["fetched"] += run.fetched_count or 0
                funnel["rule_filtered"] += run.rule_filtered_count or 0
                funnel["dedup_filtered"] += run.dedup_filtered_count or 0
                funnel["llm_filtered"] += run.llm_filtered_count or 0
                funnel["saved"] += run.saved_count or 0

            return funnel
        finally:
            if self._owns_session:
                self._close_db()


# 全局单例
stats_service = StatsService()
