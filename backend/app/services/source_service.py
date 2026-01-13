"""
[INPUT]: 依赖 models (SourceRun, SourceConfig, SOURCE_TYPES), config, scrapers/opml_parser
[OUTPUT]: 对外提供 SourceService 信号源管理服务
[POS]: 业务逻辑层，管理信号源状态、采集记录、动态配置
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config import config
from app.models.source_run import SourceRun
from app.models.source_config import SourceConfig, SOURCE_TYPES


class SourceService:
    """信号源管理服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 状态查询 ==========

    def get_all_status(self) -> List[Dict[str, Any]]:
        """
        获取所有信号源的状态概览

        Returns:
            包含每个信号源状态的列表
        """
        results = []

        for source_type in SOURCE_TYPES:
            status = self._get_source_status(source_type)
            results.append(status)

        return results

    def get_source_detail(self, source_type: str) -> Dict[str, Any]:
        """
        获取单个信号源的详细信息

        Args:
            source_type: 信号源类型

        Returns:
            包含配置、最近采集记录、统计信息的字典
        """
        if source_type not in SOURCE_TYPES:
            return {"error": f"Unknown source type: {source_type}"}

        # 获取配置
        db_config = SourceConfig.get_or_create(self.db, source_type)
        yaml_config = self._get_yaml_config(source_type)

        # 获取最近 10 次采集记录
        recent_runs = (
            self.db.query(SourceRun)
            .filter(SourceRun.source_type == source_type)
            .order_by(desc(SourceRun.started_at))
            .limit(10)
            .all()
        )

        # 获取 24h 统计
        stats_24h = self._get_24h_stats(source_type)

        return {
            "source_type": source_type,
            "enabled": db_config.enabled,
            "yaml_config": yaml_config,
            "config_override": db_config.config_override,
            "updated_at": db_config.updated_at.isoformat() if db_config.updated_at else None,
            "recent_runs": [run.to_dict() for run in recent_runs],
            "stats_24h": stats_24h,
        }

    def _get_source_status(self, source_type: str) -> Dict[str, Any]:
        """获取单个信号源的状态摘要"""
        # 获取配置
        db_config = (
            self.db.query(SourceConfig)
            .filter(SourceConfig.source_type == source_type)
            .first()
        )
        enabled = db_config.enabled if db_config else True

        # 获取最近一次采集
        last_run = (
            self.db.query(SourceRun)
            .filter(SourceRun.source_type == source_type)
            .order_by(desc(SourceRun.started_at))
            .first()
        )

        # 获取 24h 统计
        stats_24h = self._get_24h_stats(source_type)

        # 确定健康状态
        health_status = self._determine_health(source_type, enabled, last_run)

        return {
            "source_type": source_type,
            "enabled": enabled,
            "health": health_status,
            "last_run": last_run.to_dict() if last_run else None,
            "stats_24h": stats_24h,
        }

    def _get_24h_stats(self, source_type: str) -> Dict[str, int]:
        """获取最近 24 小时的统计数据"""
        since = datetime.utcnow() - timedelta(hours=24)

        result = (
            self.db.query(
                func.sum(SourceRun.fetched_count).label("fetched"),
                func.sum(SourceRun.saved_count).label("saved"),
                func.count(SourceRun.id).label("run_count"),
            )
            .filter(
                SourceRun.source_type == source_type,
                SourceRun.started_at >= since,
            )
            .first()
        )

        return {
            "fetched": result.fetched or 0,
            "saved": result.saved or 0,
            "run_count": result.run_count or 0,
        }

    def _determine_health(
        self, source_type: str, enabled: bool, last_run: Optional[SourceRun]
    ) -> Dict[str, str]:
        """确定信号源健康状态"""
        if not enabled:
            return {"status": "disabled", "message": "已禁用"}

        if not last_run:
            return {"status": "unknown", "message": "暂无采集记录"}

        # 检查最近一次采集状态
        if last_run.status == "failed":
            return {
                "status": "error",
                "message": last_run.error_message or "采集失败",
            }

        # 检查采集时间
        age = datetime.utcnow() - last_run.started_at
        if age > timedelta(hours=6):
            return {"status": "warning", "message": f"超过 {int(age.total_seconds() / 3600)} 小时未采集"}

        # 检查依赖
        dep_check = self._check_dependencies(source_type)
        if dep_check["status"] != "ok":
            return dep_check

        return {"status": "healthy", "message": "运行正常"}

    def _check_dependencies(self, source_type: str) -> Dict[str, str]:
        """检查信号源的依赖项"""
        # 检查 OPML 文件
        opml_sources = ["twitter", "blog", "podcast", "video"]
        if source_type in opml_sources:
            opml_path = self._get_opml_path(source_type)
            if opml_path and not os.path.exists(opml_path):
                return {"status": "error", "message": f"OPML 文件不存在: {opml_path}"}

        return {"status": "ok", "message": ""}

    def _get_opml_path(self, source_type: str) -> Optional[str]:
        """获取 OPML 文件路径"""
        source_config = self._get_yaml_config(source_type)
        return source_config.get("opml_path") if source_config else None

    def _get_yaml_config(self, source_type: str) -> Dict[str, Any]:
        """从 config.yaml 获取信号源配置"""
        sources = getattr(config, "sources", None)
        if sources:
            return getattr(sources, source_type, {}).__dict__ if hasattr(sources, source_type) else {}
        return {}

    # ========== 配置管理 ==========

    def toggle_source(self, source_type: str) -> Dict[str, Any]:
        """
        切换信号源的启用状态

        Args:
            source_type: 信号源类型

        Returns:
            更新后的配置
        """
        if source_type not in SOURCE_TYPES:
            return {"error": f"Unknown source type: {source_type}"}

        db_config = SourceConfig.get_or_create(self.db, source_type)
        db_config.enabled = not db_config.enabled
        self.db.commit()
        self.db.refresh(db_config)

        return db_config.to_dict()

    def update_config(
        self, source_type: str, config_override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新信号源的配置覆盖

        Args:
            source_type: 信号源类型
            config_override: 要覆盖的配置项

        Returns:
            更新后的配置
        """
        if source_type not in SOURCE_TYPES:
            return {"error": f"Unknown source type: {source_type}"}

        db_config = SourceConfig.get_or_create(self.db, source_type)
        db_config.config_override = config_override
        self.db.commit()
        self.db.refresh(db_config)

        return db_config.to_dict()

    # ========== 采集记录 ==========

    def get_runs(
        self,
        source_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        获取采集历史记录

        Args:
            source_type: 信号源类型（可选，不传则返回所有）
            page: 页码
            page_size: 每页数量

        Returns:
            分页的采集记录列表
        """
        query = self.db.query(SourceRun)

        if source_type:
            if source_type not in SOURCE_TYPES:
                return {"error": f"Unknown source type: {source_type}"}
            query = query.filter(SourceRun.source_type == source_type)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        runs = (
            query.order_by(desc(SourceRun.started_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "items": [run.to_dict() for run in runs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    def record_run(
        self,
        source_type: str,
        status: str = "success",
        fetched_count: int = 0,
        rule_filtered_count: int = 0,
        dedup_filtered_count: int = 0,
        llm_filtered_count: int = 0,
        saved_count: int = 0,
        error_message: Optional[str] = None,
        error_details: Optional[Dict] = None,
        started_at: Optional[datetime] = None,
    ) -> SourceRun:
        """
        记录一次采集运行

        Args:
            source_type: 信号源类型
            status: 状态 (success/failed/partial)
            fetched_count: 抓取数量
            rule_filtered_count: 规则过滤后剩余
            dedup_filtered_count: 去重后剩余
            llm_filtered_count: LLM 过滤后剩余
            saved_count: 存储数量
            error_message: 错误信息
            error_details: 错误详情
            started_at: 开始时间（不传则使用当前时间）

        Returns:
            创建的 SourceRun 记录
        """
        run = SourceRun(
            source_type=source_type,
            started_at=started_at or datetime.utcnow(),
            finished_at=datetime.utcnow(),
            status=status,
            fetched_count=fetched_count,
            rule_filtered_count=rule_filtered_count,
            dedup_filtered_count=dedup_filtered_count,
            llm_filtered_count=llm_filtered_count,
            saved_count=saved_count,
            error_message=error_message,
            error_details=error_details,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    # ========== Feed 管理 ==========

    def get_feeds(self, source_type: str) -> Dict[str, Any]:
        """
        获取 OPML 中的 feed 列表

        Args:
            source_type: 信号源类型

        Returns:
            feed 列表
        """
        opml_sources = ["twitter", "blog", "podcast", "video"]
        if source_type not in opml_sources:
            return {"error": f"Source type {source_type} does not use OPML"}

        opml_path = self._get_opml_path(source_type)
        if not opml_path:
            return {"error": "OPML path not configured"}

        if not os.path.exists(opml_path):
            return {"error": f"OPML file not found: {opml_path}"}

        try:
            from app.scrapers.opml_parser import parse_opml

            feeds = parse_opml(opml_path)
            return {
                "source_type": source_type,
                "opml_path": opml_path,
                "feed_count": len(feeds),
                "feeds": feeds,
            }
        except Exception as e:
            return {"error": f"Failed to parse OPML: {str(e)}"}

    # ========== 聚合漏斗 ==========

    def get_funnel_stats(self, hours: int = 24) -> Dict[str, int]:
        """
        获取聚合的采集漏斗统计

        Args:
            hours: 统计时间范围（小时）

        Returns:
            漏斗各阶段的总数
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        result = (
            self.db.query(
                func.sum(SourceRun.fetched_count).label("fetched"),
                func.sum(SourceRun.rule_filtered_count).label("rule_filtered"),
                func.sum(SourceRun.dedup_filtered_count).label("dedup_filtered"),
                func.sum(SourceRun.llm_filtered_count).label("llm_filtered"),
                func.sum(SourceRun.saved_count).label("saved"),
            )
            .filter(SourceRun.started_at >= since)
            .first()
        )

        return {
            "fetched": result.fetched or 0,
            "rule_filtered": result.rule_filtered or 0,
            "dedup_filtered": result.dedup_filtered or 0,
            "llm_filtered": result.llm_filtered or 0,
            "saved": result.saved or 0,
            "hours": hours,
        }
