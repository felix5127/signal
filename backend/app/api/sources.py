# Input: 依赖 FastAPI、database.py (get_db)、models/resource.py (Resource)
# Output: 热门来源 API 端点
# Position: API 路由层，提供热门来源数据接口
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from typing import List, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import Resource


router = APIRouter()


# ========== 响应模型 ==========


class HotSourceItem(BaseModel):
    """热门来源项"""

    name: str = Field(..., description="来源名称")
    icon: str = Field(..., description="来源图标 URL")
    totalCount: int = Field(..., description="总文章数")
    qualifiedCount: int = Field(..., description="高分文章数（score >= 85）")


class HotSourcesResponse(BaseModel):
    """热门来源列表响应"""

    items: List[HotSourceItem]


# ========== API 端点 ==========


@router.get("/hot", response_model=HotSourcesResponse)
def get_hot_sources(
    type: Literal["article", "podcast", "tweet", "video"] = Query(
        default="article", description="内容类型"
    ),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    minScore: float = Query(default=8.5, ge=0, le=10, description="最低评分"),
    db: Session = Depends(get_db),
):
    """
    获取热门来源列表

    按文章数量排序，返回指定类型下的热门来源

    Args:
        type: 内容类型（article/podcast/tweet/video）
        limit: 返回数量（1-50）
        minScore: 最低评分（用于计算合格文章数）
        db: 数据库会话

    Returns:
        热门来源列表

    Example:
        GET /api/sources/hot?type=article&limit=10&minScore=8.5

        Response:
        {
            "items": [
                {
                    "name": "Hacker News",
                    "icon": "https://icons.duckduckgo.com/ip3/news.ycombinator.com.ico",
                    "totalCount": 150,
                    "qualifiedCount": 45
                }
            ]
        }
    """
    # 查询当前类型下文章最多的来源
    # 注意：评分是 0-100，需要将 minScore (0-10) 转换为 0-100
    min_score_scaled = minScore * 10

    # 子查询：获取每个来源的统计信息（只按 source_name 分组）
    subquery = (
        db.query(
            Resource.source_name.label("name"),
            func.max(Resource.source_icon_url).label("icon"),  # 取该来源最常用的图标
            func.count(Resource.id).label("total_count"),
            func.count(Resource.id)
            .filter(Resource.score >= min_score_scaled)
            .label("qualified_count"),
        )
        .filter(Resource.type == type, Resource.status == "published")
        .group_by(Resource.source_name)
        .order_by(func.count(Resource.id).desc())
        .limit(limit)
        .subquery()
    )

    # 主查询：从子查询获取结果
    results = (
        db.query(subquery)
        .all()
    )

    items = [
        HotSourceItem(
            name=row.name or "Unknown",
            icon=row.icon or "",
            totalCount=row.total_count,
            qualifiedCount=row.qualified_count,
        )
        for row in results
    ]

    return HotSourcesResponse(items=items)
