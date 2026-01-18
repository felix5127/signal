"""
[INPUT]: agent 模块
[OUTPUT]: 导出 ResearchAgent
[POS]: research 包入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from app.agents.research.agent import ResearchAgent

__all__ = ["ResearchAgent"]
