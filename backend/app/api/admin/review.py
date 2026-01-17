"""
[INPUT]: 依赖 FastAPI, database.py (get_db), services/review_service.py
[OUTPUT]: 对外提供审核相关 API 端点
[POS]: API 路由层，Admin 审核管理
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.review_service import ReviewService


router = APIRouter()


# ========== 请求/响应模型 ==========

class ReviewActionRequest(BaseModel):
    """审核操作请求"""
    action: str  # publish/reject/restore
    comment: Optional[str] = None


class BatchReviewRequest(BaseModel):
    """批量审核请求"""
    resource_ids: List[int]
    action: str  # publish/reject/restore
    comment: Optional[str] = None


class ReviewItemResponse(BaseModel):
    """审核列表项"""
    id: int
    title: str
    url: str
    source_name: Optional[str]
    status: str
    llm_score: Optional[int]
    llm_reason: Optional[str]
    language: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """审核列表响应"""
    items: List[ReviewItemResponse]
    total: int
    page: int
    page_size: int


class ReviewStatsResponse(BaseModel):
    """审核统计响应"""
    total_pending: int
    total_approved: int
    total_rejected: int
    total_published: int
    total_overturned: int
    by_source: List[dict]


# ========== API 端点 ==========

@router.get("/list", response_model=ReviewListResponse)
async def get_review_list(
    status: Optional[str] = Query(None, description="状态筛选: approved/rejected/all"),
    source_id: Optional[int] = Query(None, description="数据源 ID"),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取待审核列表

    - 默认返回 approved 和 rejected 状态的内容
    - 支持按状态、来源、日期筛选
    - 支持分页
    """
    # 解析日期
    parsed_date_from = None
    parsed_date_to = None

    if date_from:
        try:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format, use YYYY-MM-DD")

    if date_to:
        try:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format, use YYYY-MM-DD")

    service = ReviewService(db)
    result = service.get_review_list(
        status=status,
        source_id=source_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        page=page,
        page_size=page_size,
    )

    return result


@router.post("/{resource_id}/action")
async def review_single(
    resource_id: int,
    request: ReviewActionRequest,
    db: Session = Depends(get_db),
):
    """
    单个资源审核操作

    - publish: 发布（approved -> published）
    - reject: 拒绝（approved -> rejected）
    - restore: 恢复（rejected -> published）
    """
    if request.action not in ["publish", "reject", "restore"]:
        raise HTTPException(status_code=400, detail="Invalid action, use publish/reject/restore")

    service = ReviewService(db)
    result = service.review_action(
        resource_id=resource_id,
        action=request.action,
        comment=request.comment,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")

    return {
        "success": True,
        "resource_id": resource_id,
        "new_status": result.status,
    }


@router.post("/action")
async def review_batch(
    request: BatchReviewRequest,
    db: Session = Depends(get_db),
):
    """
    批量审核操作

    - 一次最多处理 100 个资源
    """
    if len(request.resource_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 resources per batch")

    if request.action not in ["publish", "reject", "restore"]:
        raise HTTPException(status_code=400, detail="Invalid action, use publish/reject/restore")

    service = ReviewService(db)
    result = service.batch_review(
        resource_ids=request.resource_ids,
        action=request.action,
        comment=request.comment,
    )

    return {
        "success": True,
        "processed": result["success"],
        "failed": result["failed"],
    }


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取审核统计

    - 各状态数量
    - 人工改判数量
    - 按来源统计
    """
    parsed_date_from = None
    parsed_date_to = None

    if date_from:
        try:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")

    if date_to:
        try:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    service = ReviewService(db)
    return service.get_review_stats(
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
