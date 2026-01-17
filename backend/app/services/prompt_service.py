"""
[INPUT]: 依赖 database.py (SessionLocal), models/prompt.py (Prompt)
[OUTPUT]: 对外提供 PromptService 类
[POS]: 服务层，Prompt 版本管理业务逻辑
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.prompt import Prompt


class PromptService:
    """
    Prompt 版本管理服务

    支持：
    - 获取活跃 Prompt
    - 创建新版本
    - 激活/归档版本
    - 更新使用统计
    """

    def __init__(self, db: Optional[Session] = None):
        """
        初始化服务

        Args:
            db: 数据库 Session（可选，不传则使用全局 Session）
        """
        self._db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        """获取数据库 Session"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _close_db(self):
        """关闭自己创建的 Session"""
        if self._owns_session and self._db is not None:
            self._db.close()
            self._db = None

    def get_active_prompt(self, prompt_type: str) -> Optional[Prompt]:
        """
        获取指定类型的活跃 Prompt

        Args:
            prompt_type: Prompt 类型 (filter/analyzer/translator)

        Returns:
            活跃的 Prompt 对象，不存在则返回 None
        """
        db = self._get_db()
        try:
            return db.query(Prompt).filter(
                Prompt.type == prompt_type,
                Prompt.status == "active"
            ).first()
        finally:
            if self._owns_session:
                self._close_db()

    def get_prompts_by_type(self, prompt_type: str) -> List[Prompt]:
        """
        获取指定类型的所有 Prompt

        Args:
            prompt_type: Prompt 类型

        Returns:
            Prompt 列表，按版本号降序
        """
        db = self._get_db()
        try:
            return db.query(Prompt).filter(
                Prompt.type == prompt_type
            ).order_by(Prompt.version.desc()).all()
        finally:
            if self._owns_session:
                self._close_db()

    def get_all_prompts(self) -> List[Prompt]:
        """
        获取所有 Prompt

        Returns:
            Prompt 列表，按类型和版本号排序
        """
        db = self._get_db()
        try:
            return db.query(Prompt).order_by(
                Prompt.type,
                Prompt.version.desc()
            ).all()
        finally:
            if self._owns_session:
                self._close_db()

    def get_prompt_by_id(self, prompt_id: int) -> Optional[Prompt]:
        """
        根据 ID 获取 Prompt

        Args:
            prompt_id: Prompt ID

        Returns:
            Prompt 对象
        """
        db = self._get_db()
        try:
            return db.query(Prompt).filter(Prompt.id == prompt_id).first()
        finally:
            if self._owns_session:
                self._close_db()

    def create_prompt(
        self,
        name: str,
        prompt_type: str,
        system_prompt: str,
        user_prompt_template: str,
    ) -> Prompt:
        """
        创建新版本 Prompt

        自动计算版本号（当前最大版本 + 1）

        Args:
            name: Prompt 名称
            prompt_type: Prompt 类型
            system_prompt: 系统 Prompt
            user_prompt_template: 用户 Prompt 模板

        Returns:
            新创建的 Prompt 对象
        """
        db = self._get_db()
        try:
            # 计算新版本号
            max_version = db.query(Prompt).filter(
                Prompt.type == prompt_type
            ).order_by(Prompt.version.desc()).first()

            new_version = (max_version.version + 1) if max_version else 1

            prompt = Prompt(
                name=name,
                version=new_version,
                type=prompt_type,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                status="draft",
                created_at=datetime.utcnow(),
            )

            db.add(prompt)
            db.commit()
            db.refresh(prompt)

            return prompt
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def activate_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """
        激活指定 Prompt，同时将同类型其他 active 的归档

        Args:
            prompt_id: 要激活的 Prompt ID

        Returns:
            激活后的 Prompt 对象
        """
        db = self._get_db()
        try:
            prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
            if not prompt:
                return None

            # 将同类型的其他 active Prompt 归档
            db.query(Prompt).filter(
                Prompt.type == prompt.type,
                Prompt.status == "active"
            ).update({"status": "archived"})

            # 激活当前 Prompt
            prompt.status = "active"
            prompt.activated_at = datetime.utcnow()

            db.commit()
            db.refresh(prompt)

            return prompt
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()

    def update_stats(
        self,
        prompt_id: int,
        score: Optional[float] = None,
        passed: Optional[bool] = None,
    ):
        """
        更新 Prompt 使用统计

        Args:
            prompt_id: Prompt ID
            score: 本次评分（用于计算平均分）
            passed: 是否通过（用于计算通过率）
        """
        db = self._get_db()
        try:
            prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
            if not prompt:
                return

            # 更新使用次数
            prompt.total_used = (prompt.total_used or 0) + 1

            # 更新平均分
            if score is not None:
                old_avg = prompt.avg_score or 0
                old_count = prompt.total_used - 1
                prompt.avg_score = (old_avg * old_count + score) / prompt.total_used

            # 更新通过率
            if passed is not None:
                old_rate = prompt.approval_rate or 0
                old_count = prompt.total_used - 1
                approved_count = old_rate * old_count + (1 if passed else 0)
                prompt.approval_rate = approved_count / prompt.total_used

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if self._owns_session:
                self._close_db()


# 全局单例
prompt_service = PromptService()
