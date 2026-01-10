# File Input: 依赖 FastAPI、数据库会话、DailyDigest/WeeklyDigest 模型
# File Output: 提供每日/每周精选的API端点
# File Pos: API路由层，对外暴露汇总查询接口

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.digest import DailyDigest, WeeklyDigest
from app.models.signal import Signal
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 响应模型 ==========

class SignalBrief(BaseModel):
    """信号简要信息"""
    id: int
    title: str
    url: str
    source: str
    category: Optional[str] = None
    final_score: int
    created_at: str

    @field_validator('created_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True


class DailyDigestResponse(BaseModel):
    """每日精选响应"""
    date: str
    total_signals: int
    sources_breakdown: dict
    top_hn: List[SignalBrief]
    top_github: List[SignalBrief]
    top_hf: List[SignalBrief]
    top_other: List[SignalBrief]
    summary: str
    trending_topics: List[str]
    created_at: str

    class Config:
        from_attributes = True


class WeeklyDigestResponse(BaseModel):
    """每周精选响应"""
    week_start: str
    week_end: str
    total_signals: int
    sources_breakdown: dict
    top_10: List[SignalBrief]
    top_breakthroughs: List[SignalBrief]
    top_tools: List[SignalBrief]
    top_papers: List[SignalBrief]
    top_news: List[SignalBrief]
    summary: str
    trending_topics: List[str]
    hot_keywords: List[str]
    created_at: str

    class Config:
        from_attributes = True


# ========== API 端点 ==========

@router.get("/digest/today", response_model=DailyDigestResponse)
def get_today_digest(db: Session = Depends(get_db)):
    """获取今日精选 (昨日汇总)

    Returns:
        昨日的每日精选汇总
    """
    # 查找昨天的汇总
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    digest = db.query(DailyDigest).filter(DailyDigest.date == yesterday).first()

    if not digest:
        raise HTTPException(
            status_code=404,
            detail=f"昨日精选 ({yesterday}) 尚未生成，请等待每日 07:00 自动汇总"
        )

    # 获取信号详情
    top_hn = db.query(Signal).filter(Signal.id.in_(digest.top_hn_ids)).all() if digest.top_hn_ids else []
    top_github = db.query(Signal).filter(Signal.id.in_(digest.top_github_ids)).all() if digest.top_github_ids else []
    top_hf = db.query(Signal).filter(Signal.id.in_(digest.top_hf_ids)).all() if digest.top_hf_ids else []
    top_other = db.query(Signal).filter(Signal.id.in_(digest.top_other_ids)).all() if digest.top_other_ids else []

    return DailyDigestResponse(
        date=digest.date,
        total_signals=digest.total_signals,
        sources_breakdown=digest.sources_breakdown,
        top_hn=[SignalBrief.from_orm(s) for s in top_hn],
        top_github=[SignalBrief.from_orm(s) for s in top_github],
        top_hf=[SignalBrief.from_orm(s) for s in top_hf],
        top_other=[SignalBrief.from_orm(s) for s in top_other],
        summary=digest.summary or "",
        trending_topics=digest.trending_topics or [],
        created_at=digest.created_at.isoformat()
    )


@router.get("/digest/date/{date}", response_model=DailyDigestResponse)
def get_digest_by_date(date: str, db: Session = Depends(get_db)):
    """获取指定日期的每日精选

    Args:
        date: 日期字符串 "YYYY-MM-DD"
    """
    digest = db.query(DailyDigest).filter(DailyDigest.date == date).first()

    if not digest:
        raise HTTPException(status_code=404, detail=f"未找到 {date} 的每日精选")

    # 获取信号详情
    top_hn = db.query(Signal).filter(Signal.id.in_(digest.top_hn_ids)).all() if digest.top_hn_ids else []
    top_github = db.query(Signal).filter(Signal.id.in_(digest.top_github_ids)).all() if digest.top_github_ids else []
    top_hf = db.query(Signal).filter(Signal.id.in_(digest.top_hf_ids)).all() if digest.top_hf_ids else []
    top_other = db.query(Signal).filter(Signal.id.in_(digest.top_other_ids)).all() if digest.top_other_ids else []

    return DailyDigestResponse(
        date=digest.date,
        total_signals=digest.total_signals,
        sources_breakdown=digest.sources_breakdown,
        top_hn=[SignalBrief.from_orm(s) for s in top_hn],
        top_github=[SignalBrief.from_orm(s) for s in top_github],
        top_hf=[SignalBrief.from_orm(s) for s in top_hf],
        top_other=[SignalBrief.from_orm(s) for s in top_other],
        summary=digest.summary or "",
        trending_topics=digest.trending_topics or [],
        created_at=digest.created_at.isoformat()
    )


@router.get("/digest/week", response_model=WeeklyDigestResponse)
def get_this_week_digest(db: Session = Depends(get_db)):
    """获取本周精选 (上周汇总)

    Returns:
        上周的每周精选汇总
    """
    # 查找上周一
    today = datetime.utcnow()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    week_start = last_monday.strftime("%Y-%m-%d")

    digest = db.query(WeeklyDigest).filter(WeeklyDigest.week_start == week_start).first()

    if not digest:
        raise HTTPException(
            status_code=404,
            detail=f"上周精选 ({week_start}) 尚未生成，请等待每周一 08:00 自动汇总"
        )

    # 获取信号详情
    top_10 = db.query(Signal).filter(Signal.id.in_(digest.top_10_ids)).all() if digest.top_10_ids else []
    top_breakthroughs = db.query(Signal).filter(Signal.id.in_(digest.top_breakthroughs)).all() if digest.top_breakthroughs else []
    top_tools = db.query(Signal).filter(Signal.id.in_(digest.top_tools)).all() if digest.top_tools else []
    top_papers = db.query(Signal).filter(Signal.id.in_(digest.top_papers)).all() if digest.top_papers else []
    top_news = db.query(Signal).filter(Signal.id.in_(digest.top_news)).all() if digest.top_news else []

    return WeeklyDigestResponse(
        week_start=digest.week_start,
        week_end=digest.week_end,
        total_signals=digest.total_signals,
        sources_breakdown=digest.sources_breakdown,
        top_10=[SignalBrief.from_orm(s) for s in top_10],
        top_breakthroughs=[SignalBrief.from_orm(s) for s in top_breakthroughs],
        top_tools=[SignalBrief.from_orm(s) for s in top_tools],
        top_papers=[SignalBrief.from_orm(s) for s in top_papers],
        top_news=[SignalBrief.from_orm(s) for s in top_news],
        summary=digest.summary or "",
        trending_topics=digest.trending_topics or [],
        hot_keywords=digest.hot_keywords or [],
        created_at=digest.created_at.isoformat()
    )


@router.get("/digest/weeks", response_model=List[WeeklyDigestResponse])
def get_recent_weeks(limit: int = 4, db: Session = Depends(get_db)):
    """获取最近N周的精选汇总

    Args:
        limit: 返回最近N周，默认4周
    """
    digests = db.query(WeeklyDigest).order_by(WeeklyDigest.week_start.desc()).limit(limit).all()

    results = []
    for digest in digests:
        top_10 = db.query(Signal).filter(Signal.id.in_(digest.top_10_ids)).all() if digest.top_10_ids else []
        top_breakthroughs = db.query(Signal).filter(Signal.id.in_(digest.top_breakthroughs)).all() if digest.top_breakthroughs else []
        top_tools = db.query(Signal).filter(Signal.id.in_(digest.top_tools)).all() if digest.top_tools else []
        top_papers = db.query(Signal).filter(Signal.id.in_(digest.top_papers)).all() if digest.top_papers else []
        top_news = db.query(Signal).filter(Signal.id.in_(digest.top_news)).all() if digest.top_news else []

        results.append(WeeklyDigestResponse(
            week_start=digest.week_start,
            week_end=digest.week_end,
            total_signals=digest.total_signals,
            sources_breakdown=digest.sources_breakdown,
            top_10=[SignalBrief.from_orm(s) for s in top_10],
            top_breakthroughs=[SignalBrief.from_orm(s) for s in top_breakthroughs],
            top_tools=[SignalBrief.from_orm(s) for s in top_tools],
            top_papers=[SignalBrief.from_orm(s) for s in top_papers],
            top_news=[SignalBrief.from_orm(s) for s in top_news],
            summary=digest.summary or "",
            trending_topics=digest.trending_topics or [],
            hot_keywords=digest.hot_keywords or [],
            created_at=digest.created_at.isoformat()
        ))

    return results
