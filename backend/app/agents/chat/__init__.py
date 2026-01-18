"""
[INPUT]: research/agent 中的 ChatAgent
[OUTPUT]: 导出 ChatAgent
[POS]: chat 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.research.agent import ChatAgent

__all__ = ["ChatAgent"]
