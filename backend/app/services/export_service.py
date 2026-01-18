"""
[INPUT]: 依赖 models/research, services/storage_service
[OUTPUT]: 对外提供导出服务 (Markdown/PDF/Notion)
[POS]: services/ 的导出服务，被 api/export.py 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import io
import logging
import tempfile
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.research import ResearchProject, ResearchOutput, ResearchSource

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class ExportFormat(str, Enum):
    """导出格式"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    NOTION = "notion"


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    format: ExportFormat
    filename: str
    content: Optional[bytes] = None
    url: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# 导出服务
# ============================================================

class ExportService:
    """
    导出服务

    功能:
    - 导出研究输出为 Markdown
    - 导出研究输出为 PDF (需要 weasyprint/puppeteer)
    - 导出研究输出为 HTML
    - 导出研究输出到 Notion (需要 Notion API)

    使用示例:
    ```python
    service = ExportService()

    result = await service.export_output(
        output_id="xxx",
        format=ExportFormat.MARKDOWN,
    )

    if result.success:
        with open(result.filename, "wb") as f:
            f.write(result.content)
    ```
    """

    def __init__(self):
        """初始化服务"""
        pass

    async def export_output(
        self,
        db: Session,
        output_id: str,
        format: ExportFormat,
        include_sources: bool = True,
    ) -> ExportResult:
        """
        导出研究输出

        Args:
            db: 数据库会话
            output_id: 输出 ID
            format: 导出格式
            include_sources: 是否包含来源

        Returns:
            导出结果
        """
        # 获取研究输出
        output = db.query(ResearchOutput).filter(ResearchOutput.id == output_id).first()
        if not output:
            return ExportResult(
                success=False,
                format=format,
                filename="",
                error="研究输出不存在",
            )

        # 获取项目信息
        project = db.query(ResearchProject).filter(ResearchProject.id == output.project_id).first()

        try:
            if format == ExportFormat.MARKDOWN:
                return await self._export_markdown(output, project, include_sources)
            elif format == ExportFormat.PDF:
                return await self._export_pdf(output, project, include_sources)
            elif format == ExportFormat.HTML:
                return await self._export_html(output, project, include_sources)
            elif format == ExportFormat.NOTION:
                return await self._export_notion(output, project, include_sources)
            else:
                return ExportResult(
                    success=False,
                    format=format,
                    filename="",
                    error=f"不支持的格式: {format}",
                )
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ExportResult(
                success=False,
                format=format,
                filename="",
                error=str(e),
            )

    async def export_project(
        self,
        db: Session,
        project_id: str,
        format: ExportFormat,
        include_sources: bool = True,
    ) -> ExportResult:
        """
        导出整个项目

        Args:
            db: 数据库会话
            project_id: 项目 ID
            format: 导出格式
            include_sources: 是否包含来源

        Returns:
            导出结果
        """
        # 获取项目
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            return ExportResult(
                success=False,
                format=format,
                filename="",
                error="项目不存在",
            )

        # 获取所有输出
        outputs = db.query(ResearchOutput).filter(
            ResearchOutput.project_id == project_id
        ).order_by(ResearchOutput.created_at).all()

        try:
            if format == ExportFormat.MARKDOWN:
                return await self._export_project_markdown(project, outputs, include_sources)
            elif format == ExportFormat.HTML:
                return await self._export_project_html(project, outputs, include_sources)
            else:
                return ExportResult(
                    success=False,
                    format=format,
                    filename="",
                    error=f"项目导出暂不支持格式: {format}",
                )
        except Exception as e:
            logger.error(f"Export project failed: {e}")
            return ExportResult(
                success=False,
                format=format,
                filename="",
                error=str(e),
            )

    # ============================================================
    # Markdown 导出
    # ============================================================

    async def _export_markdown(
        self,
        output: ResearchOutput,
        project: Optional[ResearchProject],
        include_sources: bool,
    ) -> ExportResult:
        """导出为 Markdown"""
        lines = []

        # 标题
        lines.append(f"# {output.title or '研究报告'}")
        lines.append("")

        # 元信息
        lines.append("> **项目**: " + (project.name if project else "未知"))
        lines.append(f"> **生成时间**: {output.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"> **类型**: {output.output_type}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 内容
        if output.content:
            lines.append(output.content)
            lines.append("")

        # 来源
        if include_sources and output.extra_metadata and output.extra_metadata.get("sources"):
            lines.append("---")
            lines.append("")
            lines.append("## 参考来源")
            lines.append("")
            for idx, source in enumerate(output.extra_metadata["sources"], 1):
                lines.append(f"{idx}. {source}")
            lines.append("")

        content = "\n".join(lines)
        filename = self._generate_filename(output.title or "report", "md")

        return ExportResult(
            success=True,
            format=ExportFormat.MARKDOWN,
            filename=filename,
            content=content.encode("utf-8"),
        )

    async def _export_project_markdown(
        self,
        project: ResearchProject,
        outputs: List[ResearchOutput],
        include_sources: bool,
    ) -> ExportResult:
        """导出项目为 Markdown"""
        lines = []

        # 项目标题
        lines.append(f"# {project.name}")
        lines.append("")
        if project.description:
            lines.append(project.description)
            lines.append("")
        lines.append(f"> **创建时间**: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"> **状态**: {project.status}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 所有输出
        for idx, output in enumerate(outputs, 1):
            lines.append(f"## {idx}. {output.title or '研究输出'}")
            lines.append("")
            lines.append(f"*{output.created_at.strftime('%Y-%m-%d %H:%M')}*")
            lines.append("")
            if output.content:
                lines.append(output.content)
                lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)
        filename = self._generate_filename(project.name, "md")

        return ExportResult(
            success=True,
            format=ExportFormat.MARKDOWN,
            filename=filename,
            content=content.encode("utf-8"),
        )

    # ============================================================
    # HTML 导出
    # ============================================================

    async def _export_html(
        self,
        output: ResearchOutput,
        project: Optional[ResearchProject],
        include_sources: bool,
    ) -> ExportResult:
        """导出为 HTML"""
        import markdown

        # 先导出为 Markdown
        md_result = await self._export_markdown(output, project, include_sources)
        if not md_result.success:
            return md_result

        md_content = md_result.content.decode("utf-8")

        # 转换为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "codehilite", "toc"],
        )

        # 包装为完整 HTML
        full_html = self._wrap_html(output.title or "研究报告", html_content)

        filename = self._generate_filename(output.title or "report", "html")

        return ExportResult(
            success=True,
            format=ExportFormat.HTML,
            filename=filename,
            content=full_html.encode("utf-8"),
        )

    async def _export_project_html(
        self,
        project: ResearchProject,
        outputs: List[ResearchOutput],
        include_sources: bool,
    ) -> ExportResult:
        """导出项目为 HTML"""
        import markdown

        # 先导出为 Markdown
        md_result = await self._export_project_markdown(project, outputs, include_sources)
        if not md_result.success:
            return md_result

        md_content = md_result.content.decode("utf-8")

        # 转换为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "codehilite", "toc"],
        )

        # 包装为完整 HTML
        full_html = self._wrap_html(project.name, html_content)

        filename = self._generate_filename(project.name, "html")

        return ExportResult(
            success=True,
            format=ExportFormat.HTML,
            filename=filename,
            content=full_html.encode("utf-8"),
        )

    def _wrap_html(self, title: str, body_content: str) -> str:
        """包装为完整 HTML 文档"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.8;
            color: #333;
        }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #2a2a2a; margin-top: 40px; }}
        h3 {{ color: #3a3a3a; }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 20px 0;
            padding: 10px 20px;
            background: #f9f9f9;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 40px 0;
        }}
        a {{ color: #6366f1; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

    # ============================================================
    # PDF 导出
    # ============================================================

    async def _export_pdf(
        self,
        output: ResearchOutput,
        project: Optional[ResearchProject],
        include_sources: bool,
    ) -> ExportResult:
        """导出为 PDF"""
        # 先导出为 HTML
        html_result = await self._export_html(output, project, include_sources)
        if not html_result.success:
            return html_result

        try:
            # 尝试使用 weasyprint
            from weasyprint import HTML

            html_content = html_result.content.decode("utf-8")
            pdf_bytes = HTML(string=html_content).write_pdf()

            filename = self._generate_filename(output.title or "report", "pdf")

            return ExportResult(
                success=True,
                format=ExportFormat.PDF,
                filename=filename,
                content=pdf_bytes,
            )

        except ImportError:
            logger.warning("weasyprint not installed, PDF export unavailable")
            return ExportResult(
                success=False,
                format=ExportFormat.PDF,
                filename="",
                error="PDF 导出需要安装 weasyprint: pip install weasyprint",
            )
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return ExportResult(
                success=False,
                format=ExportFormat.PDF,
                filename="",
                error=str(e),
            )

    # ============================================================
    # Notion 导出
    # ============================================================

    async def _export_notion(
        self,
        output: ResearchOutput,
        project: Optional[ResearchProject],
        include_sources: bool,
    ) -> ExportResult:
        """导出到 Notion"""
        import os

        notion_token = os.getenv("NOTION_API_KEY")
        notion_database_id = os.getenv("NOTION_DATABASE_ID")

        if not notion_token or not notion_database_id:
            return ExportResult(
                success=False,
                format=ExportFormat.NOTION,
                filename="",
                error="请配置 NOTION_API_KEY 和 NOTION_DATABASE_ID 环境变量",
            )

        try:
            import httpx

            # 构建 Notion 页面块
            blocks = self._content_to_notion_blocks(output.content or "")

            # 创建页面
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers={
                        "Authorization": f"Bearer {notion_token}",
                        "Content-Type": "application/json",
                        "Notion-Version": "2022-06-28",
                    },
                    json={
                        "parent": {"database_id": notion_database_id},
                        "properties": {
                            "title": {
                                "title": [
                                    {"text": {"content": output.title or "研究报告"}}
                                ]
                            },
                        },
                        "children": blocks[:100],  # Notion 限制 100 个块
                    },
                )

                if response.status_code == 200:
                    page_data = response.json()
                    return ExportResult(
                        success=True,
                        format=ExportFormat.NOTION,
                        filename=output.title or "report",
                        url=page_data.get("url"),
                    )
                else:
                    return ExportResult(
                        success=False,
                        format=ExportFormat.NOTION,
                        filename="",
                        error=f"Notion API 错误: {response.text}",
                    )

        except ImportError:
            return ExportResult(
                success=False,
                format=ExportFormat.NOTION,
                filename="",
                error="需要安装 httpx: pip install httpx",
            )
        except Exception as e:
            logger.error(f"Notion export failed: {e}")
            return ExportResult(
                success=False,
                format=ExportFormat.NOTION,
                filename="",
                error=str(e),
            )

    def _content_to_notion_blocks(self, content: str) -> List[Dict[str, Any]]:
        """将 Markdown 内容转换为 Notion 块"""
        blocks = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 标题
            if line.startswith("# "):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    },
                })
            elif line.startswith("## "):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:]}}]
                    },
                })
            elif line.startswith("### "):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:]}}]
                    },
                })
            # 列表
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    },
                })
            elif line[0].isdigit() and ". " in line[:4]:
                text = line.split(". ", 1)[1] if ". " in line else line
                blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"text": {"content": text}}]
                    },
                })
            # 引用
            elif line.startswith("> "):
                blocks.append({
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    },
                })
            # 普通段落
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line[:2000]}}]  # Notion 限制
                    },
                })

        return blocks

    # ============================================================
    # 工具方法
    # ============================================================

    def _generate_filename(self, title: str, extension: str) -> str:
        """生成文件名"""
        # 清理标题
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")
        safe_title = safe_title.strip()[:50] or "export"

        # 添加时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{safe_title}_{timestamp}.{extension}"


# ============================================================
# 单例
# ============================================================

export_service = ExportService()
