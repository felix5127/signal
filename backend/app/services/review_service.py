"""
[INPUT]: 依赖 database.py (SessionLocal), models/resource.py (Resource), models/review.py (Review)
[OUTPUT]: 对外提供 ReviewService 类
[POS]: 服务层，内容审核业务逻辑
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.resource import Resource
from app.models.review import Review


class ReviewService:
    """
    内容审核服务

    支持：
    - 获取待审核列表
    - 执行审核操作
    - 批量审核
    - 审核统计
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

    def get_review_list(
        self,
        status: Optional[str] = None,
        source_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        获取待审核列表

        Args:
            status: 状态筛选 (approved/rejected/all)
            source_id: 来源筛选
            date_from: 开始日期
            date_to: 结束日期
            page: 页码
            page_size: 每页数量

        Returns:
            分页结果 {"items": [...], "total": N, "page": N, "page_size": N}
        """
        db = self._get_db()
        try:
            query = db.query(Resource)

            # 状态筛选
            if status and status != "all":
                query = query.filter(Resource.status == status)
            else:
                # 默认只查询需要审核的状态
                query = query.filter(Resource.status.in_(["approved", "rejected"]))

            # 来源筛选
            if source_id:
                query = query.filter(Resource.source_id == source_id)

            # 日期筛选
            if date_from:
                query = query.filter(Resource.created_at >= date_from)
            if date_to:
                query = query.filter(Resource.created_at <= date_to)

            # 总数
            total = query.count()

            # 分页
            offset = (page - 1) * page_size
            items = query.order_by(desc(Resource.created_at)).offset(offset).limit(page_size).all()

            return {
                "items": [self._resource_to_review_item(r) for r in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        finally:
            if self._owns_session:
                self._close_db()

    def _resource_to_review_item(self, resource: Resource) -> Dict[str, Any]:
        """将 Resource 转换为审核列表项"""
        return {
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "source_name": resource.source_name,
            "status": resource.status,
            "llm_score": resource.llm_score,
            "llm_reason": resource.llm_reason,
            "language": resource.language,
            "created_at": resource.created_at.isoformat() if resource.created_at else None,
        }

    def review_action(
        self,
        resource_id: int,
        action: str,
        comment: Optional[str] = None,
        reviewer: str = "admin",
    ) -> Optional[Resource]:
        """
        执行审核操作

        Args:
            resource_id: 资源 ID
            action: 操作 (publish/reject/restore)
            comment: 批注说明
            reviewer: 审核人

        Returns:
            更新后的 Resource 对象
        """
        db = self._get_db()
        try:
            resource = db.query(Resource).filter(Resource.id == resource_id).first()
            if not resource:
                return None

            old_status = resource.status

            # 确定新状态
            if action == "publish":
                new_status = "published"
            elif action == "reject":
                new_status = "rejected"
            elif action == "restore":
                new_status = "published"
            else:
                return None

            # 更新资源状态
            resource.status = new_status
            resource.review_status = action
            resource.review_comment = comment
            resource.reviewed_at = datetime.utcnow()
            resource.reviewed_by = reviewer

            # 创建审核记录
            review = Review(
                resource_id=resource_id,
                action=action,
                old_status=old_status,
                new_status=new_status,
                comment=comment,
                reviewer=reviewer,
            )
            db.add(review)

            db.commit()
            db.refresh(resource)

            return resource
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def batch_review(
        self,
        resource_ids: List[int],
        action: str,
        comment: Optional[str] = None,
        reviewer: str = "admin",
    ) -> Dict[str, Any]:
        """
        批量审核

        Args:
            resource_ids: 资源 ID 列表
            action: 操作
            comment: 批注
            reviewer: 审核人

        Returns:
            {"success": N, "failed": N}
        """
        success = 0
        failed = 0

        for resource_id in resource_ids:
            try:
                result = self.review_action(resource_id, action, comment, reviewer)
                if result:
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {"success": success, "failed": failed}

    def get_review_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取审核统计

        Args:
            date_from: 开始日期
            date_to: 结束日期

        Returns:
            统计数据
        """
        db = self._get_db()
        try:
            # 基础查询
            query = db.query(Resource)

            if date_from:
                query = query.filter(Resource.created_at >= date_from)
            if date_to:
                query = query.filter(Resource.created_at <= date_to)

            # 按状态统计
            status_stats = query.with_entities(
                Resource.status,
                func.count(Resource.id)
            ).group_by(Resource.status).all()

            stats = {s: c for s, c in status_stats}

            # 人工改判数
            overturned_query = db.query(Review).filter(Review.action == "restore")
            if date_from:
                overturned_query = overturned_query.filter(Review.created_at >= date_from)
            if date_to:
                overturned_query = overturned_query.filter(Review.created_at <= date_to)

            total_overturned = overturned_query.count()

            # 按来源统计
            source_stats = query.with_entities(
                Resource.source_id,
                Resource.source_name,
                func.count(Resource.id)
            ).group_by(Resource.source_id, Resource.source_name).all()

            return {
                "total_pending": stats.get("pending", 0),
                "total_approved": stats.get("approved", 0),
                "total_rejected": stats.get("rejected", 0),
                "total_published": stats.get("published", 0),
                "total_overturned": total_overturned,
                "by_source": [
                    {"source_id": s[0], "source_name": s[1], "count": s[2]}
                    for s in source_stats if s[0] is not None
                ],
            }
        finally:
            if self._owns_session:
                self._close_db()


# 全局单例
review_service = ReviewService()
