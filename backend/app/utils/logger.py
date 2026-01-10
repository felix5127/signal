# 结构化日志系统
# 使用structlog实现统一的日志记录

import logging
import sys
from typing import Any, Dict
from datetime import datetime
from pathlib import Path

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加应用上下文信息"""
    event_dict["app"] = "signal-hunter"
    event_dict["environment"] = event_dict.get("environment", "development")
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加时间戳"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def rename_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """重命名level字段为severity"""
    event_dict["severity"] = event_dict.pop("level", "info")
    return event_dict


def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """移除颜色消息键（在控制台输出时）"""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(
    level: str = "INFO",
    environment: str = "development",
    log_file: str = None,
    json_logs: bool = False,
):
    """
    配置结构化日志

    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        environment: 环境名称（development, staging, production）
        log_file: 日志文件路径（可选）
        json_logs: 是否输出JSON格式日志（生产环境推荐）
    """

    # 基础处理器列表
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        # 生产环境：JSON格式
        processors.extend([
            rename_level,
            add_app_context,
            structlog.processors.JSONRenderer()
        ])
    else:
        # 开发环境：可读性强的控制台输出
        processors.extend([
            add_app_context,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        ])

    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

        # JSON格式的文件日志
        if json_logs:
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        else:
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=False)
            )

        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    获取logger实例

    Args:
        name: logger名称（通常使用__name__）

    Returns:
        BoundLogger实例
    """
    return structlog.get_logger(name)


# 日志上下文管理器
class LogContext:
    """日志上下文管理器，用于添加临时的日志字段"""

    def __init__(self, **kwargs):
        self.context = kwargs

    def __enter__(self):
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# 便捷函数
def bind_context(**kwargs):
    """绑定日志上下文变量"""
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys):
    """解绑日志上下文变量"""
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context():
    """清除所有日志上下文变量"""
    structlog.contextvars.clear_contextvars()


# API请求日志中间件
async def log_request_middleware(request, call_next):
    """
    记录API请求的中间件

    需要在FastAPI中作为中间件使用
    """
    import time
    from app.utils.logger import get_logger

    logger = get_logger("api.request")

    # 提取请求信息
    request_id = request.headers.get("X-Request-ID", "unknown")
    path = request.url.path
    method = request.method

    # 绑定请求上下文
    bind_context(request_id=request_id, path=path, method=method)

    start_time = time.time()

    logger.info("Request started",
                client=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"))

    try:
        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        logger.info("Request completed",
                   status_code=response.status_code,
                   process_time_ms=round(process_time * 1000, 2))

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response

    except Exception as e:
        # 请求失败
        process_time = time.time() - start_time

        logger.error("Request failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time_ms=round(process_time * 1000, 2))

        raise

    finally:
        # 清除上下文
        clear_context()


# 数据库查询日志
def log_db_query(query: str, params: Dict = None, duration_ms: float = None):
    """记录数据库查询"""
    logger = get_logger("db.query")

    log_data = {
        "query": query[:200],  # 限制长度
    }

    if params:
        log_data["params"] = str(params)

    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)

        # 慢查询告警
        if duration_ms > 1000:
            logger.warning("Slow query detected", **log_data)
        else:
            logger.debug("Query executed", **log_data)
    else:
        logger.debug("Query executed", **log_data)


# 缓存操作日志
def log_cache_operation(operation: str, key: str, hit: bool = None, duration_ms: float = None):
    """记录缓存操作"""
    logger = get_logger("cache")

    log_data = {
        "operation": operation,
        "key": key[:100],  # 限制长度
    }

    if hit is not None:
        log_data["hit"] = hit

    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)

    logger.info("Cache operation", **log_data)


# LLM调用日志
def log_llm_call(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost_usd: float = None,
    duration_ms: float = None,
):
    """记录LLM API调用"""
    logger = get_logger("llm.call")

    log_data = {
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }

    if cost_usd is not None:
        log_data["cost_usd"] = round(cost_usd, 4)

    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)

    logger.info("LLM API call", **log_data)


# 任务执行日志
def log_task_execution(task_name: str, status: str, **kwargs):
    """记录任务执行"""
    logger = get_logger("task")

    log_data = {
        "task": task_name,
        "status": status,
    }

    log_data.update(kwargs)

    if status == "success":
        logger.info("Task completed", **log_data)
    elif status == "failed":
        logger.error("Task failed", **log_data)
    else:
        logger.info("Task status", **log_data)


# 初始化默认配置
def init_default_logging():
    """初始化默认日志配置"""
    import os

    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")

    # 生产环境使用JSON日志
    json_logs = environment == "production"

    configure_logging(
        level=log_level,
        environment=environment,
        log_file=log_file,
        json_logs=json_logs,
    )

    logger = get_logger("app")
    logger.info("Logging initialized",
               environment=environment,
               level=log_level,
               json_logs=json_logs)
