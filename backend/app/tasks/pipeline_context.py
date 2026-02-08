# [INPUT]: 依赖 utils/cancellation.py (CancellationToken, PipelineCancelled)
# [OUTPUT]: 对外提供 PipelineContext, StepLog
# [POS]: 流水线运行上下文，步骤级进度追踪，取消信号支持
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import structlog

from app.utils.cancellation import CancellationToken, PipelineCancelled

logger = structlog.get_logger("pipeline_context")


# ============================================================
# StepLog — 步骤日志
# ============================================================

@dataclass
class StepLog:
    """流水线步骤日志"""
    step: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    items_in: int = 0
    items_out: int = 0
    error: Optional[str] = None

    def finish(self, items_out: int = 0, error: Optional[str] = None):
        """标记步骤完成"""
        self.finished_at = datetime.now()
        self.items_out = items_out
        self.error = error

    @property
    def duration_ms(self) -> float:
        """步骤耗时 (毫秒)"""
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "step": self.step,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": round(self.duration_ms, 1),
            "items_in": self.items_in,
            "items_out": self.items_out,
            "error": self.error,
        }


# ============================================================
# PipelineContext — 流水线运行上下文
# ============================================================

@dataclass
class PipelineContext:
    """
    流水线运行上下文

    职责:
    1. 步骤级进度追踪
    2. CancellationToken 支持 (优雅取消)
    3. 结构化日志绑定 (自动附加 pipeline_id)
    4. 状态序列化 (to_dict / to_json)
    """
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_type: str = ""                # article/twitter/podcast/video
    status: str = "pending"                # pending/running/cancelled/completed/failed
    current_step: str = "init"             # 当前步骤名
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    steps_log: list[StepLog] = field(default_factory=list)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    error_message: Optional[str] = None

    def start(self):
        """标记流水线开始"""
        self.status = "running"
        self.started_at = datetime.now()
        logger.info(
            "pipeline.started",
            pipeline_id=self.pipeline_id,
            pipeline_type=self.pipeline_type,
        )

    def check_cancelled(self):
        """
        在步骤间调用，支持优雅取消

        Raises:
            PipelineCancelled: 如果收到取消信号
        """
        if self.cancellation_token.is_cancelled:
            self.status = "cancelled"
            self.finished_at = datetime.now()
            logger.info(
                "pipeline.cancelled",
                pipeline_id=self.pipeline_id,
                pipeline_type=self.pipeline_type,
                current_step=self.current_step,
            )
            raise PipelineCancelled(self.pipeline_id)

    def advance_step(self, step_name: str, items_in: int = 0):
        """
        推进到下一步骤

        Args:
            step_name: 步骤名称 (scrape/dedupe/extract/filter/analyze/translate/save)
            items_in: 输入项数
        """
        # 完成上一个步骤
        if self.steps_log:
            current = self.steps_log[-1]
            if current.finished_at is None:
                current.finish()

        # 创建新步骤
        step_log = StepLog(
            step=step_name,
            started_at=datetime.now(),
            items_in=items_in,
        )
        self.steps_log.append(step_log)
        self.current_step = step_name

        logger.info(
            "pipeline.step.started",
            pipeline_id=self.pipeline_id,
            pipeline_type=self.pipeline_type,
            step=step_name,
            items_in=items_in,
        )

    def finish_step(self, items_out: int = 0, error: Optional[str] = None):
        """完成当前步骤"""
        if self.steps_log:
            current = self.steps_log[-1]
            current.finish(items_out=items_out, error=error)

            logger.info(
                "pipeline.step.completed",
                pipeline_id=self.pipeline_id,
                step=current.step,
                items_in=current.items_in,
                items_out=items_out,
                duration_ms=round(current.duration_ms, 1),
                error=error,
            )

    def complete(self):
        """标记流水线完成"""
        self.status = "completed"
        self.finished_at = datetime.now()
        self.finish_step()  # 完成最后一步
        logger.info(
            "pipeline.completed",
            pipeline_id=self.pipeline_id,
            pipeline_type=self.pipeline_type,
            total_items=self.total_items,
            processed_items=self.processed_items,
            failed_items=self.failed_items,
            duration_ms=round(self.duration_ms, 1),
        )

    def fail(self, error: str):
        """标记流水线失败"""
        self.status = "failed"
        self.error_message = error
        self.finished_at = datetime.now()
        self.finish_step(error=error)
        logger.error(
            "pipeline.failed",
            pipeline_id=self.pipeline_id,
            pipeline_type=self.pipeline_type,
            error=error,
            current_step=self.current_step,
        )

    @property
    def duration_ms(self) -> float:
        """流水线总耗时 (毫秒)"""
        if self.started_at:
            end = self.finished_at or datetime.now()
            return (end - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def progress(self) -> float:
        """进度百分比 (0-100)"""
        if self.total_items <= 0:
            return 0.0
        return min(100.0, (self.processed_items / self.total_items) * 100)

    def to_dict(self) -> dict:
        """序列化为字典 (用于 API 响应)"""
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_type": self.pipeline_type,
            "status": self.status,
            "current_step": self.current_step,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "progress": round(self.progress, 1),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error_message,
            "steps": [s.to_dict() for s in self.steps_log],
        }

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
