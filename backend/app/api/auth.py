"""
[INPUT]: 依赖 services/auth_service, models/user, database
[OUTPUT]: 对外提供认证 API 端点
[POS]: api/ 的认证路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import auth_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])

# OAuth2 配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ============================================================
# Pydantic 模型
# ============================================================

class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class RefreshRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_superuser: bool
    email_verified: bool
    provider: str


class AuthResponse(BaseModel):
    """认证响应"""
    user: UserResponse
    tokens: TokenResponse


# ============================================================
# 依赖注入
# ============================================================

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户

    从 Authorization 头部获取 JWT 令牌并验证
    """
    if not token:
        return None

    payload = auth_service.verify_token(token)
    if not payload:
        return None

    user = db.query(User).filter(User.id == payload.sub).first()
    if not user or not user.is_active:
        return None

    return user


async def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """要求用户已登录"""
    if not user:
        raise HTTPException(status_code=401, detail="需要登录")
    return user


async def require_superuser(
    user: User = Depends(require_user),
) -> User:
    """要求超级管理员"""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ============================================================
# API 端点
# ============================================================

@router.post("/register", response_model=AuthResponse)
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    用户注册

    创建新用户账号并返回令牌。
    """
    try:
        user = await auth_service.register(
            db=db,
            email=data.email,
            username=data.username,
            password=data.password,
            full_name=data.full_name,
        )

        tokens = auth_service.create_token_pair(user)

        return AuthResponse(
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                email_verified=user.email_verified,
                provider=user.provider,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="注册失败")


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    用户登录

    验证邮箱和密码，返回令牌。
    """
    try:
        user, tokens = await auth_service.login(
            db=db,
            email=data.email,
            password=data.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

        return AuthResponse(
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                email_verified=user.email_verified,
                provider=user.provider,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="登录失败")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    刷新令牌

    使用刷新令牌获取新的访问令牌。
    """
    try:
        _, tokens = await auth_service.refresh_tokens(
            db=db,
            refresh_token=data.refresh_token,
        )

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="刷新失败")


@router.post("/logout")
async def logout(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    用户登出

    撤销刷新令牌。
    """
    await auth_service.logout(db=db, refresh_token=data.refresh_token)
    return {"success": True, "message": "已登出"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_user),
):
    """
    获取当前用户信息
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        email_verified=user.email_verified,
        provider=user.provider,
    )


# ============================================================
# OAuth 端点 (用于 NextAuth.js)
# ============================================================

class OAuthUserInfo(BaseModel):
    """OAuth 用户信息 (由 NextAuth.js 传递)"""
    provider: str = Field(..., description="提供商: github/google")
    provider_id: str = Field(..., description="提供商用户 ID")
    email: EmailStr = Field(..., description="邮箱")
    name: Optional[str] = Field(None, description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像 URL")


@router.post("/oauth/sync", response_model=AuthResponse)
async def oauth_sync(
    data: OAuthUserInfo,
    db: Session = Depends(get_db),
):
    """
    OAuth 用户同步

    NextAuth.js 验证 OAuth 后，调用此端点同步用户数据到后端。
    如果用户不存在则创建，存在则更新。
    """
    if data.provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {data.provider}")

    try:
        # 生成用户名 (从邮箱或名称)
        username = data.name or data.email.split("@")[0]
        # 确保用户名符合规范
        username = username.replace(" ", "_").lower()[:50]

        user, tokens = await auth_service.oauth_login(
            db=db,
            provider=data.provider,
            provider_id=data.provider_id,
            email=data.email,
            username=username,
            full_name=data.name,
            avatar_url=data.avatar_url,
        )

        return AuthResponse(
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                email_verified=user.email_verified,
                provider=user.provider,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )

    except Exception as e:
        logger.error(f"OAuth sync failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth 同步失败")


@router.post("/oauth/{provider}")
async def oauth_callback(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    OAuth 回调 (直接处理模式)

    处理 OAuth 提供商的认证回调。
    支持 GitHub 和 Google OAuth。
    """
    import os
    import httpx

    if provider not in ["github", "google"]:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")

    # 获取请求体
    body = await request.json()
    code = body.get("code")
    redirect_uri = body.get("redirect_uri")

    if not code:
        raise HTTPException(status_code=400, detail="缺少 authorization code")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if provider == "github":
                # GitHub OAuth
                client_id = os.getenv("GITHUB_CLIENT_ID")
                client_secret = os.getenv("GITHUB_CLIENT_SECRET")

                if not client_id or not client_secret:
                    raise HTTPException(status_code=500, detail="GitHub OAuth 未配置")

                # 交换 access_token
                token_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
                token_data = token_resp.json()

                if "error" in token_data:
                    raise HTTPException(status_code=400, detail=token_data.get("error_description", "GitHub 授权失败"))

                access_token = token_data.get("access_token")

                # 获取用户信息
                user_resp = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                user_data = user_resp.json()

                # 获取邮箱 (可能需要额外请求)
                email = user_data.get("email")
                if not email:
                    emails_resp = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github+json",
                        },
                    )
                    emails = emails_resp.json()
                    for e in emails:
                        if e.get("primary") and e.get("verified"):
                            email = e.get("email")
                            break

                if not email:
                    raise HTTPException(status_code=400, detail="无法获取 GitHub 邮箱")

                provider_id = str(user_data.get("id"))
                username = user_data.get("login", email.split("@")[0])
                full_name = user_data.get("name")
                avatar_url = user_data.get("avatar_url")

            elif provider == "google":
                # Google OAuth
                client_id = os.getenv("GOOGLE_CLIENT_ID")
                client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

                if not client_id or not client_secret:
                    raise HTTPException(status_code=500, detail="Google OAuth 未配置")

                # 交换 access_token
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_data = token_resp.json()

                if "error" in token_data:
                    raise HTTPException(status_code=400, detail=token_data.get("error_description", "Google 授权失败"))

                access_token = token_data.get("access_token")

                # 获取用户信息
                user_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                user_data = user_resp.json()

                email = user_data.get("email")
                if not email:
                    raise HTTPException(status_code=400, detail="无法获取 Google 邮箱")

                provider_id = user_data.get("id")
                username = email.split("@")[0]
                full_name = user_data.get("name")
                avatar_url = user_data.get("picture")

            # 创建或更新用户
            user, tokens = await auth_service.oauth_login(
                db=db,
                provider=provider,
                provider_id=provider_id,
                email=email,
                username=username,
                full_name=full_name,
                avatar_url=avatar_url,
            )

            return AuthResponse(
                user=UserResponse(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    avatar_url=user.avatar_url,
                    is_active=user.is_active,
                    is_superuser=user.is_superuser,
                    email_verified=user.email_verified,
                    provider=user.provider,
                ),
                tokens=TokenResponse(
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_type=tokens.token_type,
                    expires_in=tokens.expires_in,
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth 认证失败: {str(e)}")
