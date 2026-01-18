"""
[INPUT]: 依赖 services/export_service, database
[OUTPUT]: 对外提供导出 API 端点
[POS]: api/ 的导出路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.export_service import export_service, ExportFormat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["导出"])


# ============================================================
# Pydantic 模型
# ============================================================

class ExportResponse(BaseModel):
    """导出响应 (Notion)"""
    success: bool
    format: str
    filename: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# API 端点
# ============================================================

@router.get("/output/{output_id}")
async def export_output(
    output_id: str,
    format: str = Query("markdown", description="导出格式: markdown, pdf, html, notion"),
    include_sources: bool = Query(True, description="是否包含来源"),
    db: Session = Depends(get_db),
):
    """
    导出研究输出

    支持导出为 Markdown、PDF、HTML 或 Notion。
    """
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

    result = await export_service.export_output(
        db=db,
        output_id=output_id,
        format=export_format,
        include_sources=include_sources,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    # Notion 导出返回 URL
    if export_format == ExportFormat.NOTION:
        return ExportResponse(
            success=True,
            format=result.format.value,
            filename=result.filename,
            url=result.url,
        )

    # 其他格式返回文件
    media_types = {
        ExportFormat.MARKDOWN: "text/markdown",
        ExportFormat.PDF: "application/pdf",
        ExportFormat.HTML: "text/html",
    }

    return Response(
        content=result.content,
        media_type=media_types.get(export_format, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@router.get("/project/{project_id}")
async def export_project(
    project_id: str,
    format: str = Query("markdown", description="导出格式: markdown, html"),
    include_sources: bool = Query(True, description="是否包含来源"),
    db: Session = Depends(get_db),
):
    """
    导出整个项目

    将项目的所有研究输出导出为单个文件。
    """
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

    if export_format not in [ExportFormat.MARKDOWN, ExportFormat.HTML]:
        raise HTTPException(status_code=400, detail="项目导出仅支持 markdown 和 html 格式")

    result = await export_service.export_project(
        db=db,
        project_id=project_id,
        format=export_format,
        include_sources=include_sources,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    media_types = {
        ExportFormat.MARKDOWN: "text/markdown",
        ExportFormat.HTML: "text/html",
    }

    return Response(
        content=result.content,
        media_type=media_types.get(export_format, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@router.get("/formats")
async def list_export_formats():
    """获取支持的导出格式"""
    return {
        "formats": [
            {
                "id": "markdown",
                "name": "Markdown",
                "description": "Markdown 格式，适合文档编辑",
                "extension": ".md",
            },
            {
                "id": "html",
                "name": "HTML",
                "description": "网页格式，可直接浏览",
                "extension": ".html",
            },
            {
                "id": "pdf",
                "name": "PDF",
                "description": "PDF 格式，适合打印分享",
                "extension": ".pdf",
                "note": "需要安装 weasyprint",
            },
            {
                "id": "notion",
                "name": "Notion",
                "description": "导出到 Notion 页面",
                "note": "需要配置 Notion API",
            },
        ],
        "default": "markdown",
    }
