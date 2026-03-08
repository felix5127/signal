"""
[INPUT]: 依赖 models/user, jose, passlib, secrets
[OUTPUT]: 对外提供认证服务 (JWT, 密码哈希)
[POS]: services/ 的认证服务，被 api/auth.py 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User, UserSession, PasswordResetToken

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("JWT_SECRET_KEY 环境变量未设置，请在 .env 中配置")
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("JWT_SECRET_KEY 未设置，已自动生成临时密钥（仅限开发环境）")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# 类型定义
# ============================================================

@dataclass
class TokenPair:
    """JWT 令牌对"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


@dataclass
class TokenPayload:
    """JWT 载荷"""
    sub: str  # user_id
    email: str
    username: str
    is_superuser: bool
    exp: datetime
    type: str  # access/refresh


# ============================================================
# 认证服务
# ============================================================

class AuthService:
    """
    认证服务

    功能:
    - 密码哈希和验证
    - JWT 令牌生成和验证
    - 用户注册和登录
    - 会话管理
    - 密码重置

    使用示例:
    ```python
    service = AuthService()

    # 注册
    user = await service.register(db, email="user@example.com", ...)

    # 登录
    tokens = await service.login(db, email="user@example.com", password="...")

    # 验证令牌
    payload = await service.verify_token(token)
    ```
    """

    # ============================================================
    # 密码处理
    # ============================================================

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    # ============================================================
    # JWT 处理
    # ============================================================

    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "exp": expires,
            "type": "access",
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """创建刷新令牌"""
        expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(user.id),
            "exp": expires,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),  # 唯一标识
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """
        验证令牌

        Args:
            token: JWT 令牌
            token_type: 期望的令牌类型

        Returns:
            令牌载荷或 None
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None

            return TokenPayload(
                sub=payload["sub"],
                email=payload.get("email", ""),
                username=payload.get("username", ""),
                is_superuser=payload.get("is_superuser", False),
                exp=datetime.fromtimestamp(payload["exp"]),
                type=payload["type"],
            )

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    def create_token_pair(self, user: User) -> TokenPair:
        """创建令牌对 (access + refresh)"""
        return TokenPair(
            access_token=self.create_access_token(user),
            refresh_token=self.create_refresh_token(user),
        )

    # ============================================================
    # 用户注册
    # ============================================================

    async def register(
        self,
        db: Session,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """
        用户注册

        Args:
            db: 数据库会话
            email: 邮箱
            username: 用户名
            password: 密码
            full_name: 全名

        Returns:
            新用户

        Raises:
            ValueError: 邮箱或用户名已存在
        """
        # 检查邮箱是否存在
        if db.query(User).filter(User.email == email).first():
            raise ValueError("邮箱已被注册")

        # 检查用户名是否存在
        if db.query(User).filter(User.username == username).first():
            raise ValueError("用户名已被使用")

        # 创建用户
        user = User(
            email=email,
            username=username,
            hashed_password=self.hash_password(password),
            full_name=full_name,
            provider="local",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User registered: {user.email}")
        return user

    # ============================================================
    # 用户登录
    # ============================================================

    async def login(
        self,
        db: Session,
        email: str,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[User, TokenPair]:
        """
        用户登录

        Args:
            db: 数据库会话
            email: 邮箱
            password: 密码
            user_agent: 用户代理
            ip_address: IP 地址

        Returns:
            (用户, 令牌对)

        Raises:
            ValueError: 认证失败
        """
        # 查找用户
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱或密码错误")

        # 检查密码
        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            raise ValueError("邮箱或密码错误")

        # 检查账号状态
        if not user.is_active:
            raise ValueError("账号已被禁用")

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()

        # 创建令牌
        tokens = self.create_token_pair(user)

        # 保存会话
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=self._hash_token(tokens.refresh_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(session)
        db.commit()

        logger.info(f"User logged in: {user.email}")
        return user, tokens

    # ============================================================
    # 令牌刷新
    # ============================================================

    async def refresh_tokens(
        self,
        db: Session,
        refresh_token: str,
    ) -> Tuple[User, TokenPair]:
        """
        刷新令牌

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            (用户, 新令牌对)

        Raises:
            ValueError: 令牌无效
        """
        # 验证令牌
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise ValueError("刷新令牌无效")

        # 查找用户
        user = db.query(User).filter(User.id == payload.sub).first()
        if not user or not user.is_active:
            raise ValueError("用户不存在或已禁用")

        # 验证会话
        token_hash = self._hash_token(refresh_token)
        session = db.query(UserSession).filter(
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked == False,
        ).first()

        if not session:
            raise ValueError("会话已失效")

        # 撤销旧会话
        session.revoked = True

        # 创建新令牌
        tokens = self.create_token_pair(user)

        # 创建新会话
        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=self._hash_token(tokens.refresh_token),
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(new_session)
        db.commit()

        return user, tokens

    # ============================================================
    # 登出
    # ============================================================

    async def logout(
        self,
        db: Session,
        refresh_token: str,
    ) -> bool:
        """
        用户登出

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            是否成功
        """
        token_hash = self._hash_token(refresh_token)
        session = db.query(UserSession).filter(
            UserSession.refresh_token_hash == token_hash,
        ).first()

        if session:
            session.revoked = True
            db.commit()
            logger.info(f"User logged out: session {session.id}")
            return True

        return False

    # ============================================================
    # OAuth 登录
    # ============================================================

    async def oauth_login(
        self,
        db: Session,
        provider: str,
        provider_id: str,
        email: str,
        username: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Tuple[User, TokenPair]:
        """
        OAuth 登录/注册

        Args:
            db: 数据库会话
            provider: OAuth 提供商
            provider_id: 提供商用户 ID
            email: 邮箱
            username: 用户名
            full_name: 全名
            avatar_url: 头像 URL

        Returns:
            (用户, 令牌对)
        """
        # 查找现有用户
        user = db.query(User).filter(
            User.provider == provider,
            User.provider_id == provider_id,
        ).first()

        if not user:
            # 检查邮箱是否已存在
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                # 关联现有账号
                existing_user.provider = provider
                existing_user.provider_id = provider_id
                existing_user.avatar_url = avatar_url or existing_user.avatar_url
                user = existing_user
            else:
                # 创建新用户
                # 确保用户名唯一
                base_username = username
                counter = 1
                while db.query(User).filter(User.username == username).first():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    provider=provider,
                    provider_id=provider_id,
                    email_verified=True,  # OAuth 邮箱已验证
                )
                db.add(user)

        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        tokens = self.create_token_pair(user)

        logger.info(f"OAuth user logged in: {user.email} ({provider})")
        return user, tokens

    # ============================================================
    # 工具方法
    # ============================================================

    def _hash_token(self, token: str) -> str:
        """哈希令牌"""
        return hashlib.sha256(token.encode()).hexdigest()


# ============================================================
# 单例
# ============================================================

auth_service = AuthService()
