# Input: Video RSS/OPML, VideoScraper, Transcriber, PodcastAnalyzer, DataTracker
# Output: Resource 记录 (含 transcript, chapters, qa_pairs)
# Position: 视频处理流水线
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
视频处理流水线

流程:
1. RSS 采集 - 使用 VideoScraper 从 OPML 获取视频元数据
2. URL 去重 - 检查数据库中是否已存在
3. 视频转写 - 使用通义听悟转写视频内容 (可选)
4. 内容分析 - 使用 PodcastAnalyzer 生成章节和 Q&A
5. 存储到数据库 - 保存到 Resource 表
"""

from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.scrapers.video import VideoScraper
from app.scrapers.favicon import FaviconFetcher
from app.services.source_service import SourceService
from app.services.data_tracker import DataTracker
from app.processors.podcast_analyzer import podcast_analyzer
from app.tasks.pipeline.stats import VideoPipelineStats

logger = structlog.get_logger("pipeline")


async def run_video_pipeline(
    opml_path: Optional[str] = None,
    max_items_per_feed: int = 1,
    enable_transcription: bool = True,
    max_daily_transcription: int = 2,
    dry_run: bool = False,
) -> VideoPipelineStats:
    """
    运行视频处理流水线（支持转写）

    流程：
    1. RSS 采集 - 使用 VideoScraper 从 OPML 获取视频元数据
    2. URL 去重 - 检查数据库中是否已存在
    3. 视频转写 - 使用通义听悟转写视频内容
    4. 存储到数据库 - 保存转写后的视频内容

    Args:
        opml_path: OPML 文件路径（可选，默认使用配置中的路径）
        max_items_per_feed: 每个视频源最多抓取条目数
        enable_transcription: 是否启用转写
        max_daily_transcription: 每日最多转写数量（控制成本）
        dry_run: 仅模拟运行，不写入数据库

    Returns:
        VideoPipelineStats 统计信息
    """
    stats = VideoPipelineStats()
    tracker = DataTracker(pipeline="video")
    print(f"\n{'='*60}")
    print(f"[VideoPipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[VideoPipeline] Transcription: {'Enabled' if enable_transcription else 'Disabled'}")
    print(f"{'='*60}\n")

    # ========== 1. RSS 采集 ==========
    print("[VideoPipeline] Step 1: Scraping videos from RSS feeds...")

    # 使用配置中的 OPML 路径
    if opml_path is None and hasattr(config, 'video') and hasattr(config.video, 'opml_path'):
        opml_path = config.video.opml_path

    video_scraper = VideoScraper()
    raw_signals = await video_scraper.scrape(
        opml_path=opml_path,
        max_items_per_feed=max_items_per_feed
    )
    stats.scraped_count = len(raw_signals)

    print(f"[VideoPipeline] Scraped {stats.scraped_count} videos\n")

    if not raw_signals:
        print("[VideoPipeline] No videos scraped, exiting.\n")
        await tracker.flush()
        return stats

    # ========== 2. URL 去重检查 ==========
    print("[VideoPipeline] Step 2: Checking for duplicates...")

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
                source_name = (s.metadata or {}).get("channel_name", "youtube")
                tracker.track_filtered(
                    title=s.title, url=s.url, source=source_name,
                    reason="重复内容", stage="dedup",
                )
            else:
                new_signals.append(s)
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[VideoPipeline] Found {duplicate_count} duplicates, {len(new_signals)} new videos\n")

        if not new_signals:
            print("[VideoPipeline] All videos already exist, exiting.\n")
            await tracker.flush()
            return stats

        raw_signals = new_signals

    finally:
        db.close()

    # ========== 3. 视频转写（可选） ==========
    transcription_enabled = enable_transcription
    transcriber = None

    if transcription_enabled:
        try:
            from app.processors.transcriber import Transcriber
            transcriber = Transcriber()

            if not transcriber.access_key_id or not transcriber.access_key_secret:
                print("[VideoPipeline] Transcriber 未配置，跳过转写")
                transcription_enabled = False
            else:
                print("[VideoPipeline] Transcriber 已初始化")

        except ImportError:
            print("[VideoPipeline] Transcriber 模块未找到，跳过转写")
            transcription_enabled = False

    # 限制转写数量（视频转写成本高，默认只转写2个）
    items_to_transcribe = raw_signals[:max_daily_transcription] if transcription_enabled else []

    # ========== dry_run 提前返回 ==========
    if dry_run:
        logger.info("video.pipeline.dry_run_complete",
                     scraped=stats.scraped_count,
                     duplicates=duplicate_count,
                     would_save=len(raw_signals),
                     would_transcribe=len(items_to_transcribe))
        await tracker.flush()
        return stats

    # ========== 4. 存储到数据库 ==========
    print(f"[VideoPipeline] Step 3: Saving videos...")
    if transcription_enabled:
        print(f"[VideoPipeline] Will transcribe {len(items_to_transcribe)}/{len(raw_signals)} videos\n")

    db: Session = SessionLocal()
    try:
        for i, signal in enumerate(raw_signals):
            try:
                print(f"  [{i+1}/{len(raw_signals)}] Processing: {signal.title[:50]}...")

                # 获取视频元数据
                metadata = signal.metadata or {}

                # 转写视频（通义听悟支持直接处理 YouTube URL）
                transcribed_text = None
                transcribed_duration = 0

                if transcription_enabled and signal in items_to_transcribe:
                    video_url = signal.url
                    print(f"    -> Transcribing: {video_url[:60]}...")
                    try:
                        result = await transcriber.transcribe(
                            media_url=video_url,
                            media_type="video",
                            max_wait=1800,  # 30分钟
                            poll_interval=10,
                        )
                        if result:
                            transcribed_text = result.text
                            transcribed_duration = result.duration
                            stats.transcribed_count += 1
                            print(f"    -> Transcription completed ({len(transcribed_text)} chars)")
                        else:
                            print(f"    -> Transcription failed")
                    except Exception as e:
                        print(f"    -> Transcription error: {e}")

                # ========== 视频内容分析 ==========
                chapters = None
                qa_pairs = None
                if transcribed_text and len(transcribed_text) >= 100:
                    print(f"    -> Analyzing video content...")
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
                        print(f"    -> Analysis: {len(chapters)} chapters, {len(qa_pairs)} Q&A pairs")
                    except Exception as e:
                        print(f"    -> Analysis error: {e}")

                # 创建 Resource 对象
                resource = Resource(
                    type="video",
                    url_hash=Resource.generate_url_hash(signal.url),
                    source_name=metadata.get("channel_name", "youtube"),
                    source_icon_url=FaviconFetcher.get_favicon(signal.url),
                    thumbnail_url=metadata.get("thumbnail_url"),
                    url=signal.url,
                    title=signal.title,
                    one_sentence_summary=signal.title[:500],
                    content_markdown=signal.content,  # 原始描述
                    content_html=signal.content,
                    domain="科技视频",
                    tags=["视频", "AI", "科技"],
                    score=3,
                    is_featured=False,
                    language=metadata.get("language", "en"),
                    published_at=signal.source_created_at,
                    created_at=datetime.now(),
                    status="published",
                    # 视频专用字段
                    duration=transcribed_duration or metadata.get("duration", 0),
                    transcript=transcribed_text,
                    chapters=chapters,
                    qa_pairs=qa_pairs,
                    extra_metadata={
                        "video_id": metadata.get("video_id"),
                    },
                )

                db.add(resource)
                db.commit()
                stats.saved_count += 1
                tracker.track_collected(
                    title=signal.title, url=signal.url,
                    source=metadata.get("channel_name", "youtube"),
                    reason="视频收录", stage="save",
                )
                print(f"    -> Saved")

            except Exception as e:
                db.rollback()
                stats.failed_count += 1
                print(f"    -> Error: {e}")

        print(f"\n[VideoPipeline] Saved {stats.saved_count}/{len(raw_signals)} videos\n")

    finally:
        db.close()

    # ========== 统计 ==========
    print(f"{'='*60}")
    print("[VideoPipeline] Summary:")
    print(f"  - Scraped: {stats.scraped_count}")
    print(f"  - Duplicates: {stats.scraped_count - len(raw_signals)}")
    print(f"  - Transcribed: {stats.transcribed_count}")
    print(f"  - Saved: {stats.saved_count}")
    print(f"  - Failed: {stats.failed_count}")
    print(f"{'='*60}\n")

    # ========== 记录采集结果 ==========
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        source_service.record_run(
            source_type="video",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            dedup_filtered_count=len(raw_signals),
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
        record_db.close()
    except Exception as e:
        print(f"[VideoPipeline] Failed to record run: {e}")

    # ========== 飞书数据追踪 ==========
    try:
        await tracker.flush()
    except Exception as e:
        logger.warning("video.tracker.flush_failed", error=str(e))

    return stats
