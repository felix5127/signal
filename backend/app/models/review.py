# app/models/review.py

"""
[INPUT]: 依赖 database.py (Base), resource.py (Resource)
[OUTPUT]: 对外提供 Review 模型
[POS]: 数据持久化层，人工审核记录
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    """
    人工审核记录

    记录所有人工审核操作，用于分析和优化过滤规则。
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)

    # 关联
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)

    # 审核内容
    action = Column(String(20), nullable=False)         # approve/reject/restore
    old_status = Column(String(20), nullable=False)     # 原状态
    new_status = Column(String(20), nullable=False)     # 新状态
    comment = Column(Text, nullable=True)               # 批注说明

    # 审核人
    reviewer = Column(String(100), default="admin")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联对象
    resource = relationship("Resource", backref="reviews")

    def __repr__(self):
        return f"<Review {self.id} {self.action} resource={self.resource_id}>"

    def to_dict(self):
        """转换为字典，用于 API 响应"""
        return {
            "id": self.id,
            "resource_id": self.resource_id,
            "action": self.action,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "comment": self.comment,
            "reviewer": self.reviewer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
