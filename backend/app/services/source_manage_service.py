"""
[INPUT]: 依赖 database.py (SessionLocal), models/source.py (Source)
[OUTPUT]: 对外提供 SourceManageService 类
[POS]: 服务层，数据源管理业务逻辑（基于 Source 模型）
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.source import Source
from app.models.resource import Resource


class SourceManageService:
    """
    数据源管理服务

    管理 Source 模型，支持：
    - CRUD 操作
    - 白名单设置
    - 启用/禁用
    - 统计数据更新
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

    def get_all_sources(
        self,
        source_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        is_whitelist: Optional[bool] = None,
    ) -> List[Source]:
        """
        获取所有数据源

        Args:
            source_type: 类型筛选 (blog/twitter/podcast/video)
            enabled: 启用状态筛选
            is_whitelist: 白名单筛选

        Returns:
            Source 列表
        """
        db = self._get_db()
        try:
            query = db.query(Source)

            if source_type:
                query = query.filter(Source.type == source_type)
            if enabled is not None:
                query = query.filter(Source.enabled == enabled)
            if is_whitelist is not None:
                query = query.filter(Source.is_whitelist == is_whitelist)

            return query.order_by(Source.type, Source.name).all()
        finally:
            if self._owns_session:
                self._close_db()

    def get_source_by_id(self, source_id: int) -> Optional[Source]:
        """根据 ID 获取数据源"""
        db = self._get_db()
        try:
            return db.query(Source).filter(Source.id == source_id).first()
        finally:
            if self._owns_session:
                self._close_db()

    def get_source_by_url(self, url: str) -> Optional[Source]:
        """根据 URL 获取数据源"""
        db = self._get_db()
        try:
            return db.query(Source).filter(Source.url == url).first()
        finally:
            if self._owns_session:
                self._close_db()

    def create_source(
        self,
        name: str,
        source_type: str,
        url: str,
        is_whitelist: bool = False,
    ) -> Source:
        """
        创建数据源

        Args:
            name: 数据源名称
            source_type: 类型
            url: RSS URL
            is_whitelist: 是否白名单

        Returns:
            新创建的 Source 对象
        """
        db = self._get_db()
        try:
            source = Source(
                name=name,
                type=source_type,
                url=url,
                enabled=True,
                is_whitelist=is_whitelist,
                created_at=datetime.utcnow(),
            )

            db.add(source)
            db.commit()
            db.refresh(source)

            return source
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def update_source(
        self,
        source_id: int,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        is_whitelist: Optional[bool] = None,
    ) -> Optional[Source]:
        """
        更新数据源

        Args:
            source_id: 数据源 ID
            name: 新名称
            enabled: 是否启用
            is_whitelist: 是否白名单

        Returns:
            更新后的 Source 对象
        """
        db = self._get_db()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                return None

            if name is not None:
                source.name = name
            if enabled is not None:
                source.enabled = enabled
            if is_whitelist is not None:
                source.is_whitelist = is_whitelist

            source.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(source)

            return source
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def delete_source(self, source_id: int) -> bool:
        """
        删除数据源

        Args:
            source_id: 数据源 ID

        Returns:
            是否成功删除
        """
        db = self._get_db()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                return False

            db.delete(source)
            db.commit()

            return True
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def set_whitelist(self, source_id: int, is_whitelist: bool) -> Optional[Source]:
        """
        设置白名单状态

        Args:
            source_id: 数据源 ID
            is_whitelist: 是否白名单

        Returns:
            更新后的 Source 对象
        """
        return self.update_source(source_id, is_whitelist=is_whitelist)

    def toggle_enabled(self, source_id: int) -> Optional[Source]:
        """
        切换启用状态

        Args:
            source_id: 数据源 ID

        Returns:
            更新后的 Source 对象
        """
        db = self._get_db()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                return None

            source.enabled = not source.enabled
            source.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(source)

            return source
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def update_source_stats(self, source_id: int) -> Optional[Source]:
        """
        更新数据源统计数据

        从 Resource 表聚合计算统计数据

        Args:
            source_id: 数据源 ID

        Returns:
            更新后的 Source 对象
        """
        db = self._get_db()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                return None

            # 聚合统计
            stats = db.query(
                func.count(Resource.id).label("total"),
                func.count(Resource.id).filter(
                    Resource.status.in_(["approved", "published"])
                ).label("approved"),
                func.count(Resource.id).filter(
                    Resource.status == "rejected"
                ).label("rejected"),
                func.count(Resource.id).filter(
                    Resource.status == "published"
                ).label("published"),
                func.count(Resource.id).filter(
                    Resource.review_status == "restore"
                ).label("overturned"),
                func.avg(Resource.llm_score).label("avg_score"),
            ).filter(
                Resource.source_id == source_id
            ).first()

            if stats:
                source.total_collected = stats.total or 0
                source.total_approved = stats.approved or 0
                source.total_rejected = stats.rejected or 0
                source.total_published = stats.published or 0
                source.total_review_overturned = stats.overturned or 0
                source.avg_llm_score = float(stats.avg_score or 0)

            source.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(source)

            return source
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def update_all_stats(self) -> int:
        """
        更新所有数据源的统计数据

        Returns:
            更新的数据源数量
        """
        db = self._get_db()
        try:
            sources = db.query(Source).all()
            count = 0

            for source in sources:
                self.update_source_stats(source.id)
                count += 1

            return count
        finally:
            if self._owns_session:
                self._close_db()


# 全局单例
source_manage_service = SourceManageService()
