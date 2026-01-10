# Input: database.py (Base)
# Output: Signal 表 ORM 模型
# Position: 数据持久化层，定义 signals 表结构
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import hashlib
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Index
from sqlalchemy.sql import func

from app.database import Base


class Signal(Base):
    """
    Signal 表模型 - 存储技术信号数据

    字段说明：
    - source: 数据来源 ('hn' | 'github' | 'huggingface')
    - url: 原文链接（唯一键）
    - url_hash: URL 的 SHA256 hash，用于快速去重
    - title: 标题
    - title_hash: 标题的 SimHash，用于相似度去重
    - summary: LLM 生成的摘要
    - one_liner: 20 字一句话总结
    - heat_score: 热度评分 1-5
    - quality_score: 质量评分 1-5
    - final_score: 综合星级（取较低值）
    - category: 分类标签
    - status: 处理状态
    - metadata: JSON 格式的额外元数据
    """

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 来源信息
    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255))  # 原始平台 ID
    url = Column(Text, nullable=False, unique=True)
    url_hash = Column(String(64), nullable=False, index=True)

    # 内容
    title = Column(Text, nullable=False)
    title_hash = Column(String(64), index=True)  # SimHash 用于相似度检测
    raw_content = Column(Text)  # 原始内容
    processed_content = Column(Text)  # Jina Reader 处理后的 Markdown
    summary = Column(Text)  # LLM 生成的摘要
    one_liner = Column(String(100))  # 一句话总结

    # 评分
    heat_score = Column(Integer, default=0)  # 热度评分
    quality_score = Column(Integer, default=0)  # 质量评分
    final_score = Column(Integer, default=0, index=True)  # 综合星级

    # 分类
    category = Column(String(50))  # 技术突破/开源工具/商业产品/论文研究/行业动态

    # 状态跟踪
    status = Column(
        String(20), default="pending", index=True
    )  # pending/scraped/filtered/processed/failed
    filter_stage = Column(String(20))  # rule_passed/llm_passed/rejected
    filter_reason = Column(Text)  # 过滤原因（如被拒绝）

    # 尽调结果（JSON 格式字符串）
    due_diligence = Column(Text)  # GitHub 尽调详情

    # Deep Research 深度研究报告
    deep_dive = Column(Text)  # 深度研究报告（Markdown 格式）
    deep_dive_generated_at = Column(DateTime)  # 报告生成时间
    deep_dive_tokens = Column(Integer)  # Token 消耗
    deep_dive_cost = Column(Float)  # 成本（美元）
    deep_dive_strategy = Column(String(20))  # 使用的策略 (lightweight/full_agent)
    deep_dive_sources = Column(Text)  # 引用来源（JSON 数组）
    deep_dive_metadata = Column(Text)  # 扩展元数据（JSON）

    # 时间戳
    source_created_at = Column(DateTime)  # 原始内容创建时间
    created_at = Column(DateTime, default=func.now(), index=True)
    processed_at = Column(DateTime)

    # 元数据（JSON 格式字符串）
    source_metadata = Column(Text)  # HN score, GitHub stars, comments 等
    tags = Column(String(500))  # 逗号分隔的标签
    matched_conditions = Column(String(50))  # 匹配的条件 (A,B,C)

    # 复合索引优化（用于常见查询）
    __table_args__ = (
        # 按来源和创建时间查询（前端数据源筛选）
        Index('idx_source_created', 'source', 'created_at'),
        # 按评分和创建时间查询（热门排序）
        Index('idx_score_created', 'final_score', 'created_at'),
        # 按状态和创建时间查询（待处理任务）
        Index('idx_status_created', 'status', 'created_at'),
    )

    @staticmethod
    def generate_url_hash(url: str) -> str:
        """生成 URL 的 SHA256 hash"""
        return hashlib.sha256(url.encode()).hexdigest()

    @staticmethod
    def generate_title_hash(title: str) -> str:
        """
        生成标题的简单 hash（用于相似度检测）

        注意：这是一个简化版本，生产环境建议使用 SimHash 算法
        """
        # 简化版：只取标题的前 200 字符的 hash
        normalized = title.lower().strip()[:200]
        return hashlib.md5(normalized.encode()).hexdigest()

    def __repr__(self):
        return f"<Signal(id={self.id}, source={self.source}, title={self.title[:50]})>"
