"""
[INPUT]: 依赖 database, models/research
[OUTPUT]: 对外提供 SessionStore 类，管理会话历史加载
[POS]: agents/research/ 的会话存储层
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
import structlog
from typing import Optional

from app.database import SessionLocal
from app.models.research import ChatMessage

logger = structlog.get_logger()


class SessionStore:
    """
    对话历史管理

    从 ChatMessage 表加载历史消息，构建 Anthropic messages 列表。
    使用 asyncio.to_thread 避免阻塞事件循环。
    """

    async def load_history(
        self,
        project_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        加载项目的对话历史，返回 Anthropic messages 格式

        返回:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        def _sync_load():
            db = SessionLocal()
            try:
                messages = (
                    db.query(ChatMessage)
                    .filter(ChatMessage.project_id == project_id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(limit)
                    .all()
                )
                # 反转为时间正序
                messages.reverse()

                return [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
            except Exception as e:
                logger.error("session_store.load.failed", project_id=project_id, error=str(e))
                return []
            finally:
                db.close()

        return await asyncio.to_thread(_sync_load)
