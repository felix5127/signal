# 集成测试
# 测试完整的端到端流程

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime


class TestSignalWorkflow:
    """信号工作流集成测试"""

    def test_full_signal_lifecycle(self, client: TestClient, db: Session):
        """测试信号从创建到检索的完整生命周期"""
        from app.models.signal import Signal

        # 1. 创建信号（通过API或直接数据库）
        signal = Signal(
            source="github",
            title="Test Repository",
            url="https://github.com/test/repo",
            one_liner="Test one liner",
            summary="Test summary",
            final_score=4,
            heat_score=80,
            quality_score=4,
            category="ai",
            tags="ai,test",
            status="published",
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)

        # 2. 通过API获取信号列表
        response = client.get("/api/signals")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

        # 3. 获取特定信号
        response = client.get(f"/api/signals/{signal.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == signal.id
        assert data["data"]["title"] == "Test Repository"

        # 4. 使用筛选条件查询
        response = client.get("/api/signals?min_score=4")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert all(s["final_score"] >= 4 for s in data["data"]["items"])

        # 5. 使用搜索功能
        response = client.get("/api/signals?search=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] > 0

    def test_pagination_workflow(self, client: TestClient, db: Session):
        """测试分页工作流"""
        from app.models.signal import Signal

        # 创建25个信号
        for i in range(25):
            signal = Signal(
                source="github",
                title=f"Repo {i}",
                url=f"https://github.com/test/repo{i}",
                one_liner=f"Test {i}",
                summary=f"Summary {i}",
                final_score=i % 5 + 1,
                heat_score=50 + i,
                quality_score=i % 5 + 1,
                category="ai",
                tags="test",
                status="published",
            )
            db.add(signal)

        db.commit()

        # 第一页
        response = client.get("/api/signals?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 10
        assert data["data"]["total"] >= 25

        # 第二页
        response = client.get("/api/signals?limit=10&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 10

        # 第三页
        response = client.get("/api/signals?limit=10&offset=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) >= 5  # 可能不足10个


class TestErrorHandlingWorkflow:
    """错误处理工作流测试"""

    def test_404_error_workflow(self, client: TestClient):
        """测试404错误处理流程"""
        response = client.get("/api/signals/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "message" in data["error"]

    def test_validation_error_workflow(self, client: TestClient):
        """测试验证错误处理流程"""
        response = client.get("/api/signals?limit=invalid")

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "error" in data


class TestStatsWorkflow:
    """统计工作流测试"""

    def test_stats_workflow(self, client: TestClient, db: Session):
        """测试统计数据工作流"""
        from app.models.signal import Signal

        # 创建一些测试数据
        for i in range(10):
            signal = Signal(
                source="github" if i % 2 == 0 else "huggingface",
                title=f"Repo {i}",
                url=f"https://example.com/repo{i}",
                one_liner=f"Test {i}",
                summary=f"Summary {i}",
                final_score=i % 5 + 1,
                heat_score=50 + i * 5,
                quality_score=i % 5 + 1,
                category="ai" if i % 2 == 0 else "devtools",
                tags="test",
                status="published",
            )
            db.add(signal)

        db.commit()

        # 获取统计
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        stats = data["data"]
        assert "total_signals" in stats
        assert stats["total_signals"] >= 10
        assert "by_source" in stats
        assert "by_category" in stats
        assert "average_scores" in stats


class TestHealthCheckWorkflow:
    """健康检查工作流测试"""

    def test_health_check_workflow(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert "redis" in data


class TestCachingWorkflow:
    """缓存工作流测试（需要Redis）"""

    @pytest.mark.skipif(
        True,  # 跳过，除非有Redis
        reason="需要Redis"
    )
    def test_caching_workflow(self, client: TestClient, db: Session):
        """测试缓存工作流"""
        from app.services.cache_service import smart_cache

        # 测试缓存设置和获取
        cache_key = "test_key"
        test_value = {"test": "data"}

        # 设置缓存
        result = await smart_cache.set(cache_key, test_value, ttl=60)
        assert result is True

        # 获取缓存
        cached = await smart_cache.get(cache_key)
        assert cached == test_value

        # 删除缓存
        result = await smart_cache.delete(cache_key)
        assert result is True

        # 再次获取应该返回None
        cached = await smart_cache.get(cache_key)
        assert cached is None


class TestSecurityWorkflow:
    """安全工作流测试"""

    def test_sql_injection_protection(self, client: TestClient):
        """测试SQL注入防护"""
        malicious_search = "'; DROP TABLE signals; --"

        response = client.get(f"/api/signals?search={malicious_search}")

        # 应该正常处理，不会导致SQL注入
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # 不应该返回错误或崩溃
            assert data["success"] is True

    def test_xss_protection(self, client: TestClient):
        """测试XSS防护"""
        xss_payload = "<script>alert('xss')</script>"

        response = client.get(f"/api/signals?search={xss_payload}")

        # 应该清理或拒绝输入
        assert response.status_code in [200, 400, 422]

    def test_rate_limiting(self, client: TestClient):
        """测试速率限制"""
        from app.middlewares.validation import rate_limiter

        # 测试速率限制器
        identifier = "test_user_123"
        max_requests = 5

        # 发送max_requests次请求
        for _ in range(max_requests):
            assert rate_limiter.is_allowed(identifier) is True

        # 第max_requests+1次应该被拒绝
        assert rate_limiter.is_allowed(identifier) is False

        # 测试获取剩余请求数
        remaining = rate_limiter.get_remaining_requests(identifier)
        assert remaining == 0


class TestAPIResponseFormat:
    """API响应格式测试"""

    def test_success_response_format(self, client: TestClient):
        """测试成功响应格式"""
        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()

        # 检查响应格式
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

    def test_error_response_format(self, client: TestClient):
        """测试错误响应格式"""
        response = client.get("/api/signals/99999")

        assert response.status_code == 404
        data = response.json()

        # 检查错误响应格式
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "message" in data["error"]
        assert "code" in data["error"]


class TestConcurrentRequests:
    """并发请求测试"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: TestClient):
        """测试并发请求处理"""
        import asyncio

        async def make_request():
            response = client.get("/api/signals")
            return response

        # 并发发送10个请求
        responses = await asyncio.gather(*[make_request() for _ in range(10)])

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
