"""
[INPUT]: kimi_client 模块
[OUTPUT]: 导出 KimiClient
[POS]: llm 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.llm.kimi_client import KimiClient, kimi_client

__all__ = ["KimiClient", "kimi_client"]
