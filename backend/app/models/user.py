"""
[INPUT]: 依赖 sqlalchemy, database
[OUTPUT]: 对外提供 User, UserSession 模型
[POS]: models/ 的用户认证模型
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================
# 用户模型
# ============================================================

class User(Base):
    """
    用户模型

    属性:
    - id: UUID 主键
    - email: 邮箱 (唯一)
    - username: 用户名 (唯一)
    - hashed_password: 哈希密码
    - full_name: 全名
    - avatar_url: 头像 URL
    - is_active: 是否激活
    - is_superuser: 是否超级管理员
    - email_verified: 邮箱是否验证
    - provider: OAuth 提供商 (local/github/google)
    - provider_id: OAuth 提供商用户 ID
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # OAuth 用户可能没有密码
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # OAuth 信息
    provider = Column(String(20), default="local", nullable=False)  # local/github/google
    provider_id = Column(String(255), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # 关系
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    # NOTE: research_projects 关系将在 ResearchProject.owner_id FK 完成后启用
    # research_projects = relationship("ResearchProject", back_populates="user", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("idx_users_provider", "provider", "provider_id"),
    )

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


# ============================================================
# 用户会话模型
# ============================================================

class UserSession(Base):
    """
    用户会话模型

    用于管理 JWT Refresh Token

    属性:
    - id: UUID 主键
    - user_id: 用户 ID
    - refresh_token: Refresh Token 哈希
    - user_agent: 用户代理
    - ip_address: IP 地址
    - expires_at: 过期时间
    - revoked: 是否已撤销
    """

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="sessions")

    # 索引
    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<UserSession {self.id} user={self.user_id}>"


# ============================================================
# 密码重置令牌
# ============================================================

class PasswordResetToken(Base):
    """
    密码重置令牌

    属性:
    - id: UUID 主键
    - user_id: 用户 ID
    - token_hash: 令牌哈希
    - expires_at: 过期时间
    - used: 是否已使用
    """

    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 索引
    __table_args__ = (
        Index("idx_reset_tokens_user", "user_id"),
    )

    def __repr__(self):
        return f"<PasswordResetToken {self.id}>"
