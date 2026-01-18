"""
[INPUT]: 依赖 FastAPI, database.py (get_db), services/prompt_service.py
[OUTPUT]: 对外提供 Prompt 版本管理 API 端点
[POS]: API 路由层，Admin Prompt 管理
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.prompt_service import PromptService


router = APIRouter()


# ========== 请求/响应模型 ==========

class PromptCreateRequest(BaseModel):
    """创建 Prompt 请求"""
    name: str
    type: str  # filter/analyzer/translator
    system_prompt: str
    user_prompt_template: str


class PromptResponse(BaseModel):
    """Prompt 响应"""
    id: int
    name: str
    version: int
    type: str
    system_prompt: str
    user_prompt_template: str
    status: str
    total_used: int
    avg_score: Optional[float]
    approval_rate: Optional[float]
    created_at: Optional[str]
    activated_at: Optional[str]

    class Config:
        from_attributes = True


# ========== API 端点 ==========

@router.get("")
async def get_prompts(
    type: Optional[str] = Query(None, description="类型筛选: filter/analyzer/translator"),
    db: Session = Depends(get_db),
):
    """
    获取 Prompt 列表

    - 支持按类型筛选
    - 按类型和版本号排序
    """
    service = PromptService(db)

    if type:
        prompts = service.get_prompts_by_type(type)
    else:
        prompts = service.get_all_prompts()

    data = [
        {
            "id": p.id,
            "name": p.name,
            "version": p.version,
            "type": p.type,
            "system_prompt": p.system_prompt,
            "user_prompt_template": p.user_prompt_template,
            "status": p.status,
            "total_used": p.total_used or 0,
            "avg_score": p.avg_score,
            "approval_rate": p.approval_rate,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "activated_at": p.activated_at.isoformat() if p.activated_at else None,
        }
        for p in prompts
    ]

    return {"success": True, "data": data}


@router.get("/active/{prompt_type}", response_model=Optional[PromptResponse])
async def get_active_prompt(
    prompt_type: str,
    db: Session = Depends(get_db),
):
    """
    获取指定类型的当前活跃 Prompt

    - type: filter/analyzer/translator
    """
    if prompt_type not in ["filter", "analyzer", "translator"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid type, use filter/analyzer/translator"
        )

    service = PromptService(db)
    prompt = service.get_active_prompt(prompt_type)

    if not prompt:
        return None

    return {
        "id": prompt.id,
        "name": prompt.name,
        "version": prompt.version,
        "type": prompt.type,
        "system_prompt": prompt.system_prompt,
        "user_prompt_template": prompt.user_prompt_template,
        "status": prompt.status,
        "total_used": prompt.total_used or 0,
        "avg_score": prompt.avg_score,
        "approval_rate": prompt.approval_rate,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "activated_at": prompt.activated_at.isoformat() if prompt.activated_at else None,
    }


@router.post("", response_model=PromptResponse)
async def create_prompt(
    request: PromptCreateRequest,
    db: Session = Depends(get_db),
):
    """
    创建新版本 Prompt

    - 自动计算版本号（当前最大版本 + 1）
    - 初始状态为 draft
    """
    if request.type not in ["filter", "analyzer", "translator"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid type, use filter/analyzer/translator"
        )

    service = PromptService(db)

    prompt = service.create_prompt(
        name=request.name,
        prompt_type=request.type,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
    )

    return {
        "id": prompt.id,
        "name": prompt.name,
        "version": prompt.version,
        "type": prompt.type,
        "system_prompt": prompt.system_prompt,
        "user_prompt_template": prompt.user_prompt_template,
        "status": prompt.status,
        "total_used": prompt.total_used or 0,
        "avg_score": prompt.avg_score,
        "approval_rate": prompt.approval_rate,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "activated_at": prompt.activated_at.isoformat() if prompt.activated_at else None,
    }


@router.post("/{prompt_id}/activate", response_model=PromptResponse)
async def activate_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
):
    """
    激活指定 Prompt

    - 同类型的其他 active Prompt 会自动归档
    """
    service = PromptService(db)

    prompt = service.activate_prompt(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {
        "id": prompt.id,
        "name": prompt.name,
        "version": prompt.version,
        "type": prompt.type,
        "system_prompt": prompt.system_prompt,
        "user_prompt_template": prompt.user_prompt_template,
        "status": prompt.status,
        "total_used": prompt.total_used or 0,
        "avg_score": prompt.avg_score,
        "approval_rate": prompt.approval_rate,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "activated_at": prompt.activated_at.isoformat() if prompt.activated_at else None,
    }


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt_detail(
    prompt_id: int,
    db: Session = Depends(get_db),
):
    """
    获取单个 Prompt 详情
    """
    service = PromptService(db)

    prompt = service.get_prompt_by_id(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {
        "id": prompt.id,
        "name": prompt.name,
        "version": prompt.version,
        "type": prompt.type,
        "system_prompt": prompt.system_prompt,
        "user_prompt_template": prompt.user_prompt_template,
        "status": prompt.status,
        "total_used": prompt.total_used or 0,
        "avg_score": prompt.avg_score,
        "approval_rate": prompt.approval_rate,
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "activated_at": prompt.activated_at.isoformat() if prompt.activated_at else None,
    }
