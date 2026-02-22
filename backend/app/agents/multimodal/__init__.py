"""
[INPUT]: tingwu_client, video_processor 模块
[OUTPUT]: 导出多模态处理服务
[POS]: multimodal 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.multimodal.tingwu_client import TingwuClient, tingwu_client

__all__ = [
    "TingwuClient",
    "tingwu_client",
]
