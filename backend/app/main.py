"""
[INPUT]: 依赖 api/* 的所有路由 (含 admin/*, auth), middlewares 的错误处理, startup 的事件注册
[OUTPUT]: 对外提供 app (FastAPI 应用实例)
[POS]: FastAPI 应用入口，负责创建应用、注册路由、配置中间件
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入中间件
from app.middlewares.error_handler import register_exception_handlers, PrettyJSONResponse

# 导入API路由
from app.api.digest import router as digest_router
from app.api.resources import router as resources_router
from app.api.feeds import router as feeds_router
from app.api.sources import router as sources_router
from app.api.signals import router as signals_router
from app.api.stats import router as stats_router
from app.api.newsletters import router as newsletters_router
from app.api.tasks import router as tasks_router

from app.api.auth import router as auth_router

# 导入 Admin API 路由
from app.api.admin.review import router as admin_review_router
from app.api.admin.sources import router as admin_sources_router
from app.api.admin.prompts import router as admin_prompts_router
from app.api.admin.stats import router as admin_stats_router

# 导入启动事件注册
from app.startup import register_startup_events


# ============================================================
# 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="Signal API",
    description="面向超级个体的技术情报分析系统",
    version="0.2.0",
    default_response_class=PrettyJSONResponse,
)

# 注册全局异常处理
register_exception_handlers(app)

# 注册启动/关闭事件
register_startup_events(app)


# ============================================================
# 注册 API 路由
# ============================================================

app.include_router(digest_router, prefix="/api", tags=["digest"])
app.include_router(resources_router, prefix="/api", tags=["resources"])
app.include_router(feeds_router, prefix="/api/feeds", tags=["feeds"])
app.include_router(sources_router, prefix="/api/sources", tags=["sources"])
app.include_router(signals_router, prefix="/api", tags=["signals"])
app.include_router(stats_router, prefix="/api", tags=["stats"])
app.include_router(newsletters_router, prefix="/api", tags=["newsletters"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(auth_router, prefix="/api", tags=["auth"])

# Admin API 路由
app.include_router(admin_review_router, prefix="/api/admin/review", tags=["admin-review"])
app.include_router(admin_sources_router, prefix="/api/admin/sources", tags=["admin-sources"])
app.include_router(admin_prompts_router, prefix="/api/admin/prompts", tags=["admin-prompts"])
app.include_router(admin_stats_router, prefix="/api/admin/stats", tags=["admin-stats"])


# ============================================================
# CORS 配置
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
        "https://signal.felixwithai.com",
        "https://felixwithai.com",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 基础端点
# ============================================================

@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "success": True,
        "message": "Welcome to Signal API",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# 启动应用
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
