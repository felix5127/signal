"""
[INPUT]: 依赖 config, os, httpx
[OUTPUT]: 对外提供 SourceHealthChecker 健康检查服务
[POS]: 业务逻辑层，检查各信号源的依赖和可用性
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.config import config
from app.models.source_config import SOURCE_TYPES


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
    API_ENDPOINTS = {
        "hackernews": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "github": "https://api.github.com/rate_limit",
        "huggingface": "https://huggingface.co/api/models",
        "arxiv": "http://export.arxiv.org/api/query?search_query=all:electron&max_results=1",
        "producthunt": "https://api.producthunt.com/v2/api/graphql",
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
