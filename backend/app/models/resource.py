# Input: database.py (Base), hashlib
# Output: Resource 表 ORM 模型，用于存储文章/播客/推文/视频资源
# Position: 数据持久化层，v2.0 核心数据模型，替代 Signal 用于内容聚合
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Index,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy import event

from app.database import Base

# 使用 JSON 类型，PostgreSQL 会自动优化为 JSONB，SQLite 使用 TEXT 存储
# 注意：生产环境（PostgreSQL）建议手动迁移为 JSONB 以获得更好的查询性能


class Resource(Base):
    """
    Resource 表模型 - 存储多类型内容资源

    支持四种内容类型：
    - article: 文章（RSS采集 + 全文提取）
    - podcast: 播客（RSS采集 + 音频转写）
    - tweet: 推文（XGo.ing采集）
    - video: 视频（RSS采集 + 转写）

    评分体系：
    - 0-100 综合评分
    - score >= 85 自动标记为精选

    处理状态：
    - pending: 待处理
    - analyzing: LLM分析中
    - published: 已发布
    - failed: 处理失败
    """

    __tablename__ = "resources"

    # ========== 类型与来源 ==========
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)  # article/podcast/tweet/video
    source_name = Column(String(100), nullable=False)
    source_url = Column(Text)
    source_icon_url = Column(Text)
    url = Column(Text, nullable=False, unique=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)

    # ========== 原始内容 ==========
    title = Column(Text, nullable=False)
    title_translated = Column(Text)
    author = Column(String(255))
    content_markdown = Column(Text)
    content_html = Column(Text)
    word_count = Column(Integer)
    read_time = Column(Integer)

    # ========== LLM分析结果 ==========
    one_sentence_summary = Column(String(500))
    one_sentence_summary_zh = Column(String(500))
    summary = Column(Text)
    summary_zh = Column(Text)
    main_points = Column(JSON)
    main_points_zh = Column(JSON)
    key_quotes = Column(JSON)
    key_quotes_zh = Column(JSON)

    # ========== 分类与标签 ==========
    domain = Column(String(50))
    subdomain = Column(String(50))
    tags = Column(JSON)

    # ========== 评分 ==========
    score = Column(Integer, default=0, index=True)
    is_featured = Column(Boolean, default=False, index=True)

    # ========== 状态 ==========
    language = Column(String(10))
    status = Column(String(20), default="pending", index=True)

    # ========== 播客/视频专用 ==========
    audio_url = Column(Text)
    duration = Column(Integer)
    transcript = Column(Text)

    # ========== 深度研究 (Deep Research) ==========
    deep_research = Column(Text)  # 深度研究报告（Markdown 格式）
    deep_research_generated_at = Column(DateTime)  # 报告生成时间
    deep_research_tokens = Column(Integer)  # Token 消耗
    deep_research_cost = Column(Float)  # 成本（美元）
    deep_research_strategy = Column(String(20))  # 使用的策略 (lightweight/full_agent)
    deep_research_sources = Column(Text)  # 引用来源（JSON 数组字符串）
    deep_research_metadata = Column(Text)  # 扩展元数据（JSON 字符串）

    # ========== 时间戳 ==========
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    analyzed_at = Column(DateTime)

    # ========== 元数据 ==========
    extra_metadata = Column(JSON)

    # ========== 复合索引优化 ==========
    __table_args__ = (
        Index("idx_resources_type_published", "type", "published_at"),
        Index("idx_resources_type_score", "type", "score"),
        Index("idx_resources_domain_score", "domain", "score"),
        Index("idx_resources_status_created", "status", "created_at"),
        Index("idx_resources_featured_published", "is_featured", "published_at"),
        Index("idx_resources_language", "language"),
        Index("idx_resources_source_name", "source_name"),
        Index("idx_resources_published_at_desc", "published_at"),
    )

    @staticmethod
    def generate_url_hash(url: str) -> str:
        """生成 URL 哈希值（用于去重）"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def should_be_featured(score: int) -> bool:
        """判断是否应该标记为精选"""
        return score >= 85

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        return {
            "id": self.id,
            "type": self.type,
            "source_name": self.source_name,
            "url": self.url,
            "title": self.title,
            "title_translated": self.title_translated,
            "author": self.author,
            "one_sentence_summary": self.one_sentence_summary,
            "one_sentence_summary_zh": self.one_sentence_summary_zh,
            "summary": self.summary,
            "summary_zh": self.summary_zh,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "tags": self.tags,
            "score": self.score,
            "is_featured": self.is_featured,
            "language": self.language,
            "status": self.status,
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "analyzed_at": (
                self.analyzed_at.isoformat() if self.analyzed_at else None
            ),
        }


# ============================================================================
# 缓存失效钩子
# ============================================================================

@event.listens_for(Resource, 'after_update')
@event.listens_for(Resource, 'after_insert')
def invalidate_resource_cache(mapper, connection, target):
    """Resource 数据更新时自动失效缓存"""
    import asyncio

    async def _invalidate():
        try:
            from app.utils.cache import redis_cache
            await redis_cache.delete(f"resource:detail:{target.id}")
            await redis_cache.delete_pattern("resources:list*")
            await redis_cache.delete("resources:stats")
        except Exception:
            pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_invalidate())
    except RuntimeError:
        # 没有运行中的事件循环，跳过缓存失效
        pass
