"""
[INPUT]: 依赖 config, os, httpx, database (SessionLocal), models (SourceRun)
[OUTPUT]: 对外提供 SourceHealthChecker 健康检查服务
[POS]: 业务逻辑层，检查各信号源的依赖和可用性 + RSS 可达性 + 历史健康评估
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.config import config
from app.models.source_config import SOURCE_TYPES

logger = structlog.get_logger("source_health")


@dataclass
class HealthCheck:
    """单项健康检查结果"""
    name: str
    status: str  # ok/warning/error
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class SourceHealth:
    """信号源健康状态"""
    source_type: str
    status: str  # healthy/warning/error
    message: str
    checks: List[HealthCheck]
    checked_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "status": self.status,
            "message": self.message,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
            "checked_at": self.checked_at.isoformat(),
        }


class SourceHealthChecker:
    """信号源健康检查器"""

    # API 端点（用于连通性检测）
    # 已移除: hackernews, github, huggingface, arxiv, producthunt (scraper 代码已删除)
    API_ENDPOINTS = {
        # twitter, blog, podcast 使用 RSS/OPML，不需要 API 检测
    }

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def check_all(self) -> Dict[str, SourceHealth]:
        """检查所有信号源的健康状态"""
        results = {}
        for source_type in SOURCE_TYPES:
            results[source_type] = await self.check_source(source_type)
        return results

    async def check_source(self, source_type: str) -> SourceHealth:
        """检查单个信号源的健康状态"""
        checks = []

        # 1. 检查配置
        config_check = self._check_config(source_type)
        checks.append(config_check)

        # 2. 检查依赖（OPML 文件等）
        dep_check = self._check_dependencies(source_type)
        if dep_check:
            checks.append(dep_check)

        # 3. 检查 API 连通性（仅对需要的源）
        if source_type in self.API_ENDPOINTS:
            api_check = await self._check_api(source_type)
            checks.append(api_check)

        # 4. RSS Feed 可达性探测 (采样检查)
        feed_check = await self._check_feed_reachability(source_type)
        if feed_check:
            checks.append(feed_check)

        # 5. 基于历史运行记录的健康评估
        history_check = self._check_source_history(source_type)
        if history_check:
            checks.append(history_check)

        # 汇总状态
        status, message = self._aggregate_status(checks)

        return SourceHealth(
            source_type=source_type,
            status=status,
            message=message,
            checks=checks,
            checked_at=datetime.utcnow(),
        )

    def _check_config(self, source_type: str) -> HealthCheck:
        """检查配置是否存在"""
        sources = getattr(config, "sources", None)
        if not sources:
            return HealthCheck(
                name="config",
                status="error",
                message="sources 配置不存在",
            )

        source_config = getattr(sources, source_type, None)
        if not source_config:
            return HealthCheck(
                name="config",
                status="warning",
                message=f"{source_type} 配置不存在",
            )

        enabled = getattr(source_config, "enabled", True)
        if not enabled:
            return HealthCheck(
                name="config",
                status="warning",
                message="已在配置中禁用",
            )

        return HealthCheck(
            name="config",
            status="ok",
            message="配置正常",
        )

    def _check_dependencies(self, source_type: str) -> Optional[HealthCheck]:
        """检查依赖项（OPML 文件等）"""
        opml_sources = ["twitter", "blog", "podcast", "video"]
        if source_type not in opml_sources:
            return None

        sources = getattr(config, "sources", None)
        if not sources:
            return HealthCheck(
                name="opml",
                status="error",
                message="无法获取配置",
            )

        source_config = getattr(sources, source_type, None)
        if not source_config:
            return HealthCheck(
                name="opml",
                status="error",
                message="配置不存在",
            )

        opml_path = getattr(source_config, "opml_path", None)
        if not opml_path:
            return HealthCheck(
                name="opml",
                status="error",
                message="OPML 路径未配置",
            )

        if not os.path.exists(opml_path):
            return HealthCheck(
                name="opml",
                status="error",
                message=f"OPML 文件不存在: {opml_path}",
                details={"path": opml_path},
            )

        # 检查文件大小（确保非空）
        try:
            size = os.path.getsize(opml_path)
            if size == 0:
                return HealthCheck(
                    name="opml",
                    status="error",
                    message="OPML 文件为空",
                    details={"path": opml_path, "size": size},
                )

            # 尝试解析 feed 数量
            try:
                from app.scrapers.opml_parser import parse_opml
                feeds = parse_opml(opml_path)
                feed_count = len(feeds)
                return HealthCheck(
                    name="opml",
                    status="ok",
                    message=f"包含 {feed_count} 个 feed",
                    details={"path": opml_path, "feed_count": feed_count},
                )
            except Exception as e:
                return HealthCheck(
                    name="opml",
                    status="warning",
                    message=f"OPML 解析警告: {str(e)}",
                    details={"path": opml_path},
                )

        except OSError as e:
            return HealthCheck(
                name="opml",
                status="error",
                message=f"文件访问错误: {str(e)}",
                details={"path": opml_path},
            )

    async def _check_api(self, source_type: str) -> HealthCheck:
        """检查 API 连通性"""
        url = self.API_ENDPOINTS.get(source_type)
        if not url:
            return HealthCheck(
                name="api",
                status="ok",
                message="无需 API 检查",
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return HealthCheck(
                        name="api",
                        status="ok",
                        message="API 连接正常",
                        details={"status_code": response.status_code},
                    )
                elif response.status_code == 403:
                    # GitHub 可能需要 Token
                    if source_type == "github":
                        return HealthCheck(
                            name="api",
                            status="warning",
                            message="API 限流或需要 Token",
                            details={"status_code": response.status_code},
                        )
                    return HealthCheck(
                        name="api",
                        status="warning",
                        message=f"API 返回 {response.status_code}",
                        details={"status_code": response.status_code},
                    )
                else:
                    return HealthCheck(
                        name="api",
                        status="warning",
                        message=f"API 返回 {response.status_code}",
                        details={"status_code": response.status_code},
                    )

        except httpx.TimeoutException:
            return HealthCheck(
                name="api",
                status="error",
                message="API 连接超时",
                details={"timeout": self.timeout},
            )
        except httpx.ConnectError:
            return HealthCheck(
                name="api",
                status="error",
                message="无法连接到 API",
            )
        except Exception as e:
            return HealthCheck(
                name="api",
                status="error",
                message=f"API 检查失败: {str(e)}",
            )

    # ============================================================
    # RSS Feed 可达性探测
    # ============================================================

    async def _check_feed_reachability(self, source_type: str) -> Optional[HealthCheck]:
        """
        抽样检查 RSS Feed 是否可达 (HTTP HEAD)

        从 OPML 中取前 3 个 feed URL 做 HEAD 请求，
        统计可达数量来判断整体健康状况。
        """
        opml_sources = ["twitter", "blog", "podcast", "video"]
        if source_type not in opml_sources:
            return None

        # 获取 feed 列表
        sources_cfg = getattr(config, "sources", None)
        if not sources_cfg:
            return None
        source_cfg = getattr(sources_cfg, source_type, None)
        if not source_cfg:
            return None
        opml_path = getattr(source_cfg, "opml_path", None)
        if not opml_path or not os.path.exists(opml_path):
            return None  # OPML 检查已在 _check_dependencies 中处理

        try:
            from app.scrapers.opml_parser import parse_opml
            feeds = parse_opml(opml_path)
        except Exception:
            return None

        if not feeds:
            return None

        # 抽样前 3 个 feed URL
        sample_feeds = feeds[:3]
        reachable = 0
        unreachable_urls = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for feed in sample_feeds:
                url = feed.get("xmlUrl") or feed.get("url", "")
                if not url:
                    continue
                try:
                    resp = await client.head(url, follow_redirects=True)
                    if resp.status_code < 400:
                        reachable += 1
                    else:
                        unreachable_urls.append(url)
                except Exception:
                    unreachable_urls.append(url)

        total = len(sample_feeds)
        if total == 0:
            return None

        if reachable == total:
            return HealthCheck(
                name="feed_reachability",
                status="ok",
                message=f"抽样 {total} 个 Feed 全部可达",
                details={"sampled": total, "reachable": reachable},
            )
        elif reachable > 0:
            return HealthCheck(
                name="feed_reachability",
                status="warning",
                message=f"抽样 {total} 个 Feed，{total - reachable} 个不可达",
                details={
                    "sampled": total,
                    "reachable": reachable,
                    "unreachable": unreachable_urls,
                },
            )
        else:
            return HealthCheck(
                name="feed_reachability",
                status="error",
                message=f"抽样 {total} 个 Feed 全部不可达",
                details={"sampled": total, "unreachable": unreachable_urls},
            )

    # ============================================================
    # 基于历史的健康评估
    # ============================================================

    def _check_source_history(
        self,
        source_type: str,
        hours: int = 24,
    ) -> Optional[HealthCheck]:
        """
        基于最近 N 小时的 SourceRun 记录评估健康度

        规则:
        - 成功率 >= 80% → ok
        - 成功率 >= 50% → warning
        - 成功率 < 50%  → error
        - 连续 3 次失败 → error (告警阈值)
        - 无记录         → 跳过 (返回 None)
        """
        try:
            from app.database import SessionLocal
            from app.models.source_run import SourceRun
        except Exception:
            return None

        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            runs = (
                db.query(SourceRun)
                .filter(
                    SourceRun.source_type == source_type,
                    SourceRun.started_at >= since,
                )
                .order_by(SourceRun.started_at.desc())
                .all()
            )

            if not runs:
                return None  # 无历史记录，跳过此检查

            total = len(runs)
            success_count = sum(1 for r in runs if r.status == "success")
            failed_count = sum(1 for r in runs if r.status == "failed")
            success_rate = success_count / total

            # 检查连续失败 (告警阈值: 3 次)
            consecutive_failures = 0
            for r in runs:
                if r.status == "failed":
                    consecutive_failures += 1
                else:
                    break

            details = {
                "total_runs": total,
                "success": success_count,
                "failed": failed_count,
                "success_rate": round(success_rate * 100, 1),
                "consecutive_failures": consecutive_failures,
                "hours": hours,
            }

            # 连续 3 次失败 → 立即告警
            if consecutive_failures >= 3:
                return HealthCheck(
                    name="history",
                    status="error",
                    message=f"连续 {consecutive_failures} 次采集失败",
                    details=details,
                )

            if success_rate >= 0.8:
                return HealthCheck(
                    name="history",
                    status="ok",
                    message=f"近 {hours}h 成功率 {details['success_rate']}%",
                    details=details,
                )
            elif success_rate >= 0.5:
                return HealthCheck(
                    name="history",
                    status="warning",
                    message=f"近 {hours}h 成功率 {details['success_rate']}%，需关注",
                    details=details,
                )
            else:
                return HealthCheck(
                    name="history",
                    status="error",
                    message=f"近 {hours}h 成功率 {details['success_rate']}%，严重异常",
                    details=details,
                )
        except Exception as e:
            logger.warning("source_health.history.error",
                           source_type=source_type, error=str(e))
            return None
        finally:
            db.close()

    def _aggregate_status(self, checks: List[HealthCheck]) -> tuple[str, str]:
        """汇总检查结果"""
        has_error = any(c.status == "error" for c in checks)
        has_warning = any(c.status == "warning" for c in checks)

        if has_error:
            error_checks = [c for c in checks if c.status == "error"]
            return "error", error_checks[0].message
        elif has_warning:
            warning_checks = [c for c in checks if c.status == "warning"]
            return "warning", warning_checks[0].message
        else:
            return "healthy", "运行正常"


# 全局单例
health_checker = SourceHealthChecker()
