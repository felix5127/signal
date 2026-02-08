# [INPUT]: 无外部依赖
# [OUTPUT]: 对外提供 CancellationToken, PipelineCancelled
# [POS]: 共享取消令牌，供 PipelineContext 和 TranscriptionService 使用
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import threading


class CancellationToken:
    """
    线程安全的取消令牌

    通过 threading.Event 实现，可在任意线程中发出取消信号。
    供 PipelineContext 和 TranscriptionService 共用。
    """

    def __init__(self):
        self._event = threading.Event()

    def cancel(self):
        """发出取消信号"""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._event.is_set()


class PipelineCancelled(Exception):
    """流水线被取消"""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        super().__init__(f"Pipeline {pipeline_id} cancelled")
