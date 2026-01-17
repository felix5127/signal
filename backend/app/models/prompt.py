# app/models/prompt.py

"""
[INPUT]: 依赖 database.py (Base)
[OUTPUT]: 对外提供 Prompt 模型
[POS]: 数据持久化层，Prompt 版本管理
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, UniqueConstraint
from app.database import Base


class Prompt(Base):
    """
    Prompt 版本管理

    用于存储和管理 LLM Prompt 的版本历史，支持 A/B 测试。
    """
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)

    # 版本信息
    name = Column(String(100), nullable=False)          # Prompt 名称
    version = Column(Integer, nullable=False)           # 版本号
    type = Column(String(50), nullable=False, index=True)  # filter/analyzer/translator

    # 内容
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)

    # 状态
    status = Column(String(20), default="draft", index=True)  # draft/active/archived

    # 效果统计（A/B 测试用）
    total_used = Column(Integer, default=0)             # 使用次数
    avg_score = Column(Float, nullable=True)            # 平均评分
    approval_rate = Column(Float, nullable=True)        # 通过率

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)

    # 唯一约束：同类型同版本只能有一个
    __table_args__ = (
        UniqueConstraint('type', 'version', name='uix_prompt_type_version'),
    )

    def __repr__(self):
        return f"<Prompt {self.name} v{self.version} ({self.status})>"

    def to_dict(self):
        """转换为字典，用于 API 响应"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "type": self.type,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "status": self.status,
            "total_used": self.total_used,
            "avg_score": self.avg_score,
            "approval_rate": self.approval_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }
