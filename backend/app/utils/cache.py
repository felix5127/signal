# Input: Redis 配置（config.redis），FastAPI Request（可选，用于缓存键生成）
# Output: Redis 缓存客户端，缓存装饰器（cache_result）
# Position: 缓存层，为 API 提供高性能缓存支持（含降级机制）
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from app.config import config


logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Redis 客户端（单例模式，支持连接池）
# ============================================================================


class RedisCache:
    """
    Redis 缓存客户端（异步）

    特性：
    - 连接池管理
    - 自动序列化/反序列化 JSON
    - 健康检查 + 自动重连
    - 降级机制（Redis 挂了自动返回 None）
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._enabled = config.redis.enabled
        self._key_prefix = config.redis.key_prefix

    async def connect(self):
        """初始化 Redis 连接池"""
        if not self._enabled:
            logger.info("[RedisCache] Cache disabled by config")
            return

        try:
            self._pool = ConnectionPool.from_url(
                config.redis.url,
                max_connections=config.redis.max_connections,
                socket_timeout=config.redis.socket_timeout,
                socket_connect_timeout=config.redis.socket_connect_timeout,
                decode_responses=True,  # 自动解码为字符串
            )
            self._client = aioredis.Redis(connection_pool=self._pool)

            # 测试连接
            await self._client.ping()
            logger.info(f"[RedisCache] Connected to Redis: {config.redis.url}")

        except Exception as e:
            logger.error(f"[RedisCache] Failed to connect: {e}")
            self._enabled = False  # 自动降级
            self._client = None

    async def close(self):
        """关闭 Redis 连接"""
        if self._client:
            await self._client.close()
            logger.info("[RedisCache] Connection closed")

    def is_enabled(self) -> bool:
        """检查缓存是否可用"""
        return self._enabled and self._client is not None

    def _make_key(self, key: str) -> str:
        """生成完整的缓存键（带前缀）"""
        return f"{self._key_prefix}{key}"

    # ========== 基础操作 ==========

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Returns:
            缓存值（反序列化后的对象），如果不存在或 Redis 挂了返回 None
        """
        if not self.is_enabled():
            return None

        try:
            value = await self._client.get(self._make_key(key))
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning(f"[RedisCache] Get failed: {e}")
            return None  # 降级：返回 None，继续查数据库

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键（不含前缀）
            value: 缓存值（自动序列化为 JSON）
            ttl: 过期时间（秒），None 表示永不过期

        Returns:
            是否成功（Redis 挂了返回 False）
        """
        if not self.is_enabled():
            return False

        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self._client.set(
                self._make_key(key),
                serialized,
                ex=ttl,
            )
            return True
        except Exception as e:
            logger.warning(f"[RedisCache] Set failed: {e}")
            return False  # 降级：不影响业务

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_enabled():
            return False

        try:
            await self._client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.warning(f"[RedisCache] Delete failed: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        批量删除缓存（按模式匹配）

        Returns:
            删除的数量
        """
        if not self.is_enabled():
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = []
            async for key in self._client.scan_iter(full_pattern):
                keys.append(key)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"[RedisCache] Delete pattern failed: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.is_enabled():
            return False

        try:
            return await self._client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.warning(f"[RedisCache] Exists failed: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_enabled():
            return False

        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.warning(f"[RedisCache] Health check failed: {e}")
            self._enabled = False  # 自动降级
            return False


# 全局 Redis 客户端实例
redis_cache = RedisCache()


# ============================================================================
# 缓存装饰器（用于 API 端点）
# ============================================================================


def cache_result(
    key_func: Callable[..., str],
    ttl: int = 300,
    cache_empty: bool = True,
):
    """
    缓存装饰器（用于 FastAPI 端点）

    Args:
        key_func: 生成缓存键的函数（接收请求参数）
        ttl: 缓存过期时间（秒）
        cache_empty: 是否缓存空结果（防止缓存穿透）

    Example:
        @router.get("/resources")
        @cache_result(
            key_func=lambda kwargs: f"resources:list:{kwargs['type']}:{kwargs['page']}",
            ttl=300,
        )
        async def get_resources(type: str, page: int, db: Session = Depends(get_db)):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        import asyncio

        # 检测是否是异步函数
        is_async = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # 生成缓存键（支持函数或 lambda）
            try:
                cache_key = key_func(**kwargs)
            except TypeError:
                # 如果 key_func 不接受 **kwargs，尝试直接传递
                cache_key = key_func(kwargs) if kwargs else key_func()

            # 尝试从缓存获取
            cached = await redis_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"[Cache] HIT: {cache_key}")
                return cached

            logger.debug(f"[Cache] MISS: {cache_key}")

            # 缓存未命中，执行原函数
            result = await func(*args, **kwargs)

            # 缓存结果（包括空结果，防止穿透）
            if cache_empty or result is not None:
                await redis_cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"[Cache] SET: {cache_key} (TTL={ttl}s)")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 生成缓存键（支持函数或 lambda）
            try:
                cache_key = key_func(**kwargs)
            except TypeError:
                # 如果 key_func 不接受 **kwargs，尝试直接传递
                cache_key = key_func(kwargs) if kwargs else key_func()

            # 同步函数不使用缓存（Redis 客户端是异步的）
            # 如果需要同步缓存，可以使用同步 Redis 客户端
            logger.debug(f"[Cache] SYNC function, cache skipped for: {cache_key}")

            # 直接执行原函数
            return func(*args, **kwargs)

        # 返回对应的 wrapper
        return async_wrapper if is_async else sync_wrapper

    return decorator


# ============================================================================
# 辅助函数：生成缓存键
# ============================================================================


def make_resources_list_key(**kwargs) -> str:
    """
    为资源列表生成缓存键

    Args:
        type: 资源类型
        domain: 分类
        timeFilter: 时间过滤
        sort: 排序方式
        featured: 是否精选
        page: 页码
        pageSize: 每页数量
    """
    parts = [
        "resources:list",
        kwargs.get("type") or "all",
        kwargs.get("domain") or "all",
        kwargs.get("timeFilter") or "1w",
        kwargs.get("sort") or "default",
        f"featured={kwargs.get('featured')}",
        f"page={kwargs.get('page', 1)}",
        f"pageSize={kwargs.get('pageSize', 20)}",
    ]
    return ":".join(parts)


def make_resource_detail_key(resource_id: int) -> str:
    """为资源详情生成缓存键"""
    return f"resource:detail:{resource_id}"


def make_resources_stats_key(**kwargs) -> str:
    """为资源统计生成缓存键"""
    return "resources:stats"


def make_search_key(**kwargs) -> str:
    """
    为搜索结果生成缓存键

    Args:
        q: 搜索关键词
        type: 资源类型
        domain: 分类
        timeFilter: 时间过滤
        sort: 排序方式
        page: 页码
        pageSize: 每页数量
    """
    parts = [
        "resources:search",
        kwargs.get("q", ""),
        kwargs.get("type") or "all",
        kwargs.get("domain") or "all",
        kwargs.get("timeFilter") or "all",
        kwargs.get("sort") or "default",
        f"page={kwargs.get('page', 1)}",
        f"pageSize={kwargs.get('pageSize', 20)}",
    ]
    return ":".join(parts)


def make_tags_key(**kwargs) -> str:
    """为标签列表生成缓存键"""
    return "tags:list"


def make_podcast_detail_key(resource_id: int) -> str:
    """为播客详情生成缓存键（包含章节、QA等完整数据）"""
    return f"podcast:detail:{resource_id}"


def make_research_project_key(project_id: int) -> str:
    """为研究项目生成缓存键"""
    return f"research:project:{project_id}"


def make_research_sources_key(project_id: int) -> str:
    """为研究项目源材料列表生成缓存键"""
    return f"research:sources:{project_id}"


# ============================================================================
# 缓存 TTL 常量（秒）
# ============================================================================

CACHE_TTL = {
    "resources_list": 300,      # 资源列表 5 分钟
    "resource_detail": 600,     # 资源详情 10 分钟
    "podcast_detail": 600,      # 播客详情 10 分钟
    "search_results": 180,      # 搜索结果 3 分钟
    "stats": 60,                # 统计数据 1 分钟
    "tags": 3600,               # 标签列表 1 小时
    "research_project": 300,    # 研究项目 5 分钟
    "research_sources": 300,    # 研究源 5 分钟
}
