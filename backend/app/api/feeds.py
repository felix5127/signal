# Input: database.py (get_db), models/resource.py (Resource)
# Output: RSS XML 格式的 feed
# Position: RSS Feed API，提供多种订阅源
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime, timedelta
from typing import List, Literal, Optional
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import Resource

router = APIRouter()


def create_rss_feed(
    resources: List[Resource],
    title: str,
    link: str,
    description: str
) -> str:
    """
    创建 RSS 2.0 格式的 Feed

    Args:
        resources: Resource 列表
        title: Feed 标题
        link: Feed 链接
        description: Feed 描述

    Returns:
        RSS XML 字符串
    """
    # 创建 RSS 根元素
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    # Channel 元数据
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = link
    SubElement(channel, "description").text = description
    SubElement(channel, "language").text = "zh-CN"
    SubElement(channel, "generator").text = "Signal Hunter"
    SubElement(channel, "lastBuildDate").text = datetime.now().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    # 添加每个资源为一个 item
    for resource in resources:
        item = SubElement(channel, "item")

        # 标题（优先使用中文翻译）
        title_text = resource.title_translated or resource.title
        SubElement(item, "title").text = title_text

        # 链接
        SubElement(item, "link").text = resource.url

        # 描述（使用中文摘要）
        description_parts = []

        # 一句话总结
        one_liner = resource.one_sentence_summary_zh or resource.one_sentence_summary
        if one_liner:
            description_parts.append(f"<p><strong>{one_liner}</strong></p>")

        # 详细摘要
        summary = resource.summary_zh or resource.summary
        if summary:
            description_parts.append(f"<p>{summary}</p>")

        # 分类和评分
        meta_info = []
        if resource.domain:
            meta_info.append(f"分类: {resource.domain}")
        if resource.subdomain:
            meta_info.append(f"{resource.subdomain}")
        if resource.score:
            meta_info.append(f"评分: {resource.score}/100")
        if resource.is_featured:
            meta_info.append("精选")

        if meta_info:
            description_parts.append(f"<p><em>{' | '.join(meta_info)}</em></p>")

        description_text = "\n".join(description_parts)
        SubElement(item, "description").text = description_text

        # GUID（使用 URL）
        guid = SubElement(item, "guid", isPermaLink="true")
        guid.text = resource.url

        # 发布时间
        if resource.published_at:
            pub_date = resource.published_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
            SubElement(item, "pubDate").text = pub_date

        # 分类
        if resource.domain:
            SubElement(item, "category").text = resource.domain

        # 作者
        if resource.author:
            SubElement(item, "author").text = resource.author

    # 转换为 XML 字符串
    xml_str = tostring(rss, encoding="unicode", method="xml")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


@router.get("/rss")
def get_rss_feed(
    type: Optional[Literal["article", "podcast", "tweet", "video"]] = Query(
        default=None, description="资源类型"
    ),
    domain: Optional[Literal["软件编程", "人工智能", "产品设计", "商业科技"]] = Query(
        default=None, description="一级分类"
    ),
    featured: Optional[bool] = Query(default=None, description="仅精选"),
    minScore: Optional[int] = Query(default=None, ge=0, le=100, description="最低分数"),
    timeFilter: Optional[Literal["1d", "1w", "1m", "3m", "1y"]] = Query(
        default="1w", description="时间范围"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="最大条目数"),
    db: Session = Depends(get_db),
):
    """
    RSS Feed 输出

    支持多种筛选条件：
    - type: 按内容类型筛选
    - domain: 按分类筛选
    - featured: 仅精选内容
    - minScore: 最低评分
    - timeFilter: 时间范围
    - limit: 最大条目数

    示例：
    - /feeds/rss - 全站（1周内，最多50条）
    - /feeds/rss?type=article - 仅文章
    - /feeds/rss?featured=true - 仅精选
    - /feeds/rss?domain=人工智能&minScore=85 - 高分AI内容
    """
    # 基础查询
    query = db.query(Resource).filter(Resource.status == "published")

    # 类型过滤
    if type:
        query = query.filter(Resource.type == type)

    # 分类过滤
    if domain:
        query = query.filter(Resource.domain == domain)

    # 精选过滤
    if featured is not None:
        query = query.filter(Resource.is_featured == featured)

    # 分数过滤
    if minScore is not None:
        query = query.filter(Resource.score >= minScore)

    # 时间过滤
    if timeFilter:
        time_filters = {
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "1y": timedelta(days=365),
        }
        delta = time_filters.get(timeFilter)
        if delta:
            start_time = datetime.now() - delta
            query = query.filter(Resource.published_at >= start_time)

    # 排序：精选优先 + 评分倒序 + 时间倒序
    query = query.order_by(
        Resource.is_featured.desc(),
        Resource.score.desc(),
        Resource.published_at.desc(),
    )

    # 限制数量
    resources = query.limit(limit).all()

    # 生成 Feed 标题和描述
    feed_parts = []
    if type:
        type_names = {
            "article": "文章",
            "podcast": "播客",
            "tweet": "推文",
            "video": "视频",
        }
        feed_parts.append(type_names.get(type, type))

    if domain:
        feed_parts.append(domain)

    if featured:
        feed_parts.append("精选")

    if minScore:
        feed_parts.append(f"评分≥{minScore}")

    if feed_parts:
        feed_title = f"Signal Hunter - {' '.join(feed_parts)}"
        feed_description = f"{' | '.join(feed_parts)} 的最新内容"
    else:
        feed_title = "Signal Hunter - AI驱动的技术内容聚合"
        feed_description = "精选优质技术文章、播客、推文和视频"

    # 生成 RSS XML
    rss_xml = create_rss_feed(
        resources=resources,
        title=feed_title,
        link="https://signal-hunter.com",
        description=feed_description,
    )

    # 返回 XML响应
    return Response(content=rss_xml, media_type="application/rss+xml; charset=utf-8")


@router.get("/atom")
def get_atom_feed():
    """
    Atom Feed 输出（可选实现）

    Atom 是另一种常用的 feed 格式，比 RSS 更现代
    暂未实现，返回提示
    """
    return {"message": "Atom feed not implemented yet. Please use /feeds/rss"}
