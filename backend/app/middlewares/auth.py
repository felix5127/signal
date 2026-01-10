# Input: JWT配置（环境变量）, HTTP认证头
# Output: 访问令牌创建/验证, 用户认证依赖
# Position: 认证中间件，提供JWT和API密钥认证
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

# JWT认证中间件
# 提供基于JWT的API认证

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# 安全配置 - 从环境变量读取，生产环境必须设置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("JWT_SECRET_KEY environment variable must be set in production")
    # 开发环境生成随机密钥（每次重启会变化，仅用于开发）
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("Using auto-generated JWT secret key (development only)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天

security = HTTPBearer(auto_error=False)  # auto_error=False 允许可选认证


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str  # 用户ID或标识
    exp: datetime  # 过期时间


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据（通常会包含user_id等信息）
        expires_delta: 过期时间增量

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """
    验证令牌

    Args:
        token: JWT token字符串

    Returns:
        TokenPayload对象

    Raises:
        HTTPException: 如果token无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        exp: datetime = payload.get("exp")

        if user_id is None:
            raise credentials_exception

        # 检查过期时间
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise credentials_exception

        return TokenPayload(sub=user_id, exp=exp)

    except JWTError:
        raise credentials_exception


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    获取当前用户（可选认证）

    用于某些端点：如果有认证则获取用户信息，没有则返回None
    """
    if credentials is None:
        return None

    try:
        payload = verify_token(credentials.credentials)
        return payload.sub
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    获取当前用户（必须认证）

    用于需要认证的端点
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    return payload.sub


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    简化的认证依赖（同步版本）
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = verify_token(credentials.credentials)
        return payload.sub
    except HTTPException:
        raise


# API密钥认证（用于服务间调用）
class APIKeyAuth:
    """API密钥认证"""

    def __init__(self, allowed_keys: Optional[list[str]] = None):
        # 从环境变量读取允许的API密钥（逗号分隔）
        env_keys = os.getenv("API_KEYS", "")
        if env_keys:
            self.allowed_keys = [key.strip() for key in env_keys.split(",") if key.strip()]
        elif allowed_keys:
            self.allowed_keys = allowed_keys
        else:
            # 开发环境默认密钥（生产环境必须通过环境变量设置）
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("API_KEYS environment variable must be set in production")
            self.allowed_keys = ["dev-key-123"]
            logger.warning("Using default API key (development only)")

    def __call__(self, api_key: Optional[str] = None) -> bool:
        """
        验证API密钥

        Args:
            api_key: API密钥（从请求头或查询参数获取）

        Returns:
            是否有效

        Raises:
            HTTPException: 如果密钥无效
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
            )

        if api_key not in self.allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return True


# 创建API密钥认证实例
api_key_auth = APIKeyAuth()
