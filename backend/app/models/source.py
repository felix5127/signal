# app/models/source.py

"""
[INPUT]: 依赖 database.py (Base)
[OUTPUT]: 对外提供 Source 模型
[POS]: 数据持久化层，数据源管理（区别于 source_config 的运行时配置）
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, Index
from app.database import Base


class Source(Base):
    """
    数据源配置

    管理 RSS 数据源信息，包括白名单设置和统计数据。
    与 SourceConfig 的区别：
    - Source: 数据源元信息（名称、URL、白名单、统计）
    - SourceConfig: 运行时配置覆盖（采集参数）
    """
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    # 基础信息
    name = Column(String(200), nullable=False)          # 数据源名称
    type = Column(String(50), nullable=False, index=True)  # blog/twitter/podcast/video
    url = Column(String(500), nullable=False, unique=True)  # RSS URL

    # 配置
    enabled = Column(Boolean, default=True, index=True)  # 是否启用
    is_whitelist = Column(Boolean, default=False, index=True)  # 是否白名单

    # 统计（定期更新）
    total_collected = Column(Integer, default=0)        # 总采集数
    total_approved = Column(Integer, default=0)         # LLM 通过数
    total_rejected = Column(Integer, default=0)         # LLM 拒绝数
    total_published = Column(Integer, default=0)        # 已发布数
    total_review_overturned = Column(Integer, default=0)  # 人工改判数
    avg_llm_score = Column(Float, default=0.0)          # 平均 LLM 评分

    # 状态
    last_collected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 复合索引
    __table_args__ = (
        Index("idx_sources_type_enabled", "type", "enabled"),
        Index("idx_sources_whitelist", "is_whitelist"),
    )

    def __repr__(self):
        status = "whitelist" if self.is_whitelist else ("enabled" if self.enabled else "disabled")
        return f"<Source {self.name} ({self.type}) {status}>"

    def to_dict(self):
        """转换为字典，用于 API 响应"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "enabled": self.enabled,
            "is_whitelist": self.is_whitelist,
            "stats": {
                "total_collected": self.total_collected,
                "total_approved": self.total_approved,
                "total_rejected": self.total_rejected,
                "total_published": self.total_published,
                "total_review_overturned": self.total_review_overturned,
                "avg_llm_score": self.avg_llm_score,
                "approval_rate": (
                    self.total_approved / self.total_collected
                    if self.total_collected > 0 else 0.0
                ),
            },
            "last_collected_at": self.last_collected_at.isoformat() if self.last_collected_at else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
