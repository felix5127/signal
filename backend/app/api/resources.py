# Input: 依赖 FastAPI、database.py (get_db)、models/resource.py (Resource)
# Output: 资源 CRUD API 端点 (列表/详情/统计/搜索)
# Position: API 路由层，v2.0 资源管理对外接口
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, cast, String
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import Resource
from app.utils.cache import (
    cache_result,
    make_resource_detail_key,
    make_resources_list_key,
    make_resources_stats_key,
    make_search_key,
    redis_cache,
)
from app.config import config


router = APIRouter()


# ========== 响应模型 ==========


class ResourceBrief(BaseModel):
    """资源简要信息（列表项）"""

    id: int
    type: str  # article/podcast/tweet/video
    source_name: str
    url: str
    title: str
    title_translated: Optional[str] = None
    author: Optional[str] = None
    one_sentence_summary: Optional[str] = None
    one_sentence_summary_zh: Optional[str] = None
    summary: Optional[str] = None  # 详细摘要
    summary_zh: Optional[str] = None  # 中文详细摘要
    content_markdown: Optional[str] = None  # 正文内容（用于列表预览）
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    tags: Optional[List[str]] = None
    score: int = 0
    is_featured: bool = False
    language: Optional[str] = None
    word_count: Optional[int] = None
    read_time: Optional[int] = None
    duration: Optional[int] = None  # 播客/视频时长
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    source_icon_url: Optional[str] = None  # Phase 1.5 新增
    thumbnail_url: Optional[str] = None  # 缩略图/封面 (播客/视频)

    @field_validator("published_at", "created_at", mode="before")
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True


class ResourceDetail(ResourceBrief):
    """资源完整详情"""

    source_url: Optional[str] = None
    content_markdown: Optional[str] = None
    summary: Optional[str] = None
    summary_zh: Optional[str] = None
    main_points: Optional[List[Dict[str, str]]] = None
    main_points_zh: Optional[List[Dict[str, str]]] = None
    key_quotes: Optional[List[str]] = None
    key_quotes_zh: Optional[List[str]] = None
    status: str = "pending"
    audio_url: Optional[str] = None
    transcript: Optional[str] = None
    chapters: Optional[List[Dict[str, Any]]] = None  # 章节列表
    qa_pairs: Optional[List[Dict[str, Any]]] = None  # Q&A 对
    featured_reason: Optional[str] = None  # 精选理由
    featured_reason_zh: Optional[str] = None  # 中文精选理由
    analyzed_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("analyzed_at", "updated_at", mode="before")
    @classmethod
    def convert_detail_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class ResourceListResponse(BaseModel):
    """资源列表响应"""

    items: List[ResourceBrief]
    total: int
    page: int
    pageSize: int


class ResourceStatsResponse(BaseModel):
    """资源统计响应"""

    total: int
    by_type: Dict[str, int]
    by_domain: Dict[str, int]
    by_status: Dict[str, int]
    featured_count: int
    latest_update: Optional[str] = None


# ========== 时间过滤辅助函数 ==========


def get_time_filter_date(time_filter: str) -> Optional[datetime]:
    """
    根据时间过滤参数计算起始时间

    Args:
        time_filter: 1d/1w/1m/3m/1y

    Returns:
        起始时间 datetime，如果无效返回 None
    """
    now = datetime.now()
    filters = {
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    delta = filters.get(time_filter)
    if delta:
        return now - delta
    return None


# ========== API 端点 ==========


@router.get("/resources", response_model=ResourceListResponse)
@cache_result(
    key_func=make_resources_list_key,
    ttl=300,  # 5 分钟（可在 config.yaml 中配置）
)
def get_resources(
    type: Optional[Literal["article", "podcast", "tweet", "video"]] = Query(
        default=None, description="资源类型"
    ),
    domain: Optional[
        Literal["软件编程", "人工智能", "产品设计", "商业科技"]
    ] = Query(default=None, description="一级分类"),
    lang: Optional[Literal["zh", "en"]] = Query(
        default=None, description="语言筛选: zh/en"
    ),
    source: Optional[str] = Query(default=None, description="来源名称"),
    timeFilter: Optional[str] = Query(
        default=None, description="时间范围: 1d/1w/1m/3m/1y（空或无效值视为不限）"
    ),
    minScore: Optional[float] = Query(
        default=None, ge=0, le=10, description="最低评分（0-10）"
    ),
    sort: Optional[Literal["default", "time", "score"]] = Query(
        default="default", description="排序方式"
    ),
    featured: Optional[bool] = Query(default=None, description="仅精选"),
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取资源列表

    Phase 1.5 新增参数：
    - lang: 语言筛选（zh/en）
    - source: 来源名称筛选
    - minScore: 最低评分（0-10）

    排序规则：
    - default: 精选优先 + 评分倒序 + 时间倒序
    - time: 发布时间倒序
    - score: 评分倒序 + 时间倒序

    时间过滤：
    - 1d: 1天内
    - 1w: 1周内（默认）
    - 1m: 1个月内
    - 3m: 3个月内
    - 1y: 1年内

    缓存：5 分钟（可在 config.yaml 中配置）
    """
    # 基础查询：只查询已发布的资源
    query = db.query(Resource).filter(Resource.status == "published")

    # 类型过滤
    if type:
        query = query.filter(Resource.type == type)

    # 分类过滤
    if domain:
        query = query.filter(Resource.domain == domain)

    # 语言过滤（Phase 1.5 新增）
    if lang:
        query = query.filter(Resource.language == lang)

    # 来源过滤（Phase 1.5 新增）
    if source:
        query = query.filter(Resource.source_name == source)

    # 评分过滤（Phase 1.5 新增，注意：数据库 score 是 0-100）
    if minScore is not None:
        min_score_scaled = minScore * 10
        query = query.filter(Resource.score >= min_score_scaled)

    # 精选过滤
    if featured is not None:
        query = query.filter(Resource.is_featured == featured)

    # 时间过滤
    if timeFilter:
        start_time = get_time_filter_date(timeFilter)
        if start_time:
            query = query.filter(Resource.published_at >= start_time)

    # 获取总数（在排序和分页之前）
    total = query.count()

    # 排序
    if sort == "time":
        query = query.order_by(Resource.published_at.desc())
    elif sort == "score":
        query = query.order_by(Resource.score.desc(), Resource.published_at.desc())
    else:  # default
        query = query.order_by(
            Resource.is_featured.desc(),
            Resource.score.desc(),
            Resource.published_at.desc(),
        )

    # 分页
    offset = (page - 1) * pageSize
    items = query.offset(offset).limit(pageSize).all()

    # 转换为响应模型
    items_brief = []
    for item in items:
        items_brief.append(
            ResourceBrief(
                id=item.id,
                type=item.type,
                source_name=item.source_name,
                url=item.url,
                title=item.title,
                title_translated=item.title_translated,
                author=item.author,
                one_sentence_summary=item.one_sentence_summary,
                one_sentence_summary_zh=item.one_sentence_summary_zh,
                summary=item.summary,
                summary_zh=item.summary_zh,
                content_markdown=item.content_markdown,
                domain=item.domain,
                subdomain=item.subdomain,
                tags=item.tags,
                score=item.score or 0,
                is_featured=item.is_featured or False,
                language=item.language,
                word_count=item.word_count,
                read_time=item.read_time,
                duration=item.duration,
                published_at=item.published_at,
                created_at=item.created_at,
                source_icon_url=item.source_icon_url,
                thumbnail_url=item.thumbnail_url,
            )
        )

    return ResourceListResponse(
        items=items_brief, total=total, page=page, pageSize=pageSize
    )


@router.get("/resources/stats", response_model=ResourceStatsResponse)
@cache_result(
    key_func=make_resources_stats_key,
    ttl=60,  # 1 分钟
)
def get_resources_stats(db: Session = Depends(get_db)):
    """
    获取资源统计信息

    返回各类型、各分类的数量统计

    缓存：1 分钟（可在 config.yaml 中配置）
    """
    # 总数（已发布）
    total = db.query(Resource).filter(Resource.status == "published").count()

    # 按类型统计
    by_type_query = (
        db.query(Resource.type, func.count(Resource.id).label("count"))
        .filter(Resource.status == "published")
        .group_by(Resource.type)
        .all()
    )
    by_type = {row.type: row.count for row in by_type_query}

    # 按分类统计
    by_domain_query = (
        db.query(Resource.domain, func.count(Resource.id).label("count"))
        .filter(Resource.status == "published")
        .filter(Resource.domain.isnot(None))
        .group_by(Resource.domain)
        .all()
    )
    by_domain = {row.domain: row.count for row in by_domain_query}

    # 按状态统计（全部状态）
    by_status_query = (
        db.query(Resource.status, func.count(Resource.id).label("count"))
        .group_by(Resource.status)
        .all()
    )
    by_status = {row.status: row.count for row in by_status_query}

    # 精选数量
    featured_count = (
        db.query(Resource)
        .filter(Resource.status == "published")
        .filter(Resource.is_featured == True)  # noqa: E712
        .count()
    )

    # 最新更新时间
    latest = (
        db.query(Resource)
        .filter(Resource.status == "published")
        .order_by(Resource.created_at.desc())
        .first()
    )
    latest_update = latest.created_at.isoformat() if latest and latest.created_at else None

    return ResourceStatsResponse(
        total=total,
        by_type=by_type,
        by_domain=by_domain,
        by_status=by_status,
        featured_count=featured_count,
        latest_update=latest_update,
    )


@router.get("/resources/{resource_id}", response_model=ResourceDetail)
@cache_result(
    key_func=lambda kwargs: make_resource_detail_key(kwargs["resource_id"]),
    ttl=600,  # 10 分钟
)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """
    获取资源详情

    Args:
        resource_id: 资源 ID

    Returns:
        完整的 Resource 对象

    缓存：10 分钟（可在 config.yaml 中配置）
    """
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    return ResourceDetail(
        id=resource.id,
        type=resource.type,
        source_name=resource.source_name,
        source_url=resource.source_url,
        source_icon_url=resource.source_icon_url,
        thumbnail_url=resource.thumbnail_url,
        url=resource.url,
        title=resource.title,
        title_translated=resource.title_translated,
        author=resource.author,
        content_markdown=resource.content_markdown,
        word_count=resource.word_count,
        read_time=resource.read_time,
        one_sentence_summary=resource.one_sentence_summary,
        one_sentence_summary_zh=resource.one_sentence_summary_zh,
        summary=resource.summary,
        summary_zh=resource.summary_zh,
        main_points=resource.main_points,
        main_points_zh=resource.main_points_zh,
        key_quotes=resource.key_quotes,
        key_quotes_zh=resource.key_quotes_zh,
        domain=resource.domain,
        subdomain=resource.subdomain,
        tags=resource.tags,
        score=resource.score or 0,
        is_featured=resource.is_featured or False,
        featured_reason=resource.featured_reason,
        featured_reason_zh=resource.featured_reason_zh,
        language=resource.language,
        status=resource.status,
        audio_url=resource.audio_url,
        duration=resource.duration,
        transcript=resource.transcript,
        chapters=resource.chapters,
        qa_pairs=resource.qa_pairs,
        published_at=resource.published_at,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        analyzed_at=resource.analyzed_at,
    )


@router.get("/search", response_model=ResourceListResponse)
@cache_result(
    key_func=make_search_key,
    ttl=300,  # 5 分钟
)
def search_resources(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    type: Optional[Literal["article", "podcast", "tweet", "video"]] = Query(
        default=None, description="资源类型"
    ),
    domain: Optional[
        Literal["软件编程", "人工智能", "产品设计", "商业科技"]
    ] = Query(default=None, description="一级分类"),
    lang: Optional[Literal["zh", "en"]] = Query(
        default=None, description="语言筛选: zh/en"
    ),
    source: Optional[str] = Query(default=None, description="来源名称"),
    timeFilter: Optional[Literal["1d", "1w", "1m", "3m", "1y"]] = Query(
        default=None, description="时间范围"
    ),
    minScore: Optional[float] = Query(
        default=None, ge=0, le=10, description="最低评分（0-10）"
    ),
    sort: Optional[Literal["default", "time", "score"]] = Query(
        default="default", description="排序方式"
    ),
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    全文搜索资源

    搜索范围：
    - title / title_translated（标题）
    - one_sentence_summary / one_sentence_summary_zh（一句话总结）
    - summary / summary_zh（详细摘要）
    - tags（标签，JSON数组）

    使用 ILIKE 进行模糊匹配，兼容 PostgreSQL 和 SQLite

    Args:
        q: 搜索关键词
        type: 资源类型筛选
        domain: 分类筛选
        timeFilter: 时间范围筛选
        sort: 排序方式
        page: 页码
        pageSize: 每页数量

    Returns:
        匹配的资源列表

    缓存：5 分钟（可在 config.yaml 中配置）
    """
    keyword = q.strip()

    # 基础查询：只查询已发布的资源
    query = db.query(Resource).filter(Resource.status == "published")

    # 全文搜索：使用 ILIKE 模糊匹配（兼容 PostgreSQL 和 SQLite）
    # 注意：SQLite 使用 LIKE（大小写不敏感依赖 collation）
    search_conditions = [
        Resource.title.ilike(f"%{keyword}%"),
        Resource.title_translated.ilike(f"%{keyword}%"),
        Resource.one_sentence_summary.ilike(f"%{keyword}%"),
        Resource.one_sentence_summary_zh.ilike(f"%{keyword}%"),
        Resource.summary.ilike(f"%{keyword}%"),
        Resource.summary_zh.ilike(f"%{keyword}%"),
        # tags 是 JSON 数组，转换为字符串进行搜索
        cast(Resource.tags, String).ilike(f"%{keyword}%"),
    ]
    query = query.filter(or_(*search_conditions))

    # 类型过滤
    if type:
        query = query.filter(Resource.type == type)

    # 分类过滤
    if domain:
        query = query.filter(Resource.domain == domain)

    # 语言过滤（Phase 1.5 新增）
    if lang:
        query = query.filter(Resource.language == lang)

    # 来源过滤（Phase 1.5 新增）
    if source:
        query = query.filter(Resource.source_name == source)

    # 评分过滤（Phase 1.5 新增，注意：数据库 score 是 0-100）
    if minScore is not None:
        min_score_scaled = minScore * 10
        query = query.filter(Resource.score >= min_score_scaled)

    # 时间过滤
    if timeFilter:
        start_time = get_time_filter_date(timeFilter)
        if start_time:
            query = query.filter(Resource.published_at >= start_time)

    # 获取总数
    total = query.count()

    # 排序
    if sort == "time":
        query = query.order_by(Resource.published_at.desc())
    elif sort == "score":
        query = query.order_by(Resource.score.desc(), Resource.published_at.desc())
    else:  # default - 精选优先 + 评分倒序 + 时间倒序
        query = query.order_by(
            Resource.is_featured.desc(),
            Resource.score.desc(),
            Resource.published_at.desc(),
        )

    # 分页
    offset = (page - 1) * pageSize
    items = query.offset(offset).limit(pageSize).all()

    # 转换为响应模型
    items_brief = []
    for item in items:
        items_brief.append(
            ResourceBrief(
                id=item.id,
                type=item.type,
                source_name=item.source_name,
                url=item.url,
                title=item.title,
                title_translated=item.title_translated,
                author=item.author,
                one_sentence_summary=item.one_sentence_summary,
                one_sentence_summary_zh=item.one_sentence_summary_zh,
                summary=item.summary,
                summary_zh=item.summary_zh,
                content_markdown=item.content_markdown,
                domain=item.domain,
                subdomain=item.subdomain,
                tags=item.tags,
                score=item.score or 0,
                is_featured=item.is_featured or False,
                language=item.language,
                word_count=item.word_count,
                read_time=item.read_time,
                duration=item.duration,
                published_at=item.published_at,
                created_at=item.created_at,
                source_icon_url=item.source_icon_url,
                thumbnail_url=item.thumbnail_url,
            )
        )

    return ResourceListResponse(
        items=items_brief, total=total, page=page, pageSize=pageSize
    )


# ========== Deep Research 端点 ==========


@router.get("/resources/{resource_id}/deep-research")
async def get_resource_deep_research(resource_id: int, db: Session = Depends(get_db)):
    """
    获取资源的深度研究报告
    """
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if not resource.deep_research:
        raise HTTPException(status_code=404, detail="深度研究报告不存在")

    return {
        "success": True,
        "data": {
            "resource_id": resource.id,
            "title": resource.title,
            "content": resource.deep_research,
            "generated_at": resource.deep_research_generated_at.isoformat() if resource.deep_research_generated_at else None,
            "tokens_used": resource.deep_research_tokens or 0,
            "cost_usd": resource.deep_research_cost or 0.0,
            "strategy": resource.deep_research_strategy or "unknown",
            "sources": resource.deep_research_sources,
            "metadata": resource.deep_research_metadata,
        }
    }


@router.post("/resources/{resource_id}/deep-research")
async def generate_resource_deep_research(
    resource_id: int,
    background_tasks: BackgroundTasks,
    strategy: str = Query(default="lightweight", pattern="^(lightweight|full_agent|auto)$"),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    生成资源深度研究报告（后台异步执行）

    Args:
        resource_id: 资源ID
        background_tasks: FastAPI后台任务
        strategy: 研究策略 (lightweight/full_agent/auto)
        force: 强制重新生成，忽略缓存

    Returns:
        任务状态信息（包含 task_id 用于跟踪进度）
    """
    import time
    from datetime import datetime
    from app.config import config as app_config
    from app.models.task import TaskStatus

    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    # 检查缓存
    if not force and resource.deep_research and resource.deep_research_generated_at:
        cache_age = datetime.now() - resource.deep_research_generated_at
        cache_hours = getattr(app_config, 'deep_research', type('DeepResearchConfig', (), {'cache_duration_hours': 24})).cache_duration_hours

        if cache_age.total_seconds() < cache_hours * 3600:
            return {
                "success": True,
                "data": {
                    "status": "cached",
                    "message": "报告已存在且仍然新鲜",
                    "resource_id": resource_id,
                    "generated_at": resource.deep_research_generated_at.isoformat(),
                    "cache_age_hours": cache_age.total_seconds() / 3600,
                }
            }

    # 生成唯一任务ID
    task_id = f"deep_research_{resource_id}_{int(time.time())}"

    # 创建 TaskStatus 记录
    task = TaskStatus(
        task_id=task_id,
        task_type="deep_research",
        status="pending",
        progress=0,
        meta={
            "resource_id": resource_id,
            "resource_title": resource.title,
            "resource_type": resource.type,
            "strategy": strategy,
        }
    )
    db.add(task)
    db.commit()

    # 启动后台任务（传入 task_id）
    from app.background_tasks import run_resource_deep_research
    background_tasks.add_task(run_resource_deep_research, resource_id, task_id, strategy)

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "pending",
            "message": "深度研究报告生成已在后台启动",
            "resource_id": resource_id,
            "strategy": strategy,
        }
    }
