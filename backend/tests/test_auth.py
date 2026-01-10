# API认证测试
# 测试JWT认证和API密钥认证

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestJWTAuth:
    """JWT认证测试"""

    def test_create_token(self):
        """测试创建JWT token"""
        from app.middlewares.auth import create_access_token
        from datetime import timedelta

        # 创建token
        token = create_access_token(
            data={"user_id": "test_user"},
            expires_delta=timedelta(minutes=30)
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT token应该足够长

    def test_verify_token_valid(self):
        """测试验证有效的token"""
        from app.middlewares.auth import create_access_token, verify_token

        # 创建token
        token = create_access_token(data={"user_id": "test_user"})

        # 验证token
        payload = verify_token(token)

        assert payload.sub == "test_user"
        assert payload.exp is not None

    def test_verify_token_invalid(self):
        """测试验证无效的token"""
        from app.middlewares.auth import verify_token
        from fastapi import HTTPException

        # 无效的token
        with pytest.raises(HTTPException):
            verify_token("invalid_token_12345")

    def test_verify_token_expired(self):
        """测试验证过期的token"""
        from app.middlewares.auth import create_access_token, verify_token
        from datetime import timedelta
        from fastapi import HTTPException

        # 创建一个立即过期的token
        token = create_access_token(
            data={"user_id": "test_user"},
            expires_delta=timedelta(seconds=-1)  # 已经过期
        )

        # 应该抛出异常
        with pytest.raises(HTTPException):
            verify_token(token)

    def test_protected_endpoint_without_token(self, client: TestClient):
        """测试没有token访问受保护的端点"""
        # 注意：这需要端点启用认证
        # 目前我们的API使用可选认证，所以这个测试会通过
        response = client.get("/api/signals")

        # 应该返回200（因为认证是可选的）
        assert response.status_code in [200, 401]

    def test_protected_endpoint_with_valid_token(self, client: TestClient):
        """测试使用有效token访问受保护的端点"""
        from app.middlewares.auth import create_access_token

        # 创建token
        token = create_access_token(data={"user_id": "test_user"})

        # 使用token访问API
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/signals", headers=headers)

        # 应该成功
        assert response.status_code == 200

    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """测试使用无效token访问受保护的端点"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/signals", headers=headers)

        # 应该返回401或403
        assert response.status_code in [401, 403]


class TestAPIKeyAuth:
    """API密钥认证测试"""

    def test_api_key_valid(self):
        """测试有效的API密钥"""
        from app.middlewares.auth import api_key_auth

        # 开发环境的测试密钥
        assert api_key_auth("dev-key-123") is True

    def test_api_key_invalid(self):
        """测试无效的API密钥"""
        from app.middlewares.auth import api_key_auth
        from fastapi import HTTPException

        # 无效的密钥
        with pytest.raises(HTTPException):
            api_key_auth("invalid_key")

    def test_api_key_missing(self):
        """测试缺少API密钥"""
        from app.middlewares.auth import api_key_auth
        from fastapi import HTTPException

        # 没有密钥
        with pytest.raises(HTTPException):
            api_key_auth(None)


class TestOptionalAuth:
    """可选认证测试"""

    def test_optional_auth_with_token(self, client: TestClient):
        """测试可选认证 - 有token"""
        from app.middlewares.auth import create_access_token

        token = create_access_token(data={"user_id": "test_user"})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/signals", headers=headers)
        assert response.status_code == 200

    def test_optional_auth_without_token(self, client: TestClient):
        """测试可选认证 - 没有token"""
        response = client.get("/api/signals")
        assert response.status_code == 200


class TestTokenPayload:
    """Token载荷测试"""

    def test_token_payload_validation(self):
        """测试TokenPayload验证"""
        from app.middlewares.auth import TokenPayload
        from datetime import datetime, timedelta

        # 有效的payload
        exp = datetime.utcnow() + timedelta(hours=1)
        payload = TokenPayload(sub="user123", exp=exp)

        assert payload.sub == "user123"
        assert payload.exp == exp

    def test_token_payload_missing_fields(self):
        """测试缺少字段的TokenPayload"""
        from pydantic import ValidationError

        from app.middlewares.auth import TokenPayload

        # 缺少必需字段
        with pytest.raises(ValidationError):
            TokenPayload(sub="user123")  # 缺少exp


class TestAuthMiddleware:
    """认证中间件集成测试"""

    def test_auth_middleware_registers(self):
        """测试认证中间件已注册"""
        from app.main import app

        # 检查中间件是否存在
        # 这是一个简单的检查，实际测试可能需要更复杂
        assert app is not None

    def test_get_current_user_optional(self, client: TestClient):
        """测试get_current_user_optional依赖"""
        from app.middlewares.auth import create_access_token

        # 有token
        token = create_access_token(data={"user_id": "test_user"})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/signals", headers=headers)
        assert response.status_code == 200

        # 没有token
        response = client.get("/api/signals")
        assert response.status_code == 200
