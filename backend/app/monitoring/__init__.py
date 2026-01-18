"""
[INPUT]: 依赖 sentry_sdk, logging, os
[OUTPUT]: 对外提供监控和日志配置
[POS]: 监控配置模块入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Sentry 集成
# ============================================================

def init_sentry():
    """
    初始化 Sentry 错误追踪

    需要环境变量:
    - SENTRY_DSN: Sentry 数据源名称
    - ENVIRONMENT: 运行环境 (development/staging/production)
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1,  # 10% 性能追踪
            profiles_sample_rate=0.1,  # 10% 性能分析
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            # 敏感信息过滤
            before_send=_filter_sensitive_data,
        )

        logger.info(f"Sentry initialized with environment: {os.getenv('ENVIRONMENT')}")

    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _filter_sensitive_data(event, hint):
    """过滤敏感数据"""
    # 过滤请求头中的敏感信息
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[FILTERED]"

    return event


# ============================================================
# LangSmith 集成 (Agent 追踪)
# ============================================================

def init_langsmith():
    """
    初始化 LangSmith Agent 追踪

    需要环境变量:
    - LANGCHAIN_TRACING_V2: true/false
    - LANGCHAIN_API_KEY: LangSmith API Key
    - LANGCHAIN_PROJECT: 项目名称
    """
    langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    if not langsmith_enabled:
        logger.info("LangSmith tracing not enabled")
        return

    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.warning("LANGCHAIN_API_KEY not set, LangSmith tracing disabled")
        return

    project = os.getenv("LANGCHAIN_PROJECT", "signal-hunter")

    logger.info(f"LangSmith tracing enabled for project: {project}")


# ============================================================
# 日志配置
# ============================================================

def configure_logging(
    level: str = "INFO",
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    json_format: bool = False,
):
    """
    配置日志系统

    Args:
        level: 日志级别
        format: 日志格式
        json_format: 是否使用 JSON 格式 (适合日志收集)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if json_format:
        try:
            import json_log_formatter

            formatter = json_log_formatter.JSONFormatter()
        except ImportError:
            logger.warning("json-log-formatter not installed, using default format")
            formatter = logging.Formatter(format)
    else:
        formatter = logging.Formatter(format)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 降低第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.info(f"Logging configured with level: {level}")


# ============================================================
# 健康检查
# ============================================================

class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.checks = {}

    def register(self, name: str, check_func):
        """注册健康检查"""
        self.checks[name] = check_func

    async def check_all(self) -> dict:
        """执行所有健康检查"""
        results = {}
        overall_healthy = True

        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()

                results[name] = {"status": "healthy", "details": result}
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
        }


health_checker = HealthChecker()


# ============================================================
# 初始化
# ============================================================

def init_monitoring():
    """初始化所有监控组件"""
    configure_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        json_format=os.getenv("LOG_FORMAT") == "json",
    )
    init_sentry()
    init_langsmith()

    logger.info("Monitoring initialized")


import asyncio
