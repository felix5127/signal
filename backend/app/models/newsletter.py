"""
[INPUT]: 依赖 database 的 Base (SQLAlchemy 基类)
[OUTPUT]: 对外提供 Newsletter 模型
[POS]: 数据模型层，周刊记录的 ORM 定义，year+week_number 唯一索引
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Index, JSON
from sqlalchemy.sql import func

from app.database import Base

# 使用 JSON 类型，PostgreSQL 会自动优化，SQLite 使用 TEXT 存储


class Newsletter(Base):
    """
    Newsletter 表模型 - 存储自动生成的周刊

    周刊功能：
    - 每周五自动触发生成
    - 筛选本周 Top 内容
    - 生成 Markdown 格式周刊
    - 与 Resource 表通过 resource_ids 关联

    周刊内容：
    - 本周精选文章摘要
    - 各分类 Top 内容
    - 重要趋势总结
    """

    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ==================== 周刊基础信息 ====================
    title = Column(String(255), nullable=False)  # 周刊标题，如 "Signal 周刊 #12"
    week_number = Column(Integer, nullable=False)  # 年内第几周（1-52）
    year = Column(Integer, nullable=False)  # 年份，如 2026

    # ==================== 周刊内容 ====================
    content = Column(Text)  # Markdown 格式的周刊正文

    # ==================== 关联资源 ====================
    # 存储本期周刊包含的资源ID列表
    # 格式: [1, 2, 3, 4, 5, ...]
    resource_ids = Column(JSON)

    # ==================== 时间戳 ====================
    published_at = Column(DateTime, index=True)  # 发布时间
    created_at = Column(DateTime, default=func.now())  # 创建时间

    # ==================== 复合索引优化 ====================
    __table_args__ = (
        # 按年份和周数唯一查询
        Index("idx_newsletters_year_week", "year", "week_number", unique=True),
    )

    @staticmethod
    def generate_title(year: int, week_number: int) -> str:
        """
        生成周刊标题

        Args:
            year: 年份
            week_number: 周数

        Returns:
            格式化的周刊标题，如 "Signal 周刊 2026年第12周"
        """
        return f"Signal 周刊 {year}年第{week_number}周"

    def __repr__(self):
        return f"<Newsletter(id={self.id}, year={self.year}, week={self.week_number})>"
