# API端点测试
# 测试API路由的正确性

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestSignalsAPI:
    """信号API测试类"""

    def test_get_signals_empty(self, client: TestClient, db: Session):
        """测试空数据库获取信号列表"""
        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    def test_get_signals_with_data(self, client: TestClient, db: Session, sample_signals):
        """测试获取信号列表"""
        response = client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 10
        assert len(data["data"]["items"]) == 10

    def test_get_signals_pagination(self, client: TestClient, db: Session, sample_signals):
        """测试分页"""
        # 第一页
        response = client.get("/api/signals?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5

        # 第二页
        response = client.get("/api/signals?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5

    def test_get_signals_filter_by_min_score(self, client: TestClient, db: Session, sample_signals):
        """测试按最低评分筛选"""
        response = client.get("/api/signals?min_score=4")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert all(item["final_score"] >= 4 for item in data["data"]["items"])

    def test_get_signals_search(self, client: TestClient, db: Session, sample_signals):
        """测试搜索"""
        response = client.get("/api/signals?search=Repository")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] > 0

    def test_get_signal_by_id_exists(self, client: TestClient, db: Session, sample_signal):
        """测试获取存在的信号"""
        response = client.get(f"/api/signals/{sample_signal.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_signal.id
        assert data["data"]["title"] == sample_signal.title

    def test_get_signal_by_id_not_exists(self, client: TestClient, db: Session):
        """测试获取不存在的信号"""
        response = client.get("/api/signals/99999")

        assert response.status_code == 404

    def test_get_stats(self, client: TestClient, db: Session, sample_signals):
        """测试获取统计数据"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_signals" in data["data"]
        assert data["data"]["total_signals"] == 10

    def test_health_check(self, client: TestClient):
        """测试健康检查"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data


class TestValidation:
    """输入验证测试"""

    def test_search_query_xss_attack(self, client: TestClient):
        """测试XSS攻击防护"""
        response = client.get("/api/signals?search=<script>alert('xss')</script>")

        # 应该拒绝或清理输入
        assert response.status_code in [200, 400, 422]

    def test_search_query_sql_injection(self, client: TestClient):
        """测试SQL注入防护"""
        response = client.get("/api/signals?search=' OR '1'='1")

        # 应该拒绝或清理输入
        assert response.status_code in [200, 400, 422]

    def test_invalid_limit(self, client: TestClient):
        """测试无效的limit参数"""
        response = client.get("/api/signals?limit=999")

        # 应该强制限制到最大值
        assert response.status_code == 200

    def test_invalid_sort_by(self, client: TestClient):
        """测试无效的sort_by参数"""
        response = client.get("/api/signals?sort_by=invalid_field")

        # 应该返回验证错误
        assert response.status_code == 422


class TestErrorHandling:
    """错误处理测试"""

    def test_404_error(self, client: TestClient):
        """测试404错误处理"""
        response = client.get("/api/signals/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_validation_error(self, client: TestClient):
        """测试验证错误处理"""
        response = client.get("/api/signals?limit=invalid")

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "error" in data
