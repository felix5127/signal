# [INPUT]: 依赖 Resource 模型、DailyDigest/WeeklyDigest 模型、数据库会话
# [OUTPUT]: 提供每日/每周汇总生成函数
# [POS]: 定时任务层，负责生成时间维度的资源聚合
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
import logging

from app.models.resource import Resource
from app.models.digest import DailyDigest, WeeklyDigest
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def generate_daily_digest(target_date: str = None) -> DailyDigest:
    """生成每日精选汇总

    Args:
        target_date: 目标日期 "YYYY-MM-DD"，默认为昨天

    Returns:
        DailyDigest 对象

    逻辑:
        - 方案D (分源精选): 每个源选出Top N
        - HN头条 (3条): score >= 60, 按score排序
        - GitHub热门 (3条): 按score排序
        - HF重要模型 (2条): 按score排序
        - 其他源 (2条): 按score排序
        - 总计: 10条左右
    """
    db = SessionLocal()

    try:
        # 确定目标日期
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"[DailyDigest] 开始生成 {target_date} 的每日精选")

        # 检查是否已存在
        existing = db.query(DailyDigest).filter(DailyDigest.date == target_date).first()
        if existing:
            logger.warning(f"[DailyDigest] {target_date} 已存在，跳过生成")
            return existing

        # 查询当天所有资源
        start_time = f"{target_date} 00:00:00"
        end_time = f"{target_date} 23:59:59"

        all_resources = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time
        ).all()

        logger.info(f"[DailyDigest] 找到 {len(all_resources)} 条资源")

        # 按来源分组统计
        sources_breakdown = {}
        for r in all_resources:
            sources_breakdown[r.source_name] = sources_breakdown.get(r.source_name, 0) + 1

        # 分源精选 (使用 Resource 表的 source_name 和 score)
        # HN: source_name 可能是 "HN" 或 "hackernews"
        top_hn = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.source_name.in_(["HN", "hackernews", "Hacker News"]),
            Resource.score >= 30
        ).order_by(desc(Resource.score)).limit(3).all()

        # GitHub: source_name 可能是 "GITHUB" 或 "github"
        top_github = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.source_name.in_(["GITHUB", "github", "GitHub"]),
            Resource.score >= 30
        ).order_by(desc(Resource.score)).limit(3).all()

        # HuggingFace
        top_hf = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.source_name.in_(["huggingface", "HuggingFace", "HF"]),
            Resource.score >= 40  # HF 要求稍高
        ).order_by(desc(Resource.score)).limit(2).all()

        # 其他源 (twitter, arxiv 等)
        other_sources = ["twitter", "TWITTER", "arxiv", "arXiv", "reddit"]
        top_other = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.source_name.in_(other_sources),
            Resource.score >= 30
        ).order_by(desc(Resource.score)).limit(2).all()

        # 生成摘要
        summary = _generate_daily_summary(all_resources, sources_breakdown)

        # 提取热门话题
        trending_topics = _extract_trending_topics(all_resources)

        # 创建汇总记录
        digest = DailyDigest(
            date=target_date,
            total_signals=len(all_resources),
            sources_breakdown=sources_breakdown,
            top_hn_ids=[r.id for r in top_hn],
            top_github_ids=[r.id for r in top_github],
            top_hf_ids=[r.id for r in top_hf],
            top_other_ids=[r.id for r in top_other],
            summary=summary,
            trending_topics=trending_topics
        )

        db.add(digest)
        db.commit()
        db.refresh(digest)

        logger.info(f"[DailyDigest] {target_date} 生成成功: {len(top_hn)}条HN + {len(top_github)}条GitHub + {len(top_hf)}条HF")

        return digest

    except Exception as e:
        logger.error(f"[DailyDigest] 生成失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def generate_weekly_digest(week_start: str = None) -> WeeklyDigest:
    """生成每周精选汇总

    Args:
        week_start: 周一日期 "YYYY-MM-DD"，默认为上周一

    Returns:
        WeeklyDigest 对象

    逻辑:
        - 综合 Top 10: 按 score 排序
        - 分领域精选 (基于 domain 字段):
          - 人工智能 Top 3
          - 软件编程 Top 3
          - 商业科技 Top 2
          - 产品设计 Top 2
    """
    db = SessionLocal()

    try:
        # 确定周一和周日
        if week_start is None:
            today = datetime.utcnow()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            week_start = last_monday.strftime("%Y-%m-%d")

        week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        week_end_dt = week_start_dt + timedelta(days=6)
        week_end = week_end_dt.strftime("%Y-%m-%d")

        logger.info(f"[WeeklyDigest] 开始生成 {week_start} ~ {week_end} 的每周精选")

        # 检查是否已存在
        existing = db.query(WeeklyDigest).filter(WeeklyDigest.week_start == week_start).first()
        if existing:
            logger.warning(f"[WeeklyDigest] {week_start} 已存在，跳过生成")
            return existing

        # 查询本周所有资源
        start_time = f"{week_start} 00:00:00"
        end_time = f"{week_end} 23:59:59"

        all_resources = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time
        ).all()

        logger.info(f"[WeeklyDigest] 找到 {len(all_resources)} 条资源")

        # 按来源分组统计
        sources_breakdown = {}
        for r in all_resources:
            sources_breakdown[r.source_name] = sources_breakdown.get(r.source_name, 0) + 1

        # 综合 Top 10
        top_10 = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time
        ).order_by(desc(Resource.score)).limit(10).all()

        # 分领域精选 (基于 domain 字段)
        # 人工智能 (对应原来的 "技术突破" + "论文研究")
        top_breakthroughs = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.domain == "人工智能"
        ).order_by(desc(Resource.score)).limit(3).all()

        # 软件编程 (对应原来的 "开源工具")
        top_tools = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.domain == "软件编程"
        ).order_by(desc(Resource.score)).limit(3).all()

        # 商业科技 (对应原来的 "行业动态")
        top_papers = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.domain == "商业科技"
        ).order_by(desc(Resource.score)).limit(2).all()

        # 产品设计
        top_news = db.query(Resource).filter(
            Resource.created_at >= start_time,
            Resource.created_at <= end_time,
            Resource.domain == "产品设计"
        ).order_by(desc(Resource.score)).limit(2).all()

        # 生成摘要
        summary = _generate_weekly_summary(all_resources, sources_breakdown)

        # 提取热门话题和关键词
        trending_topics = _extract_trending_topics(all_resources)
        hot_keywords = _extract_hot_keywords(all_resources)

        # 创建汇总记录
        digest = WeeklyDigest(
            week_start=week_start,
            week_end=week_end,
            total_signals=len(all_resources),
            sources_breakdown=sources_breakdown,
            top_10_ids=[r.id for r in top_10],
            top_breakthroughs=[r.id for r in top_breakthroughs],
            top_tools=[r.id for r in top_tools],
            top_papers=[r.id for r in top_papers],
            top_news=[r.id for r in top_news],
            summary=summary,
            trending_topics=trending_topics,
            hot_keywords=hot_keywords
        )

        db.add(digest)
        db.commit()
        db.refresh(digest)

        logger.info(f"[WeeklyDigest] {week_start} 生成成功: Top10={len(top_10)}, 人工智能={len(top_breakthroughs)}")

        return digest

    except Exception as e:
        logger.error(f"[WeeklyDigest] 生成失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _generate_daily_summary(resources: List[Resource], sources: Dict) -> str:
    """生成每日摘要"""
    if not resources:
        return "今日暂无技术资源"

    total = len(resources)
    # Resource.score 是 0-100，转换为 1-5 星显示
    avg_score = sum(r.score for r in resources if r.score) / total if total > 0 else 0
    avg_star = avg_score / 20  # 100分制 → 5星制

    source_str = ", ".join([f"{k}({v}条)" for k, v in sources.items()])

    return f"今日共收录 {total} 条技术资源，平均评分 {avg_star:.1f}星。来源分布: {source_str}。"


def _generate_weekly_summary(resources: List[Resource], sources: Dict) -> str:
    """生成每周摘要"""
    if not resources:
        return "本周暂无技术资源"

    total = len(resources)
    # score >= 85 对应精选内容
    featured = len([r for r in resources if r.score and r.score >= 85])

    source_str = ", ".join([f"{k}({v}条)" for k, v in sources.items()])

    return f"本周共收录 {total} 条技术资源，其中 {featured} 条精选内容。来源分布: {source_str}。"


def _extract_trending_topics(resources: List[Resource]) -> List[str]:
    """提取热门话题标签"""
    # 基于 domain 统计
    topics = {}
    for r in resources:
        if r.domain:
            topics[r.domain] = topics.get(r.domain, 0) + 1

    # 按频率排序
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics[:5]]


def _extract_hot_keywords(resources: List[Resource]) -> List[str]:
    """提取高频关键词"""
    # 统计 title 中的常见技术词
    keywords_count = {}
    tech_keywords = ["AI", "GPT", "LLM", "ML", "模型", "Claude", "ChatGPT",
                     "开源", "GitHub", "Python", "Rust", "Go", "Agent", "RAG"]

    for r in resources:
        title_lower = r.title.lower() if r.title else ""
        for kw in tech_keywords:
            if kw.lower() in title_lower:
                keywords_count[kw] = keywords_count.get(kw, 0) + 1

    # 按频率排序
    sorted_kw = sorted(keywords_count.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, count in sorted_kw[:10]]
