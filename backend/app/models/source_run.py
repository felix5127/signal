"""
[INPUT]: 依赖 database.py (Base)
[OUTPUT]: 对外提供 SourceRun 模型
[POS]: 数据持久化层，记录每次信号源采集的结果
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index

from app.database import Base


class SourceRun(Base):
    """
    记录每次数据源采集的结果

    用于追踪采集漏斗：
    - fetched_count: 原始抓取数量
    - rule_filtered_count: 规则过滤后剩余
    - dedup_filtered_count: 去重后剩余
    - llm_filtered_count: LLM 过滤后剩余
    - saved_count: 最终存储数量

    状态说明：
    - running: 正在运行
    - success: 成功完成
    - failed: 失败
    - partial: 部分成功（有错误但仍保存了部分数据）
    """

    __tablename__ = "source_runs"

    # ========== 基础信息 ==========
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running", nullable=False)

    # ========== 采集漏斗统计 ==========
    fetched_count = Column(Integer, default=0)
    rule_filtered_count = Column(Integer, default=0)
    dedup_filtered_count = Column(Integer, default=0)
    llm_filtered_count = Column(Integer, default=0)
    saved_count = Column(Integer, default=0)

    # ========== 错误信息 ==========
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # ========== 索引优化 ==========
    __table_args__ = (
        Index("ix_source_runs_source_started", "source_type", "started_at"),
    )

    def __repr__(self):
        return f"<SourceRun {self.source_type} {self.status} at {self.started_at}>"

    def to_dict(self):
        """转换为字典，用于 API 响应"""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "funnel": {
                "fetched": self.fetched_count,
                "rule_filtered": self.rule_filtered_count,
                "dedup_filtered": self.dedup_filtered_count,
                "llm_filtered": self.llm_filtered_count,
                "saved": self.saved_count,
            },
            "error_message": self.error_message,
            "error_details": self.error_details,
        }
