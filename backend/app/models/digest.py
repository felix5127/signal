"""
[INPUT]: 依赖 database 的 Base (SQLAlchemy 基类)
[OUTPUT]: 对外提供 DailyDigest, WeeklyDigest 模型
[POS]: 数据模型层，日周精选汇总的 ORM 定义
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DailyDigest(Base):
    """每日精选汇总

    每天早上7点生成，包含昨日最重要的信号
    """
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)  # 格式: "2025-12-31"
    created_at = Column(DateTime, default=datetime.utcnow)

    # 汇总统计
    total_signals = Column(Integer, default=0)  # 当天总信号数
    sources_breakdown = Column(JSON, default=dict)  # {"hn": 10, "github": 5, "hf": 2}

    # 精选信号 ID 列表（分源）
    top_hn_ids = Column(JSON, default=list)  # HN 精选 ID 列表
    top_github_ids = Column(JSON, default=list)  # GitHub 精选 ID 列表
    top_hf_ids = Column(JSON, default=list)  # HF 精选 ID 列表
    top_other_ids = Column(JSON, default=list)  # 其他源精选 ID 列表

    # 摘要
    summary = Column(Text)  # AI 生成的当日概览
    trending_topics = Column(JSON, default=list)  # ["AI模型", "开源工具"]


class WeeklyDigest(Base):
    """每周精选汇总

    每周一早上8点生成，包含上周 Top 10
    """
    __tablename__ = "weekly_digests"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(String, index=True)  # 格式: "2025-12-25" (周一)
    week_end = Column(String)  # 格式: "2025-12-31" (周日)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 汇总统计
    total_signals = Column(Integer, default=0)  # 本周总信号数
    sources_breakdown = Column(JSON, default=dict)  # 来源分布

    # Top 10 信号 ID 列表
    top_10_ids = Column(JSON, default=list)  # 综合评分 Top 10

    # 分类 Top 3
    top_breakthroughs = Column(JSON, default=list)  # 技术突破 Top 3
    top_tools = Column(JSON, default=list)  # 开源工具 Top 3
    top_papers = Column(JSON, default=list)  # 论文研究 Top 2
    top_news = Column(JSON, default=list)  # 行业动态 Top 2

    # 摘要
    summary = Column(Text)  # AI 生成的本周概览
    trending_topics = Column(JSON, default=list)  # 热门话题标签
    hot_keywords = Column(JSON, default=list)  # 高频关键词
