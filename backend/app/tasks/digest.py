# File Input: 依赖 Signal 模型、DailyDigest/WeeklyDigest 模型、数据库会话
# File Output: 提供每日/每周汇总生成函数
# File Pos: 定时任务层，负责生成时间维度的信号聚合

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
import logging

from app.models.signal import Signal
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
        - HN头条 (3条): score_threshold >= 30, 按final_score排序
        - GitHub热门 (3条): 按final_score排序
        - HF重要模型 (2条): 按final_score排序
        - 其他源 (2条): 按final_score排序
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

        # 查询当天所有信号
        start_time = f"{target_date} 00:00:00"
        end_time = f"{target_date} 23:59:59"

        all_signals = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time
        ).all()

        logger.info(f"[DailyDigest] 找到 {len(all_signals)} 条信号")

        # 按来源分组统计
        sources_breakdown = {}
        for sig in all_signals:
            sources_breakdown[sig.source] = sources_breakdown.get(sig.source, 0) + 1

        # 分源精选
        top_hn = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.source == "hn",
            Signal.final_score >= 3
        ).order_by(desc(Signal.final_score)).limit(3).all()

        top_github = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.source == "github",
            Signal.final_score >= 3
        ).order_by(desc(Signal.final_score)).limit(3).all()

        top_hf = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.source == "huggingface",
            Signal.final_score >= 4  # HF要求更高评分
        ).order_by(desc(Signal.final_score)).limit(2).all()

        # 其他源
        other_sources = ["arxiv", "twitter", "reddit"]  # 未来的数据源
        top_other = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.source.in_(other_sources),
            Signal.final_score >= 3
        ).order_by(desc(Signal.final_score)).limit(2).all()

        # 生成摘要
        summary = _generate_daily_summary(all_signals, sources_breakdown)

        # 提取热门话题
        trending_topics = _extract_trending_topics(all_signals)

        # 创建汇总记录
        digest = DailyDigest(
            date=target_date,
            total_signals=len(all_signals),
            sources_breakdown=sources_breakdown,
            top_hn_ids=[s.id for s in top_hn],
            top_github_ids=[s.id for s in top_github],
            top_hf_ids=[s.id for s in top_hf],
            top_other_ids=[s.id for s in top_other],
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
        - 方案C (分类Top 3):
          - 技术突破 Top 3 (final_score >= 5, category="技术突破")
          - 开源工具 Top 3 (category="开源工具")
          - 论文研究 Top 2 (category="论文研究")
          - 行业动态 Top 2 (category="行业动态")
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

        # 查询本周所有信号
        start_time = f"{week_start} 00:00:00"
        end_time = f"{week_end} 23:59:59"

        all_signals = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time
        ).all()

        logger.info(f"[WeeklyDigest] 找到 {len(all_signals)} 条信号")

        # 按来源分组统计
        sources_breakdown = {}
        for sig in all_signals:
            sources_breakdown[sig.source] = sources_breakdown.get(sig.source, 0) + 1

        # 综合 Top 10
        top_10 = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time
        ).order_by(desc(Signal.final_score)).limit(10).all()

        # 分类精选 (基于category字段)
        top_breakthroughs = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.category == "技术突破"
        ).order_by(desc(Signal.final_score)).limit(3).all()

        top_tools = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.category == "开源工具"
        ).order_by(desc(Signal.final_score)).limit(3).all()

        top_papers = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.category == "论文研究"
        ).order_by(desc(Signal.final_score)).limit(2).all()

        top_news = db.query(Signal).filter(
            Signal.created_at >= start_time,
            Signal.created_at <= end_time,
            Signal.category == "行业动态"
        ).order_by(desc(Signal.final_score)).limit(2).all()

        # 生成摘要
        summary = _generate_weekly_summary(all_signals, sources_breakdown)

        # 提取热门话题和关键词
        trending_topics = _extract_trending_topics(all_signals)
        hot_keywords = _extract_hot_keywords(all_signals)

        # 创建汇总记录
        digest = WeeklyDigest(
            week_start=week_start,
            week_end=week_end,
            total_signals=len(all_signals),
            sources_breakdown=sources_breakdown,
            top_10_ids=[s.id for s in top_10],
            top_breakthroughs=[s.id for s in top_breakthroughs],
            top_tools=[s.id for s in top_tools],
            top_papers=[s.id for s in top_papers],
            top_news=[s.id for s in top_news],
            summary=summary,
            trending_topics=trending_topics,
            hot_keywords=hot_keywords
        )

        db.add(digest)
        db.commit()
        db.refresh(digest)

        logger.info(f"[WeeklyDigest] {week_start} 生成成功: Top10={len(top_10)}, 技术突破={len(top_breakthroughs)}")

        return digest

    except Exception as e:
        logger.error(f"[WeeklyDigest] 生成失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _generate_daily_summary(signals: List[Signal], sources: Dict) -> str:
    """生成每日摘要"""
    if not signals:
        return "今日暂无技术信号"

    total = len(signals)
    avg_score = sum(s.final_score for s in signals) / total if total > 0 else 0

    source_str = ", ".join([f"{k}({v}条)" for k, v in sources.items()])

    return f"今日共收录 {total} 条技术信号，平均评分 {avg_score:.1f}。来源分布: {source_str}。"


def _generate_weekly_summary(signals: List[Signal], sources: Dict) -> str:
    """生成每周摘要"""
    if not signals:
        return "本周暂无技术信号"

    total = len(signals)
    five_star = len([s for s in signals if s.final_score >= 5])

    source_str = ", ".join([f"{k}({v}条)" for k, v in sources.items()])

    return f"本周共收录 {total} 条技术信号，其中 {five_star} 条五星信号。来源分布: {source_str}。"


def _extract_trending_topics(signals: List[Signal]) -> List[str]:
    """提取热门话题标签"""
    # 简单实现: 基于category统计
    topics = {}
    for sig in signals:
        if sig.category:
            topics[sig.category] = topics.get(sig.category, 0) + 1

    # 按频率排序
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics[:5]]


def _extract_hot_keywords(signals: List[Signal]) -> List[str]:
    """提取高频关键词"""
    # 简单实现: 统计title中的常见技术词
    keywords_count = {}
    tech_keywords = ["AI", "GPT", "LLM", "ML", "模型", "Claude", "ChatGPT",
                     "开源", "GitHub", "Python", "Rust", "Go"]

    for sig in signals:
        title_lower = sig.title.lower()
        for kw in tech_keywords:
            if kw.lower() in title_lower:
                keywords_count[kw] = keywords_count.get(kw, 0) + 1

    # 按频率排序
    sorted_kw = sorted(keywords_count.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, count in sorted_kw[:10]]
