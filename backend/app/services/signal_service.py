# Signal服务层
# 处理信号相关的业务逻辑

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.signal import Signal
from app.middlewares.validation import SignalFilter, validate_input


class SignalService:
    """信号服务类"""

    def __init__(self, db: Session):
        self.db = db

    def get_signals(
        self,
        filters: SignalFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取信号列表（带筛选和分页）

        Args:
            filters: 筛选条件
            limit: 每页数量
            offset: 偏移量

        Returns:
            (信号列表, 总数)
        """
        # 构建基础查询
        query = self.db.query(Signal).filter(Signal.status == "published")

        # 应用筛选条件
        query = self._apply_filters(query, filters)

        # 获取总数（优化：使用子查询避免重复）
        # SQLAlchemy 2.0+ 要求位置参数而非列表
        total_query = query.statement.with_only_columns(func.count()).order_by(None)
        total = self.db.execute(total_query).scalar()

        # 排序
        query = self._apply_sorting(query, filters.sort_by)

        # 分页
        items = query.offset(offset).limit(limit).all()

        # 转换为字典
        items_dict = [self._signal_to_dict(item) for item in items]

        return items_dict, total

    def get_signal_by_id(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个信号

        Args:
            signal_id: 信号ID

        Returns:
            信号字典，如果不存在返回None
        """
        signal = self.db.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            return None

        return self._signal_to_dict(signal, include_all_fields=True)

    def get_signal_stats(self) -> Dict[str, Any]:
        """
        获取信号统计数据

        Returns:
            统计数据字典
        """
        # 总信号数
        total_signals = (
            self.db.query(Signal).filter(Signal.status == "published").count()
        )

        # 按来源统计
        by_source = (
            self.db.query(Signal.source, func.count(Signal.id).label("count"))
            .filter(Signal.status == "published")
            .group_by(Signal.source)
            .all()
        )
        source_stats = {row.source: row.count for row in by_source}

        # 按分类统计
        by_category = (
            self.db.query(Signal.category, func.count(Signal.id).label("count"))
            .filter(Signal.status == "published")
            .group_by(Signal.category)
            .all()
        )
        category_stats = {row.category: row.count for row in by_category}

        # 按评分统计
        by_score = (
            self.db.query(
                Signal.final_score, func.count(Signal.id).label("count")
            )
            .filter(Signal.status == "published")
            .group_by(Signal.final_score)
            .order_by(Signal.final_score.desc())
            .all()
        )
        score_stats = {row.final_score: row.count for row in by_score}

        # 平均评分
        avg_scores = (
            self.db.query(
                func.avg(Signal.heat_score).label("avg_heat"),
                func.avg(Signal.quality_score).label("avg_quality"),
                func.avg(Signal.final_score).label("avg_final"),
            )
            .filter(Signal.status == "published")
            .first()
        )

        # 最新更新时间
        latest_signal = (
            self.db.query(Signal)
            .filter(Signal.status == "published")
            .order_by(Signal.created_at.desc())
            .first()
        )

        return {
            "total_signals": total_signals,
            "by_source": source_stats,
            "by_category": category_stats,
            "by_score": score_stats,
            "average_scores": {
                "heat": round(avg_scores.avg_heat, 2) if avg_scores.avg_heat else 0,
                "quality": (
                    round(avg_scores.avg_quality, 2) if avg_scores.avg_quality else 0
                ),
                "final": (
                    round(avg_scores.avg_final, 2) if avg_scores.avg_final else 0
                ),
            },
            "latest_update": (
                latest_signal.created_at.isoformat() if latest_signal else None
            ),
        }

    def _apply_filters(self, query, filters: SignalFilter):
        """应用筛选条件到查询"""
        if filters.min_score:
            query = query.filter(Signal.final_score >= filters.min_score)

        # 数据源筛选（支持单个或多个）
        if filters.sources:
            source_list = [s.strip() for s in filters.sources.split(",") if s.strip()]
            if source_list:
                query = query.filter(Signal.source.in_(source_list))
        elif filters.source:
            query = query.filter(Signal.source == filters.source)

        if filters.category:
            query = query.filter(Signal.category == filters.category)

        if filters.search:
            # 搜索标题或摘要
            search_pattern = f"%{filters.search}%"
            query = query.filter(
                (Signal.title.ilike(search_pattern)) | (Signal.summary.ilike(search_pattern))
            )

        return query

    def _apply_sorting(self, query, sort_by: str):
        """应用排序到查询"""
        if sort_by == "final_score":
            return query.order_by(Signal.final_score.desc(), Signal.created_at.desc())
        else:
            return query.order_by(Signal.created_at.desc())

    def _signal_to_dict(self, signal: Signal, include_all_fields: bool = False) -> Dict[str, Any]:
        """
        将Signal对象转换为字典

        Args:
            signal: Signal模型实例
            include_all_fields: 是否包含所有字段（包括详情字段）

        Returns:
            信号字典
        """
        # 安全解析 source_metadata
        metadata = {}
        if signal.source_metadata:
            try:
                metadata = json.loads(signal.source_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        base_dict = {
            "id": signal.id,
            "source": signal.source,
            "title": signal.title,
            "url": signal.url,
            "one_liner": signal.one_liner,
            "summary": signal.summary,
            "final_score": signal.final_score,
            "heat_score": signal.heat_score,
            "quality_score": signal.quality_score,
            "category": signal.category,
            "tags": signal.tags.split(",") if signal.tags else [],
            "source_metadata": metadata,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
        }

        # 如果需要包含所有字段（详情页）
        if include_all_fields:
            base_dict.update({
                "matched_conditions": (
                    signal.matched_conditions.split(",")
                    if signal.matched_conditions
                    else []
                ),
                "source_created_at": (
                    signal.source_created_at.isoformat()
                    if signal.source_created_at
                    else None
                ),
            })

        return base_dict
