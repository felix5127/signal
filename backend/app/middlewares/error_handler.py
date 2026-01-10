# 全局异常处理中间件
# 统一处理所有异常，避免敏感信息泄露

from typing import Union, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.responses import Response as FastAPIResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
import logging
import traceback
import json

# 配置日志
logger = logging.getLogger(__name__)


# ============================================
# 美化 JSON 响应类
# ============================================
class PrettyJSONResponse(Response):
    """带缩进的 JSON 响应，方便阅读"""

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            indent=2,
            separators=(",", ": "),
        ).encode("utf-8")


# 自定义异常类
class APIException(Exception):
    """API异常基类"""

    def __init__(
        self,
        message: str,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Union[dict, None] = None,
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundException(APIException):
    """资源未找到异常"""

    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class BadRequestException(APIException):
    """错误请求异常"""

    def __init__(self, message: str = "Bad request", details: dict = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class UnauthorizedException(APIException):
    """未授权异常"""

    def __init__(self, message: str = "Unauthorized", details: dict = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenException(APIException):
    """禁止访问异常"""

    def __init__(self, message: str = "Forbidden", details: dict = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class ValidationException(APIException):
    """验证失败异常"""

    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


def create_error_response(
    code: int, message: str, details: dict = None, path: str = None
) -> JSONResponse:
    """创建统一的错误响应"""
    content = {
        "success": False,
        "error": {
            "message": message,
            "code": code,
        }
    }

    if details:
        content["error"]["details"] = details

    if path:
        content["error"]["path"] = path

    return JSONResponse(status_code=code, content=content)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """处理自定义API异常"""
    logger.warning(
        f"API Exception: {exc.code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """处理HTTP异常"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        code=exc.status_code,
        message=str(exc.detail),
        path=request.url.path,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证异常"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"Validation Error: {len(errors)} errors",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        },
    )

    return create_error_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Request validation failed",
        details={"errors": errors},
        path=request.url.path,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    # 记录完整的错误堆栈
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # 开发环境返回详细信息，生产环境隐藏细节
    import os

    debug = os.getenv("DEBUG", "false").lower() == "true"

    if debug:
        # 开发环境：返回完整错误信息
        return create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Internal Server Error: {str(exc)}",
            details={
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
            path=request.url.path,
        )
    else:
        # 生产环境：隐藏敏感信息
        return create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Please try again later.",
            path=request.url.path,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """注册所有异常处理器"""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
