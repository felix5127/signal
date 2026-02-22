"""
[INPUT]: 依赖 database.py (Base), hashlib, sqlalchemy (Column, ForeignKey, Index, JSON 等)
[OUTPUT]: 对外提供 Resource ORM 模型，支持 article/podcast/tweet/video 四类内容
[POS]: models/ 的核心数据模型，v2.0 架构，被 api/processors/tasks 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
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
    - pending: 待处理（待 LLM 评分）
    - approved: LLM 通过，待人工审核
    - rejected: LLM 拒绝，待人工确认
    - published: 已发布，对外可见
    - archived: 已归档
    - failed: 处理失败
    """

    __tablename__ = "resources"

    # ========== 类型与来源 ==========
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)  # article/podcast/tweet/video
    source_name = Column(String(255), nullable=False)
    source_url = Column(Text)
    source_icon_url = Column(Text)
    thumbnail_url = Column(Text)  # 缩略图/封面 URL (播客/视频)
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
    domain = Column(String(100))
    subdomain = Column(String(100))
    tags = Column(JSON)

    # ========== 评分 ==========
    score = Column(Integer, default=0, index=True)
    is_featured = Column(Boolean, default=False, index=True)

    # ========== 状态 ==========
    language = Column(String(10))
    status = Column(String(20), default="pending", index=True)

    # ========== LLM 过滤结果 ==========
    llm_score = Column(Integer, nullable=True, index=True)  # 0-5 分
    llm_reason = Column(Text, nullable=True)                # LLM 判断理由
    llm_prompt_version = Column(Integer, nullable=True)     # 使用的 Prompt 版本

    # ========== 人工审核 ==========
    review_status = Column(String(20), nullable=True)       # approved/rejected (人工)
    review_comment = Column(Text, nullable=True)            # 人工批注
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    # ========== 来源关联 ==========
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)

    # ========== 播客/视频专用 ==========
    audio_url = Column(Text)
    duration = Column(Integer)
    transcript = Column(Text)
    chapters = Column(JSON)  # 章节列表 [{time: int, title: str, summary?: str}]
    qa_pairs = Column(JSON)  # Q&A 对 [{question: str, answer: str, timestamp?: int}]

    # ========== 精选理由 ==========
    featured_reason = Column(Text)     # 英文精选理由
    featured_reason_zh = Column(Text)  # 中文精选理由

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
        Index("idx_resources_llm_score", "llm_score"),
        Index("idx_resources_source_id", "source_id"),
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
            "source_id": self.source_id,
            "thumbnail_url": self.thumbnail_url,
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
            "featured_reason": self.featured_reason,
            "featured_reason_zh": self.featured_reason_zh,
            "language": self.language,
            "status": self.status,
            # LLM 过滤结果
            "llm_score": self.llm_score,
            "llm_reason": self.llm_reason,
            "llm_prompt_version": self.llm_prompt_version,
            # 人工审核
            "review_status": self.review_status,
            "review_comment": self.review_comment,
            "reviewed_at": (
                self.reviewed_at.isoformat() if self.reviewed_at else None
            ),
            "reviewed_by": self.reviewed_by,
            # 播客/视频专用
            "audio_url": self.audio_url,
            "duration": self.duration,
            "transcript": self.transcript,
            "chapters": self.chapters,
            "qa_pairs": self.qa_pairs,
            # 时间戳
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
