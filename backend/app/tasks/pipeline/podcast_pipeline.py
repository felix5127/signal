# Input: Podcast RSS/OPML, PodcastScraper, Transcriber, PodcastAnalyzer
# Output: Resource 记录 (含 transcript, chapters, qa_pairs)
# Position: 播客处理流水线
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
播客处理流水线

流程:
1. RSS 采集 - 使用 PodcastScraper 从 OPML 获取播客元数据
2. URL 去重 - 检查数据库中是否已存在 + DataTracker 追踪重复项
3. 音频转写 - 使用通义听悟转写音频内容 (可选，双路径: 新版 TranscriptionService → 旧版 Transcriber)
4. 内容分析 - 使用 PodcastAnalyzer 生成章节和 Q&A
5. 存储到数据库 - 保存到 Resource 表 + DataTracker 追踪收录
"""

from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.scrapers.podcast import PodcastScraper
from app.scrapers.favicon import FaviconFetcher
from app.services.source_service import SourceService
from app.services.data_tracker import DataTracker
from app.processors.podcast_analyzer import podcast_analyzer
from app.tasks.pipeline.stats import PodcastPipelineStats

logger = structlog.get_logger("pipeline")


async def run_podcast_pipeline(
    opml_path: Optional[str] = None,
    max_items_per_feed: int = 2,
    enable_transcription: bool = True,
    max_daily_transcription: int = 5,
    dry_run: bool = False,
) -> PodcastPipelineStats:
    """
    运行播客处理流水线（支持转写）

    流程：
    1. RSS 采集 - 使用 PodcastScraper 从 OPML 获取播客元数据
    2. URL 去重 - 检查数据库中是否已存在
    3. 音频转写 - 使用通义听悟转写音频内容
    4. 存储到数据库 - 保存转写后的播客内容

    Args:
        opml_path: OPML 文件路径（可选，默认使用配置中的路径）
        max_items_per_feed: 每个播客源最多抓取条目数
        enable_transcription: 是否启用转写
        max_daily_transcription: 每日最多转写数量（控制成本）
        dry_run: 仅运行采集+去重+转写设置，不实际写入数据库

    Returns:
        PodcastPipelineStats 统计信息
    """
    stats = PodcastPipelineStats()
    tracker = DataTracker(pipeline="podcast")
    logger.info("podcast.pipeline.started", transcription_enabled=enable_transcription)

    # ========== 1. RSS 采集 ==========
    logger.info("podcast.scrape.started")

    # 使用配置中的 OPML 路径
    if opml_path is None and hasattr(config, 'podcast') and hasattr(config.podcast, 'opml_path'):
        opml_path = config.podcast.opml_path

    podcast_scraper = PodcastScraper()
    raw_signals = await podcast_scraper.scrape(
        opml_path=opml_path,
        max_items_per_feed=max_items_per_feed
    )
    stats.scraped_count = len(raw_signals)

    logger.info("podcast.scrape.completed", count=stats.scraped_count)

    if not raw_signals:
        logger.info("podcast.scrape.empty")
        return stats

    # ========== 2. URL 去重检查 ==========
    logger.info("podcast.dedupe.started", items_in=len(raw_signals))

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
                source_name = (s.metadata or {}).get("podcast_name", "podcast")
                tracker.track_filtered(
                    title=s.title, url=s.url, source=source_name,
                    reason="重复内容", stage="dedup",
                )
            else:
                new_signals.append(s)
        duplicate_count = len(raw_signals) - len(new_signals)

        logger.info("podcast.dedupe.completed", duplicates=duplicate_count, new_count=len(new_signals))

        if not new_signals:
            logger.info("podcast.dedupe.all_duplicates")
            return stats

        raw_signals = new_signals

    finally:
        db.close()

    # ========== 3. 音频转写（可选） ==========
    transcription_enabled = enable_transcription
    transcriber = None
    new_transcription_service = None
    use_new_transcriber = False

    if transcription_enabled:
        # 优先尝试新版 TranscriptionService
        try:
            from app.processors.transcription_service import TranscriptionService
            new_ts = TranscriptionService(config.tingwu)
            if new_ts.is_available():
                new_transcription_service = new_ts
                use_new_transcriber = True
                logger.info("podcast.transcription.using_new_service")
            else:
                missing = new_ts.validate_config()
                logger.warning("podcast.transcription.new_service_unavailable", missing=missing)
        except ImportError:
            pass

        # 降级到旧版 Transcriber
        if not use_new_transcriber:
            try:
                from app.processors.transcriber import Transcriber
                transcriber = Transcriber()

                if not transcriber.access_key_id or not transcriber.access_key_secret:
                    logger.warning("podcast.transcription.legacy_not_configured")
                    transcription_enabled = False
                else:
                    logger.info("podcast.transcription.using_legacy")

            except ImportError:
                logger.warning("podcast.transcription.module_not_found")
                transcription_enabled = False

    # 限制转写数量
    items_to_transcribe = raw_signals[:max_daily_transcription] if transcription_enabled else []

    # ========== dry_run 提前返回 ==========
    if dry_run:
        logger.info("podcast.pipeline.dry_run_complete",
                     scraped=stats.scraped_count,
                     duplicates=duplicate_count,
                     would_save=len(raw_signals),
                     would_transcribe=len(items_to_transcribe))
        return stats

    # ========== 4. 存储到数据库 ==========
    logger.info("podcast.save.started", items_in=len(raw_signals),
                transcribe_count=len(items_to_transcribe))

    db: Session = SessionLocal()
    try:
        for i, signal in enumerate(raw_signals):
            try:
                logger.debug("podcast.save.processing", index=i + 1, total=len(raw_signals),
                             title=signal.title[:50])

                # 获取播客元数据
                metadata = signal.metadata or {}
                audio_url = metadata.get("audio_url", "")

                # 转写音频
                transcribed_text = None
                transcribed_duration = 0

                if transcription_enabled and signal in items_to_transcribe and audio_url:
                    try:
                        # ── 新版转写服务 ──
                        if use_new_transcriber and new_transcription_service is not None:
                            result = await new_transcription_service.transcribe(
                                media_url=audio_url,
                                media_type="audio",
                                max_daily=max_daily_transcription,
                            )
                            transcribed_text = result.text
                            transcribed_duration = result.duration
                            stats.transcribed_count += 1
                        # ── 旧版转写器 ──
                        elif transcriber is not None:
                            result = await transcriber.transcribe(
                                media_url=audio_url,
                                media_type="audio",
                                max_wait=1800,  # 30分钟
                                poll_interval=10,
                            )
                            if result:
                                transcribed_text = result.text
                                transcribed_duration = result.duration
                                stats.transcribed_count += 1
                    except Exception as e:
                        logger.error("podcast.transcription.error",
                                     url=audio_url[:80], error=str(e))

                # ========== 播客内容分析 ==========
                chapters = None
                qa_pairs = None
                if transcribed_text and len(transcribed_text) >= 100:
                    try:
                        analysis = await podcast_analyzer.analyze(
                            transcript=transcribed_text,
                            duration=transcribed_duration or metadata.get("duration", 3600),
                        )
                        chapters = [
                            {"time": ch.time, "title": ch.title, "summary": ch.summary}
                            for ch in analysis.chapters
                        ]
                        qa_pairs = [
                            {"question": qa.question, "answer": qa.answer, "timestamp": qa.timestamp}
                            for qa in analysis.qa_pairs
                        ]
                        logger.info("podcast.analysis.completed",
                                    chapters=len(chapters), qa_pairs=len(qa_pairs))
                    except Exception as e:
                        logger.warning("podcast.analysis.error",
                                       title=signal.title[:50], error=str(e))

                # 创建 Resource 对象
                resource = Resource(
                    type="podcast",
                    url_hash=Resource.generate_url_hash(signal.url),
                    source_name=metadata.get("podcast_name", "podcast"),
                    source_icon_url=FaviconFetcher.get_favicon(signal.url),
                    thumbnail_url=metadata.get("thumbnail_url"),
                    url=signal.url,
                    title=signal.title,
                    one_sentence_summary=signal.title,
                    content_markdown=signal.content,  # 原始描述 (Show Notes)
                    content_html=signal.content,
                    domain="科技播客",
                    tags=["播客", "科技"],
                    score=3,
                    is_featured=False,
                    language="zh",
                    published_at=signal.source_created_at,
                    created_at=datetime.now(),
                    status="published",
                    # 播客专用字段
                    audio_url=audio_url,
                    duration=transcribed_duration or metadata.get("duration", 0),
                    transcript=transcribed_text,
                    chapters=chapters,
                    qa_pairs=qa_pairs,
                )

                db.add(resource)
                db.commit()
                stats.saved_count += 1
                tracker.track_collected(
                    title=signal.title, url=signal.url,
                    source=metadata.get("podcast_name", "podcast"),
                    reason="播客收录", stage="save",
                )

            except Exception as e:
                db.rollback()
                stats.failed_count += 1
                logger.error("podcast.save.item_error", url=signal.url[:80], error=str(e))

        logger.info("podcast.save.completed", saved=stats.saved_count, total=len(raw_signals))

    finally:
        db.close()

    # ========== 统计 ==========
    logger.info("podcast.pipeline.summary",
                scraped=stats.scraped_count,
                transcribed=stats.transcribed_count,
                saved=stats.saved_count,
                failed=stats.failed_count)

    # ========== 记录采集结果 ==========
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        source_service.record_run(
            source_type="podcast",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            dedup_filtered_count=len(raw_signals),
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
        record_db.close()
    except Exception as e:
        logger.error("podcast.record_run.failed", error=str(e))

    # ========== 飞书数据追踪 ==========
    try:
        await tracker.flush()
    except Exception as e:
        logger.warning("podcast.tracker.flush_failed", error=str(e))

    return stats
