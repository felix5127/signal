# 输入验证和安全防护
# 防止SQL注入、XSS、路径遍历等安全漏洞

import re
from typing import Optional, List
from pydantic import BaseModel, validator, Field
from html import escape


# 危险字符和SQL注入模式检测
SQL_INJECTION_PATTERNS = [
    r"(\bunion\b.*\bselect\b)",
    r"(\bselect\b.*\bfrom\b)",
    r"(\binsert\b.*\binto\b)",
    r"(\bdelete\b.*\bfrom\b)",
    r"(\bupdate\b.*\bset\b)",
    r"(\bdrop\b.*\btable\b)",
    r"(\bexec\b|\bexecute\b)",
    r"(;.*\b(\bwaitfor\b|\bdelay\b))",
    r"('.*--)",
    r"(\|.*\|)",
    r"(\bor\b.*=)",
    r"(\band\b.*=)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
]


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    清理字符串输入

    Args:
        value: 输入字符串
        max_length: 最大长度

    Returns:
        清理后的字符串
    """
    if not value:
        return ""

    # 截断到最大长度
    if len(value) > max_length:
        value = value[:max_length]

    # 转义HTML特殊字符（防止XSS）
    value = escape(value)

    # 移除控制字符
    value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

    return value.strip()


def check_sql_injection(value: str) -> bool:
    """
    检测SQL注入攻击

    Args:
        value: 输入字符串

    Returns:
        是否包含SQL注入模式
    """
    value_lower = value.lower()

    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True

    return False


def check_xss(value: str) -> bool:
    """
    检测XSS攻击

    Args:
        value: 输入字符串

    Returns:
        是否包含XSS模式
    """
    value_lower = value.lower()

    for pattern in XSS_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True

    return False


def check_path_traversal(value: str) -> bool:
    """
    检测路径遍历攻击

    Args:
        value: 输入字符串

    Returns:
        是否包含路径遍历模式
    """
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, value):
            return True

    return False


def validate_input(value: str, field_name: str = "input") -> str:
    """
    综合验证输入

    Args:
        value: 输入字符串
        field_name: 字段名（用于错误消息）

    Returns:
        验证和清理后的字符串

    Raises:
        ValueError: 如果输入不安全
    """
    if not value:
        return ""

    # 检测各种攻击模式
    if check_sql_injection(value):
        raise ValueError(f"Invalid {field_name}: contains potential SQL injection")

    if check_xss(value):
        raise ValueError(f"Invalid {field_name}: contains potential XSS code")

    if check_path_traversal(value):
        raise ValueError(f"Invalid {field_name}: contains path traversal pattern")

    # 清理输入
    return sanitize_string(value)


# Pydantic验证模型
class SearchQuery(BaseModel):
    """搜索查询验证模型"""

    q: str = Field(..., min_length=1, max_length=200, description="搜索关键词")

    @validator("q")
    def validate_query(cls, v):
        """验证搜索查询"""
        if not v:
            raise ValueError("Query cannot be empty")

        # 检测攻击模式
        if check_sql_injection(v):
            raise ValueError("Query contains invalid characters")

        if check_xss(v):
            raise ValueError("Query contains invalid patterns")

        # 只允许字母、数字、中文和常见符号
        if not re.match(r'^[\w\s\-_.,?!:\u4e00-\u9fff]*$', v):
            raise ValueError("Query contains invalid characters")

        return v.strip()


class SignalFilter(BaseModel):
    """信号筛选验证模型"""

    min_score: Optional[int] = Field(None, ge=1, le=5, description="最低评分")
    source: Optional[str] = Field(None, max_length=50, description="数据源")
    sources: Optional[str] = Field(None, max_length=200, description="多个数据源（逗号分隔）")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    search: Optional[str] = Field(None, max_length=200, description="搜索关键词")
    sort_by: str = Field(
        "created_at",
        pattern="^(created_at|final_score)$",
        description="排序字段"
    )

    @validator("sources")
    def validate_sources(cls, v):
        """验证数据源列表"""
        if v:
            source_list = [s.strip() for s in v.split(",") if s.strip()]

            # 验证每个source
            for source in source_list:
                if not re.match(r'^[a-z0-9_]+$', source):
                    raise ValueError(f"Invalid source name: {source}")

            return ",".join(source_list)

        return v

    @validator("source")
    def validate_source(cls, v):
        """验证单个数据源"""
        if v and not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError("Invalid source name")

        return v

    @validator("category")
    def validate_category(cls, v):
        """验证分类"""
        if v and not re.match(r'^[a-z0-9_\-]+$', v):
            raise ValueError("Invalid category name")

        return v


class PaginationParams(BaseModel):
    """分页参数验证模型"""

    limit: int = Field(20, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")

    @validator("limit")
    def validate_limit(cls, v):
        """验证limit"""
        if v > 100:
            v = 100  # 强制限制最大值
        return v


class URLValidator:
    """URL验证工具"""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL格式"""
        if not url:
            return False

        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE,
        )

        return url_pattern.match(url) is not None


# 速率限制（简单版）
class RateLimiter:
    """
    简单的内存速率限制器

    生产环境建议使用Redis实现分布式速率限制
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}

    def is_allowed(self, identifier: str) -> bool:
        """
        检查是否允许请求

        Args:
            identifier: 唯一标识（通常是IP地址或API密钥）

        Returns:
            是否允许请求
        """
        import time

        now = time.time()

        # 清理过期记录
        if identifier in self.requests:
            self.requests[identifier] = [
                (ts, count)
                for ts, count in self.requests[identifier]
                if now - ts < self.window_seconds
            ]
        else:
            self.requests[identifier] = []

        # 计算当前窗口内的请求数
        current_count = sum(count for _, count in self.requests[identifier])

        if current_count >= self.max_requests:
            return False

        # 记录这次请求
        self.requests[identifier].append((now, 1))

        return True

    def get_remaining_requests(self, identifier: str) -> int:
        """
        获取剩余请求数

        Args:
            identifier: 唯一标识

        Returns:
            剩余请求数
        """
        import time

        now = time.time()

        if identifier in self.requests:
            # 清理过期记录
            self.requests[identifier] = [
                (ts, count)
                for ts, count in self.requests[identifier]
                if now - ts < self.window_seconds
            ]

            current_count = sum(count for _, count in self.requests[identifier])
            return max(0, self.max_requests - current_count)

        return self.max_requests


# 创建全局速率限制器实例
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
