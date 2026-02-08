# [INPUT]: 依赖 tasks/pipeline_context.py (PipelineContext), utils/cancellation.py (PipelineCancelled)
# [OUTPUT]: 对外提供 PipelineOrchestrator, orchestrator (全局单例), PipelineAlreadyRunning
# [POS]: 流水线编排器，防重叠执行，取消/状态查询
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import threading
from datetime import datetime
from typing import Optional

import structlog

from app.tasks.pipeline_context import PipelineContext
from app.utils.cancellation import PipelineCancelled

logger = structlog.get_logger("orchestrator")


class PipelineAlreadyRunning(Exception):
    """流水线已在运行中"""

    def __init__(self, pipeline_type: str):
        self.pipeline_type = pipeline_type
        super().__init__(f"Pipeline '{pipeline_type}' is already running")


class PipelineOrchestrator:
    """
    流水线编排器

    职责:
    1. 创建并管理 PipelineContext
    2. 防止重叠执行 (同类型同时只能运行一个)
    3. 提供取消能力
    4. 状态查询 (运行中 + 历史)
    """

    def __init__(self):
        self._running: dict[str, PipelineContext] = {}  # type -> context
        self._lock = threading.Lock()
        self._history: list[dict] = []  # 最近完成的流水线记录
        self._max_history = 20

    def create_context(self, pipeline_type: str) -> PipelineContext:
        """
        创建流水线上下文并注册为运行中

        Args:
            pipeline_type: 流水线类型 (blog/twitter/podcast/video)

        Returns:
            PipelineContext 实例

        Raises:
            PipelineAlreadyRunning: 同类型流水线已在运行
        """
        with self._lock:
            if pipeline_type in self._running:
                existing = self._running[pipeline_type]
                logger.warning(
                    "orchestrator.already_running",
                    pipeline_type=pipeline_type,
                    existing_id=existing.pipeline_id,
                    started_at=existing.started_at.isoformat() if existing.started_at else None,
                )
                raise PipelineAlreadyRunning(pipeline_type)

            ctx = PipelineContext(
                pipeline_type=pipeline_type,
                status="running",
                current_step="init",
                started_at=datetime.now(),
            )
            self._running[pipeline_type] = ctx

            logger.info(
                "orchestrator.registered",
                pipeline_type=pipeline_type,
                pipeline_id=ctx.pipeline_id,
            )

            return ctx

    def finish(self, pipeline_type: str):
        """
        标记流水线完成并从运行列表移除

        Args:
            pipeline_type: 流水线类型
        """
        with self._lock:
            ctx = self._running.pop(pipeline_type, None)
            if ctx:
                # 保存到历史记录
                self._history.append(ctx.to_dict())
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

                logger.info(
                    "orchestrator.finished",
                    pipeline_type=pipeline_type,
                    pipeline_id=ctx.pipeline_id,
                    status=ctx.status,
                    duration_ms=round(ctx.duration_ms, 1),
                )

    def cancel(self, pipeline_type: str) -> bool:
        """
        取消运行中的流水线

        Args:
            pipeline_type: 流水线类型

        Returns:
            True 如果成功发出取消信号，False 如果没有运行中的流水线
        """
        ctx = self._running.get(pipeline_type)
        if ctx:
            ctx.cancellation_token.cancel()
            logger.info(
                "orchestrator.cancel_requested",
                pipeline_type=pipeline_type,
                pipeline_id=ctx.pipeline_id,
            )
            return True
        return False

    def is_running(self, pipeline_type: str) -> bool:
        """检查指定类型是否正在运行"""
        return pipeline_type in self._running

    def get_status(self, pipeline_type: str) -> Optional[dict]:
        """获取指定类型的运行状态"""
        ctx = self._running.get(pipeline_type)
        return ctx.to_dict() if ctx else None

    def get_all_status(self) -> list[dict]:
        """获取所有运行中流水线的状态"""
        return [ctx.to_dict() for ctx in self._running.values()]

    def get_history(self) -> list[dict]:
        """获取最近完成的流水线记录"""
        return list(reversed(self._history))


# 全局单例
orchestrator = PipelineOrchestrator()
