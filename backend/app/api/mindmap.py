"""
[INPUT]: 依赖 agents/mindmap
[OUTPUT]: 对外提供概念图生成 API 端点
[POS]: api/ 的概念图路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.mindmap.agent import mindmap_agent, DiagramType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mindmap", tags=["概念图生成"])


# ============================================================
# Pydantic 模型
# ============================================================

class MindmapRequest(BaseModel):
    """概念图生成请求"""
    content: str = Field(..., min_length=50, max_length=50000, description="研究内容")
    diagram_type: str = Field(default="mindmap", description="图表类型")
    focus: Optional[str] = Field(None, max_length=100, description="聚焦主题")


class MindmapResponse(BaseModel):
    """概念图响应"""
    success: bool
    diagram_type: str
    mermaid_code: str
    title: str
    description: str
    error: Optional[str] = None


# ============================================================
# API 端点
# ============================================================

@router.post("/generate", response_model=MindmapResponse)
async def generate_mindmap(data: MindmapRequest):
    """
    生成概念图

    从文本内容生成 Mermaid 格式的图表。
    """
    try:
        # 解析图表类型
        try:
            diagram_type = DiagramType(data.diagram_type)
        except ValueError:
            diagram_type = DiagramType.MINDMAP

        result = await mindmap_agent.generate_mindmap(
            content=data.content,
            diagram_type=diagram_type,
            focus=data.focus,
        )

        return MindmapResponse(
            success=result.success,
            diagram_type=result.diagram_type.value,
            mermaid_code=result.mermaid_code,
            title=result.title,
            description=result.description,
            error=result.error,
        )

    except Exception as e:
        logger.error(f"Mindmap generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=MindmapResponse)
async def generate_summary_mindmap(data: MindmapRequest):
    """
    生成摘要思维导图

    生成内容的结构化摘要思维导图。
    """
    try:
        result = await mindmap_agent.generate_summary_mindmap(
            content=data.content,
            max_depth=3,
        )

        return MindmapResponse(
            success=result.success,
            diagram_type=result.diagram_type.value,
            mermaid_code=result.mermaid_code,
            title=result.title,
            description=result.description,
            error=result.error,
        )

    except Exception as e:
        logger.error(f"Summary mindmap failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def list_diagram_types():
    """获取支持的图表类型"""
    return {
        "types": [
            {"id": "mindmap", "name": "思维导图", "description": "展示概念层次和关联"},
            {"id": "flowchart", "name": "流程图", "description": "展示流程和决策"},
            {"id": "sequence", "name": "时序图", "description": "展示交互过程"},
            {"id": "class", "name": "类图", "description": "展示实体关系"},
            {"id": "er", "name": "ER 图", "description": "展示数据实体关系"},
        ],
        "default": "mindmap",
    }
