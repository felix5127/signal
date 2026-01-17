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


# 全局单例
stats_service = StatsService()
