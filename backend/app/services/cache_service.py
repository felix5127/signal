# 智能缓存服务
# 提供分布式的缓存管理，支持动态TTL、缓存预热、失效策略

import json
import hashlib
from typing import Optional, Any, List, Dict, Callable
from functools import wraps
from datetime import datetime, timedelta
import asyncio
import logging

from app.utils.cache import redis_cache
from app.config import config

logger = logging.getLogger(__name__)


class CacheStrategy:
    """缓存策略枚举"""

    LRU = "lru"  # 最近最少使用
    TTL = "ttl"  # 基于时间的过期
    WRITE_THROUGH = "write_through"  # 写穿
    WRITE_BACK = "write_back"  # 写回


class SmartCache:
    """
    智能缓存管理器

    功能：
    - 自动生成缓存键
    - 支持动态TTL
    - 缓存预热
    - 批量失效
    - 缓存统计
    """

    def __init__(self):
        self.enabled = redis_cache.is_enabled()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def is_enabled(self) -> bool:
        """检查缓存是否可用"""
        return self.enabled

    def _generate_key(
        self, prefix: str, params: Dict[str, Any] = None, namespace: str = "default"
    ) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            params: 参数字典
            namespace: 命名空间

        Returns:
            缓存键
        """
        key_parts = [namespace, prefix]

        if params:
            # 对参数进行排序并序列化，确保一致性
            sorted_params = json.dumps(params, sort_keys=True)
            # 使用哈希避免键过长
            params_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            key_parts.append(params_hash)

        return ":".join(key_parts)

    async def get(
        self,
        key: str,
        default: Any = None,
    ) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        if not self.enabled:
            return default

        try:
            value = await redis_cache.get(key)

            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return default

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            await redis_cache.set(key, value, expire=ttl)
            self.stats["sets"] += 1
            logger.debug(f"Cache set: {key}, ttl={ttl}")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            await redis_cache.delete(key)
            self.stats["deletes"] += 1
            logger.debug(f"Cache delete: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        批量删除匹配模式的缓存

        Args:
            pattern: 键模式（如 "signals:*"）

        Returns:
            删除的数量
        """
        if not self.enabled:
            return 0

        try:
            # Redis需要使用SCAN遍历键
            count = 0
            async for key in redis_cache.client.scan_iter(match=pattern):
                await redis_cache.delete(key)
                count += 1

            self.stats["deletes"] += count
            logger.info(f"Cache delete pattern: {pattern}, count={count}")
            return count

        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """
        获取缓存，如果不存在则通过factory函数创建

        Args:
            key: 缓存键
            factory: 值工厂函数（可以是协程函数）
            ttl: 过期时间

        Returns:
            缓存值
        """
        # 先尝试获取
        value = await self.get(key)

        if value is not None:
            return value

        # 缓存未命中，调用工厂函数
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        # 设置缓存
        await self.set(key, value, ttl)

        return value

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计字典
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "hit_rate": round(hit_rate * 100, 2),
            "total": total,
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }


# 全局缓存实例
smart_cache = SmartCache()


def cache_result(
    key_prefix: str,
    ttl: int = 3600,
    namespace: str = "default",
):
    """
    缓存函数结果的装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        namespace: 命名空间

    Usage:
        @cache_result("signals", ttl=600, namespace="api")
        async def get_signals(filters):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            # 将参数转换为字典
            params_str = json.dumps(kwargs, sort_keys=True)
            cache_key = smart_cache._generate_key(
                prefix=key_prefix,
                params={"params": params_str},
                namespace=namespace,
            )

            # 尝试从缓存获取
            cached = await smart_cache.get(cache_key)
            if cached is not None:
                return cached

            # 调用原函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await smart_cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class CacheWarmer:
    """
    缓存预热器

    用于在系统启动或定时预热常用数据
    """

    def __init__(self, cache: SmartCache):
        self.cache = cache

    async def warmup_signals_list(self):
        """预热信号列表缓存"""
        try:
            from app.services.signal_service import SignalService
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                service = SignalService(db)

                # 预热热门查询
                from app.middlewares.validation import SignalFilter

                popular_filters = [
                    SignalFilter(),  # 默认查询
                    SignalFilter(min_score=4),  # 高质量
                    SignalFilter(source="github"),  # GitHub
                    SignalFilter(sort_by="final_score"),  # 热门排序
                ]

                for filter_obj in popular_filters:
                    key = self.cache._generate_key(
                        prefix="signals",
                        params=filter_obj.dict(),
                        namespace="api",
                    )

                    # 检查是否已缓存
                    cached = await self.cache.get(key)
                    if cached is None:
                        # 执行查询并缓存
                        items, total = service.get_signals(filter_obj, 20, 0)
                        await self.cache.set(
                            key,
                            {"items": items, "total": total},
                            ttl=600,  # 10分钟
                        )
                        logger.info(f"Warmed up cache: {key}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Cache warmup error: {e}")

    async def warmup_stats(self):
        """预热统计数据缓存"""
        try:
            from app.services.signal_service import SignalService
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                service = SignalService(db)
                stats = service.get_signal_stats()

                key = self.cache._generate_key(
                    prefix="stats", namespace="api"
                )
                await self.cache.set(key, stats, ttl=300)  # 5分钟
                logger.info(f"Warmed up stats cache")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Stats warmup error: {e}")

    async def warmup_all(self):
        """预热所有缓存"""
        logger.info("Starting cache warmup...")
        await self.warmup_signals_list()
        await self.warmup_stats()
        logger.info("Cache warmup completed")


# 创建缓存预热器
cache_warmer = CacheWarmer(smart_cache)
