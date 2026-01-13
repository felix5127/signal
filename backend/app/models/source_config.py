"""
[INPUT]: 依赖 database.py (Base)
[OUTPUT]: 对外提供 SourceConfig 模型
[POS]: 数据持久化层，动态配置覆盖 config.yaml
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, JSON

from app.database import Base


# 所有支持的信号源类型
SOURCE_TYPES = [
    "hackernews",
    "github",
    "huggingface",
    "twitter",
    "arxiv",
    "producthunt",
    "blog",
    "podcast",
    "video",
]


class SourceConfig(Base):
    """
    数据源动态配置

    用于运行时覆盖 config.yaml 中的配置：
    - enabled: 是否启用该数据源
    - config_override: JSON 格式的配置覆盖

    config_override 示例：
    {
        "max_items": 10,
        "keywords": ["AI", "LLM"],
        "score_threshold": 50
    }
    """

    __tablename__ = "source_configs"

    # ========== 基础信息 ==========
    source_type = Column(String(50), primary_key=True)
    enabled = Column(Boolean, default=True, nullable=False)
    config_override = Column(JSON, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"<SourceConfig {self.source_type} {status}>"

    def to_dict(self):
        """转换为字典，用于 API 响应"""
        return {
            "source_type": self.source_type,
            "enabled": self.enabled,
            "config_override": self.config_override,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_or_create(cls, db, source_type: str):
        """获取或创建配置记录"""
        config = db.query(cls).filter(cls.source_type == source_type).first()
        if not config:
            config = cls(source_type=source_type, enabled=True)
            db.add(config)
            db.commit()
            db.refresh(config)
        return config
