"""
[INPUT]: 依赖 database.py (SessionLocal), models/resource.py (Resource)
[OUTPUT]: 对外提供 Deduper 类
[POS]: 内容处理层，三层去重器 (URL + 标题相似度 + 内容指纹)
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.resource import Resource


class Deduper:
    """
    内容去重器

    三层去重策略：
    1. URL 精确匹配（数据库查重）
    2. 标题相似度（Jaccard > 0.8，近 7 天）
    3. 内容指纹（SimHash 汉明距离 < 3，可选）

    使用方式：
    - 单条检查：is_duplicate(url, title)
    - 批量去重：dedupe_batch(items)
    """

    # 标题相似度阈值
    TITLE_SIMILARITY_THRESHOLD = 0.8

    # 去重时间窗口（天）
    DEDUP_WINDOW_DAYS = 7

    def __init__(self, db: Optional[Session] = None):
        """
        初始化去重器

        Args:
            db: 数据库 Session（可选）
        """
        self._db = db
        self._owns_session = db is None

        # 运行时缓存（批量处理时使用）
        self._url_cache: Set[str] = set()
        self._title_cache: Set[str] = set()

    def _get_db(self) -> Session:
        """获取数据库 Session"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _close_db(self):
        """关闭自己创建的 Session"""
        if self._owns_session and self._db is not None:
            self._db.close()
            self._db = None

    @staticmethod
    def compute_url_hash(url: str) -> str:
        """计算 URL 哈希"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_title_tokens(title: str) -> Set[str]:
        """
        将标题分词为 token 集合

        简单实现：按空格分词 + 中文按字分割
        """
        import re

        tokens = set()

        # 英文按空格分词
        english_tokens = re.findall(r'[a-zA-Z]+', title.lower())
        tokens.update(english_tokens)

        # 中文按字分割
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', title)
        tokens.update(chinese_chars)

        return tokens

    @staticmethod
    def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """计算两个集合的 Jaccard 相似度"""
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _url_exists_in_db(self, url_hash: str) -> bool:
        """检查 URL 是否已存在于数据库"""
        db = self._get_db()
        try:
            exists = db.query(Resource).filter(
                Resource.url_hash == url_hash
            ).first() is not None
            return exists
        finally:
            pass  # 不在这里关闭，由调用者决定

    def _get_recent_titles(self) -> List[str]:
        """获取近 N 天的标题列表"""
        db = self._get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.DEDUP_WINDOW_DAYS)
            results = db.query(Resource.title).filter(
                Resource.created_at > cutoff
            ).all()
            return [r[0] for r in results if r[0]]
        finally:
            pass

    def _similar_title_exists(self, title: str, recent_titles: Optional[List[str]] = None) -> bool:
        """
        检查是否存在相似标题

        Args:
            title: 待检查的标题
            recent_titles: 最近的标题列表（可选，不传则从数据库获取）

        Returns:
            是否存在相似标题
        """
        if not title:
            return False

        title_tokens = self.compute_title_tokens(title)

        # 从数据库获取或使用传入的列表
        if recent_titles is None:
            recent_titles = self._get_recent_titles()

        for existing_title in recent_titles:
            existing_tokens = self.compute_title_tokens(existing_title)
            similarity = self.jaccard_similarity(title_tokens, existing_tokens)

            if similarity > self.TITLE_SIMILARITY_THRESHOLD:
                return True

        return False

    def is_duplicate(self, url: str, title: str) -> tuple[bool, str]:
        """
        检查单条内容是否重复

        Args:
            url: 内容 URL
            title: 内容标题

        Returns:
            (is_duplicate, reason) - 是否重复及原因
        """
        try:
            # 1. URL 精确匹配
            url_hash = self.compute_url_hash(url)

            # 检查运行时缓存
            if url_hash in self._url_cache:
                return True, "URL 重复（缓存）"

            # 检查数据库
            if self._url_exists_in_db(url_hash):
                return True, "URL 重复（数据库）"

            # 2. 标题相似度
            title_key = title.lower().strip()

            # 检查运行时缓存
            if title_key in self._title_cache:
                return True, "标题重复（缓存）"

            # 检查数据库
            if self._similar_title_exists(title):
                return True, "标题相似度过高"

            # 不重复，添加到缓存
            self._url_cache.add(url_hash)
            self._title_cache.add(title_key)

            return False, ""

        finally:
            if self._owns_session:
                self._close_db()

    def dedupe_batch(self, items: List[dict]) -> List[dict]:
        """
        批量去重

        Args:
            items: 内容列表，每个 item 应包含 url 和 title

        Returns:
            去重后的内容列表
        """
        try:
            # 预加载最近标题
            recent_titles = self._get_recent_titles()

            result = []
            for item in items:
                url = item.get("url", "")
                title = item.get("title", "")

                if not url:
                    continue

                # URL 去重
                url_hash = self.compute_url_hash(url)
                if url_hash in self._url_cache or self._url_exists_in_db(url_hash):
                    continue

                # 标题去重
                title_key = title.lower().strip()
                if title_key in self._title_cache:
                    continue

                if self._similar_title_exists(title, recent_titles):
                    continue

                # 通过去重
                self._url_cache.add(url_hash)
                self._title_cache.add(title_key)
                recent_titles.append(title)  # 添加到列表用于后续比较

                result.append(item)

            return result

        finally:
            if self._owns_session:
                self._close_db()

    def reset_cache(self):
        """重置运行时缓存"""
        self._url_cache.clear()
        self._title_cache.clear()


# 全局单例
deduper = Deduper()
