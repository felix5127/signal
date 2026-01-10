# 输入验证测试
# 测试安全防护和输入验证

import pytest
from app.middlewares.validation import (
    sanitize_string,
    check_sql_injection,
    check_xss,
    check_path_traversal,
    validate_input,
    SearchQuery,
    SignalFilter,
    URLValidator,
    RateLimiter,
)


class TestSanitization:
    """输入清理测试"""

    def test_sanitize_string_basic(self):
        """测试基本字符串清理"""
        assert sanitize_string("hello world") == "hello world"
        assert sanitize_string("  hello  ") == "hello"

    def test_sanitize_string_html_escape(self):
        """测试HTML转义"""
        assert sanitize_string("<script>") == "&lt;script&gt;"
        assert sanitize_string("<div>") == "&lt;div&gt;"

    def test_sanitize_string_max_length(self):
        """测试长度限制"""
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_empty(self):
        """测试空字符串"""
        assert sanitize_string("") == ""
        assert sanitize_string(None) == ""


class TestSecurityChecks:
    """安全检查测试"""

    def test_check_sql_injection_true(self):
        """测试SQL注入检测（应该检测到）"""
        assert check_sql_injection("'; DROP TABLE users; --")
        assert check_sql_injection("1' OR '1'='1")
        assert check_sql_injection("UNION SELECT * FROM users")

    def test_check_sql_injection_false(self):
        """测试SQL注入检测（正常的输入）"""
        assert not check_sql_injection("normal text")
        assert not check_sql_injection("hello world")

    def test_check_xss_true(self):
        """测试XSS检测（应该检测到）"""
        assert check_xss("<script>alert('xss')</script>")
        assert check_xss("<div onerror=\"alert('xss')\">")
        assert check_xss("javascript:alert('xss')")

    def test_check_xss_false(self):
        """测试XSS检测（正常的输入）"""
        assert not check_xss("normal text")
        assert not check_xss("<div>normal</div>")  # 没有事件处理器

    def test_check_path_traversal_true(self):
        """测试路径遍历检测（应该检测到）"""
        assert check_path_traversal("../../../etc/passwd")
        assert check_path_traversal("..\\..\\windows\\system32")

    def test_check_path_traversal_false(self):
        """测试路径遍历检测（正常的输入）"""
        assert not check_path_traversal("normal/path")
        assert not check_path_traversal("file.txt")


class TestValidateInput:
    """综合输入验证测试"""

    def test_validate_input_normal(self):
        """测试正常输入"""
        result = validate_input("hello world")
        assert result == "hello world"

    def test_validate_input_sql_injection(self):
        """测试SQL注入输入"""
        with pytest.raises(ValueError, match="SQL injection"):
            validate_input("'; DROP TABLE users; --")

    def test_validate_input_xss(self):
        """测试XSS输入"""
        with pytest.raises(ValueError, match="XSS"):
            validate_input("<script>alert('xss')</script>")

    def test_validate_input_path_traversal(self):
        """测试路径遍历输入"""
        with pytest.raises(ValueError, match="path traversal"):
            validate_input("../../../etc/passwd")


class TestSearchQuery:
    """SearchQuery验证模型测试"""

    def test_valid_query(self):
        """测试有效查询"""
        query = SearchQuery(q="test search")
        assert query.q == "test search"

    def test_empty_query(self):
        """测试空查询"""
        with pytest.raises(ValueError):
            SearchQuery(q="")

    def test_query_too_long(self):
        """测试过长的查询"""
        with pytest.raises(ValueError):
            SearchQuery(q="a" * 201)

    def test_query_with_special_chars(self):
        """测试特殊字符"""
        # 允许的特殊字符
        query = SearchQuery(q="test-query_123")
        assert query.q == "test-query_123"

    def test_query_with_sql_injection(self):
        """测试包含SQL注入的查询"""
        with pytest.raises(ValueError):
            SearchQuery(q="'; DROP TABLE users; --")


class TestSignalFilter:
    """SignalFilter验证模型测试"""

    def test_valid_filter(self):
        """测试有效的筛选器"""
        filter = SignalFilter(
            min_score=3,
            source="github",
            category="ai",
            sort_by="created_at",
        )
        assert filter.min_score == 3
        assert filter.source == "github"

    def test_invalid_min_score(self):
        """测试无效的最低评分"""
        with pytest.raises(ValueError):
            SignalFilter(min_score=6)  # 最大值是5

        with pytest.raises(ValueError):
            SignalFilter(min_score=0)  # 最小值是1

    def test_invalid_sort_by(self):
        """测试无效的排序字段"""
        with pytest.raises(ValueError):
            SignalFilter(sort_by="invalid_field")

    def test_sources_validation(self):
        """测试多个数据源验证"""
        filter = SignalFilter(sources="github,huggingface,arxiv")
        assert filter.sources == "github,huggingface,arxiv"

    def test_invalid_source_name(self):
        """测试无效的数据源名称"""
        with pytest.raises(ValueError):
            SignalFilter(source="github@123")


class TestURLValidator:
    """URL验证测试"""

    def test_valid_urls(self):
        """测试有效的URL"""
        assert URLValidator.is_valid_url("https://github.com/test/repo")
        assert URLValidator.is_valid_url("http://example.com")
        assert URLValidator.is_valid_url("https://localhost:8000")

    def test_invalid_urls(self):
        """测试无效的URL"""
        assert not URLValidator.is_valid_url("")
        assert not URLValidator.is_valid_url("not a url")
        assert not URLValidator.is_valid_url("ftp://example.com")


class TestRateLimiter:
    """速率限制测试"""

    def test_rate_limiter_basic(self):
        """测试基本速率限制"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # 前5个请求应该被允许
        for i in range(5):
            assert limiter.is_allowed("test_user") is True

        # 第6个请求应该被拒绝
        assert limiter.is_allowed("test_user") is False

    def test_rate_limiter_different_users(self):
        """测试不同用户的速率限制"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # 用户1
        for i in range(3):
            assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

        # 用户2应该有自己的限制
        assert limiter.is_allowed("user2") is True

    def test_rate_limiter_window_expiry(self):
        """测试时间窗口过期"""
        import time

        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # 前2个请求
        assert limiter.is_allowed("test_user") is True
        assert limiter.is_allowed("test_user") is True
        assert limiter.is_allowed("test_user") is False

        # 等待窗口过期
        time.sleep(1.1)

        # 现在应该又能请求了
        assert limiter.is_allowed("test_user") is True

    def test_get_remaining_requests(self):
        """测试获取剩余请求数"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        # 初始应该是10
        assert limiter.get_remaining_requests("test_user") == 10

        # 使用3次后应该是7
        for i in range(3):
            limiter.is_allowed("test_user")

        assert limiter.get_remaining_requests("test_user") == 7
