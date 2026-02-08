"""
[INPUT]: 依赖 scrapers/xgoing 的 XGoingScraper, models/resource 的 Resource, config 的配置, services/data_tracker 的 DataTracker
[OUTPUT]: 对外提供 run_twitter_pipeline 函数
[POS]: Twitter 采集流水线，跳过 LLM 直接存储推文
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.scrapers.xgoing import XGoingScraper
from app.scrapers.favicon import FaviconFetcher
from app.services.source_service import SourceService
from app.services.data_tracker import DataTracker
from app.tasks.pipeline.stats import TwitterPipelineStats

logger = structlog.get_logger("pipeline")


async def run_twitter_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 2,
    dry_run: bool = False,
) -> TwitterPipelineStats:
    """
    运行 Twitter 推文处理流水线（简化版：跳过 LLM 筛选，直接保存）

    流程：
    1. XGoing 采集 - 使用 XGoingScraper 从 OPML 获取 Twitter 推文
    2. URL 去重 - 检查数据库中是否已存在
    3. 直接存储 - 跳过 LLM 分析，直接保存推文

    Args:
        opml_path: OPML 文件路径（可选，默认使用配置中的路径）
        min_value_score: 已废弃，保留参数兼容性
        dry_run: 仅模拟运行，不写入数据库

    Returns:
        TwitterPipelineStats 统计信息
    """
    stats = TwitterPipelineStats()
    tracker = DataTracker(pipeline="twitter")
    print(f"\n{'='*60}")
    print(f"[TwitterPipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[TwitterPipeline] Mode: Skip LLM, save all tweets")
    print(f"{'='*60}\n")

    # ========== 1. XGoing 采集 ==========
    print("[TwitterPipeline] Step 1: Scraping Twitter via XGo.ing...")

    # 使用配置中的 OPML 路径
    if opml_path is None and hasattr(config.twitter, 'opml_path'):
        opml_path = config.twitter.opml_path

    xgoing_scraper = XGoingScraper()
    raw_signals = await xgoing_scraper.scrape(opml_path=opml_path)
    stats.scraped_count = len(raw_signals)

    print(f"[TwitterPipeline] Scraped {stats.scraped_count} tweets from XGo.ing\n")

    if not raw_signals:
        print("[TwitterPipeline] No tweets scraped, exiting.\n")
        await tracker.flush()
        return stats

    # ========== 2. URL 去重检查 ==========
    print("[TwitterPipeline] Step 2: Checking for duplicates...")

    db: Session = SessionLocal()
    try:
        # 获取已存在的 URL hash
        existing_urls = set()
        for signal in raw_signals:
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                existing_urls.add(signal.url)

        # 过滤掉已存在的 + 追踪重复项
        new_signals = []
        for s in raw_signals:
            if s.url in existing_urls:
                source_name = (s.metadata or {}).get("source_name", "twitter")
                tracker.track_filtered(
                    title=s.title, url=s.url, source=source_name,
                    reason="重复内容", stage="dedup",
                )
            else:
                new_signals.append(s)
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[TwitterPipeline] Found {duplicate_count} duplicates, {len(new_signals)} new tweets\n")

        if not new_signals:
            print("[TwitterPipeline] All tweets already exist, exiting.\n")
            await tracker.flush()
            return stats

        raw_signals = new_signals

    finally:
        db.close()

    # ========== dry_run 提前返回 ==========
    if dry_run:
        logger.info("twitter.pipeline.dry_run_complete",
                     scraped=stats.scraped_count,
                     duplicates=duplicate_count,
                     would_save=len(raw_signals))
        await tracker.flush()
        return stats

    # ========== 3. 直接存储（跳过 LLM）==========
    print("[TwitterPipeline] Step 3: Saving tweets directly (skipping LLM analysis)...")

    db: Session = SessionLocal()
    try:
        for i, signal in enumerate(raw_signals):
            try:
                print(f"  [{i+1}/{len(raw_signals)}] Saving: {signal.title[:50]}...")

                # 获取推文元数据
                metadata = signal.metadata or {}

                # 创建 Resource 对象
                resource = Resource(
                    type="tweet",
                    url_hash=Resource.generate_url_hash(signal.url),
                    source_name=metadata.get("source_name", "twitter"),
                    source_icon_url=FaviconFetcher.get_favicon(signal.url),
                    url=signal.url,
                    title=signal.title,
                    one_sentence_summary=signal.title,  # 使用标题作为摘要
                    content_html=signal.content,  # HTML 内容存储在 content_html
                    domain=metadata.get("domain", ""),
                    tags=metadata.get("tags", []),
                    score=3,  # 默认中等评分
                    is_featured=False,
                    language=metadata.get("language", "en"),
                    published_at=signal.source_created_at,
                    created_at=datetime.now(),
                    status="published",
                )

                db.add(resource)
                db.commit()
                stats.saved_count += 1
                tracker.track_collected(
                    title=signal.title, url=signal.url,
                    source=metadata.get("source_name", "twitter"),
                    reason="直接收录", stage="save",
                )
                print(f"    -> Saved")

            except Exception as e:
                db.rollback()
                stats.failed_count += 1
                print(f"    -> Error: {e}")

        print(f"\n[TwitterPipeline] Saved {stats.saved_count}/{len(raw_signals)} tweets\n")

    finally:
        db.close()

    # ========== 统计 ==========
    print(f"{'='*60}")
    print("[TwitterPipeline] Summary:")
    print(f"  - Scraped: {stats.scraped_count}")
    print(f"  - Duplicates: {stats.scraped_count - len(raw_signals)}")
    print(f"  - Saved: {stats.saved_count}")
    print(f"  - Failed: {stats.failed_count}")
    print(f"  - LLM tokens: 0 (skipped)")
    print(f"{'='*60}\n")

    # ========== 记录采集结果 ==========
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        source_service.record_run(
            source_type="twitter",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            dedup_filtered_count=len(raw_signals),
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
        record_db.close()
    except Exception as e:
        print(f"[TwitterPipeline] Failed to record run: {e}")

    # ========== 飞书数据追踪 ==========
    try:
        await tracker.flush()
    except Exception as e:
        logger.warning("twitter.tracker.flush_failed", error=str(e))

    return stats
