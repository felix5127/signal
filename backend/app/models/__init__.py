"""
[INPUT]: 各子模块的 ORM 模型
[OUTPUT]: 统一导出所有数据模型
[POS]: models 包入口，聚合所有 ORM 模型供外部导入
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.models.signal import Signal
from app.models.digest import DailyDigest, WeeklyDigest
from app.models.resource import Resource
from app.models.newsletter import Newsletter
from app.models.task import TaskStatus
from app.models.source_run import SourceRun
from app.models.source_config import SourceConfig, SOURCE_TYPES
from app.models.research import (
    ResearchProject,
    ResearchSource,
    SourceEmbedding,
    ResearchOutput,
    ChatSession,
    AgentTask,
)

__all__ = [
    # v1.0 旧模型（保留兼容）
    "Signal",
    "DailyDigest",
    "WeeklyDigest",
    # v2.0 新模型
    "Resource",
    "Newsletter",
    # 任务状态模型
    "TaskStatus",
    # 信号源管理模型
    "SourceRun",
    "SourceConfig",
    "SOURCE_TYPES",
    # v3.0 研究助手模型
    "ResearchProject",
    "ResearchSource",
    "SourceEmbedding",
    "ResearchOutput",
    "ChatSession",
    "AgentTask",
]
