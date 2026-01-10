# Input: 依赖 FastAPI、database.py (get_db)、models/newsletter.py (Newsletter)、tasks/newsletter.py (generate_newsletter_for_week)
# Output: 周刊 CRUD API 端点 (列表/详情/手动生成)
# Position: API 路由层，周刊功能对外接口
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.newsletter import Newsletter
from app.tasks.newsletter import generate_newsletter_for_week
from app.utils.cache import cache_result, redis_cache


logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 响应模型 ====================


class NewsletterBrief(BaseModel):
    """周刊简要信息（列表项）"""

    id: int
    title: str
    year: int
    week_number: int
    published_at: str  # ISO 8601 格式
    created_at: str
    resource_count: int = Field(description="收录资源总数")
    featured_count: int = Field(description="精选资源数（评分 >= 85）")
    preview: str = Field(description="内容预览（前100字）")

    class Config:
        from_attributes = True


class NewsletterDetail(BaseModel):
    """周刊详细信息"""

    id: int
    title: str
    year: int
    week_number: int
    content: str = Field(description="完整 Markdown 内容")
    resource_ids: List[int] = Field(description="关联的资源 ID 列表")
    published_at: str
    created_at: str
    resource_count: int
    featured_count: int

    class Config:
        from_attributes = True


class PaginatedNewsletters(BaseModel):
    """分页响应"""

    items: List[NewsletterBrief]
    total: int
    page: int
    page_size: int


# ==================== 辅助函数 ====================


def extract_preview(content: str, max_length: int = 100) -> str:
    """
    从 Markdown 内容中提取预览文本

    策略：
    - 移除标题符号（#）
    - 移除特殊标记（>, *, -）
    - 保留纯文本
    - 截取前 max_length 字

    Args:
        content: Markdown 内容
        max_length: 最大长度

    Returns:
        预览文本
    """
    if not content:
        return ""

    # 移除标题符号
    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        # 跳过空行
        if not line.strip():
            continue

        # 移除 Markdown 符号
        cleaned = (
            line.strip()
            .replace("#", "")
            .replace(">", "")
            .replace("*", "")
            .replace("-", "")
            .replace("|", "")
            .strip()
        )

        if cleaned:
            cleaned_lines.append(cleaned)

        # 累计达到最大长度后停止
        if sum(len(line) for line in cleaned_lines) >= max_length:
            break

    preview = " ".join(cleaned_lines)
    return preview[:max_length] + "..." if len(preview) > max_length else preview


def count_featured_resources(resource_ids: List[int], db: Session) -> int:
    """
    统计精选资源数量（评分 >= 85 或 is_featured = True）

    Args:
        resource_ids: 资源 ID 列表
        db: 数据库会话

    Returns:
        精选资源数量
    """
    if not resource_ids:
        return 0

    from app.models.resource import Resource

    count = (
        db.query(Resource)
        .filter(
            Resource.id.in_(resource_ids),
            (Resource.score >= 85) | (Resource.is_featured == True),
        )
        .count()
    )

    return count


# ==================== API 端点 ====================


@router.get(
    "/newsletters",
    response_model=PaginatedNewsletters,
    summary="获取周刊列表",
    description="按时间倒序获取所有周刊，支持分页和年份筛选",
)
@cache_result(
    key_func=lambda kwargs: f"newsletters:list:year={kwargs.get('year')}:page={kwargs.get('page', 1)}:size={kwargs.get('page_size', 10)}",
    ttl=300,  # 5 分钟
)
async def list_newsletters(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    year: Optional[int] = Query(None, description="筛选年份"),
    db: Session = Depends(get_db),
):
    """
    获取周刊列表

    返回格式：
    - 按 published_at 倒序排列
    - 支持分页
    - 支持按年份筛选
    - 包含内容预览（前100字）
    """
    # 构建查询
    query = db.query(Newsletter)

    if year is not None:
        query = query.filter(Newsletter.year == year)

    # 按发布时间倒序
    query = query.order_by(Newsletter.published_at.desc())

    # 统计总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    newsletters = query.offset(offset).limit(page_size).all()

    # 构建响应
    items = []
    for nl in newsletters:
        # 计算资源总数
        resource_count = len(nl.resource_ids) if nl.resource_ids else 0

        # 统计精选数量
        featured_count = count_featured_resources(
            nl.resource_ids or [], db
        )

        # 提取预览
        preview = extract_preview(nl.content)

        items.append(
            NewsletterBrief(
                id=nl.id,
                title=nl.title,
                year=nl.year,
                week_number=nl.week_number,
                published_at=nl.published_at.isoformat() if nl.published_at else "",
                created_at=nl.created_at.isoformat() if nl.created_at else "",
                resource_count=resource_count,
                featured_count=featured_count,
                preview=preview,
            )
        )

    return PaginatedNewsletters(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/newsletters/{newsletter_id}",
    response_model=NewsletterDetail,
    summary="获取周刊详情",
    description="获取指定周刊的完整 Markdown 内容",
)
@cache_result(
    key_func=lambda kwargs: f"newsletters:detail:{kwargs['newsletter_id']}",
    ttl=600,  # 10 分钟
)
async def get_newsletter(
    newsletter_id: int,
    db: Session = Depends(get_db),
):
    """
    获取周刊详情

    返回完整的周刊内容，包括：
    - Markdown 格式的正文
    - 关联的资源 ID 列表
    - 统计信息
    """
    newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()

    if not newsletter:
        raise HTTPException(status_code=404, detail=f"Newsletter {newsletter_id} not found")

    # 计算资源总数
    resource_count = len(newsletter.resource_ids) if newsletter.resource_ids else 0

    # 统计精选数量
    featured_count = count_featured_resources(
        newsletter.resource_ids or [], db
    )

    return NewsletterDetail(
        id=newsletter.id,
        title=newsletter.title,
        year=newsletter.year,
        week_number=newsletter.week_number,
        content=newsletter.content or "",
        resource_ids=newsletter.resource_ids or [],
        published_at=newsletter.published_at.isoformat() if newsletter.published_at else "",
        created_at=newsletter.created_at.isoformat() if newsletter.created_at else "",
        resource_count=resource_count,
        featured_count=featured_count,
    )


@router.post(
    "/newsletters",
    response_model=NewsletterDetail,
    summary="手动生成本周周刊",
    description="手动触发周刊生成，支持指定年份和周数",
)
async def create_newsletter(
    year: Optional[int] = Query(None, description="年份（默认为本年）"),
    week_number: Optional[int] = Query(None, description="周数（默认为本周）"),
    force: bool = Query(False, description="是否强制重新生成（覆盖已存在的周刊）"),
    db: Session = Depends(get_db),
):
    """
    手动生成本周周刊

    行为：
    - 如果未指定 year 和 week_number，生成本周
    - 如果周刊已存在且 force=False，返回 400 错误
    - 如果周刊已存在且 force=True，覆盖旧周刊
    - 调用 generate_newsletter_for_week() 生成
    - 成功后清除列表缓存
    """
    # 计算本周年份和周数
    if year is None or week_number is None:
        from datetime import datetime

        now = datetime.now()
        iso_calendar = now.isocalendar()
        year = iso_calendar[0]
        week_number = iso_calendar[1]

    # 检查是否已存在
    existing = (
        db.query(Newsletter)
        .filter(
            Newsletter.year == year,
            Newsletter.week_number == week_number,
        )
        .first()
    )

    if existing and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Newsletter for {year} week {week_number} already exists. Use force=true to regenerate.",
        )

    logger.info(f"[API] 手动生成周刊: {year}年第{week_number}周")

    try:
        # 调用生成函数
        newsletter = await generate_newsletter_for_week(
            year=year,
            week_number=week_number,
            force_regenerate=force,
        )

        if not newsletter:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate newsletter for {year} week {week_number}. No content available.",
            )

        # 清除列表缓存
        await redis_cache.delete_pattern("newsletters:list:*")
        logger.info(f"[API] 已清除周刊列表缓存")

        # 重新查询以确保最新数据（避免会话过期问题）
        newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter.id).first()

        if not newsletter:
            raise HTTPException(
                status_code=500,
                detail=f"Newsletter was created but not found in database"
            )

        # 计算资源总数
        resource_count = len(newsletter.resource_ids) if newsletter.resource_ids else 0

        # 统计精选数量
        featured_count = count_featured_resources(
            newsletter.resource_ids or [], db
        )

        return NewsletterDetail(
            id=newsletter.id,
            title=newsletter.title,
            year=newsletter.year,
            week_number=newsletter.week_number,
            content=newsletter.content or "",
            resource_ids=newsletter.resource_ids or [],
            published_at=newsletter.published_at.isoformat() if newsletter.published_at else "",
            created_at=newsletter.created_at.isoformat() if newsletter.created_at else "",
            resource_count=resource_count,
            featured_count=featured_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 生成周刊失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate newsletter: {str(e)}",
        )
