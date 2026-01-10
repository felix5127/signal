# 视频采集 API 示例
# 展示如何使用 VideoScraper 和 Transcriber

import asyncio
from typing import List

from app.scrapers.video import VideoScraper
from app.processors.transcriber import Transcriber
from app.models.resource import Resource
from app.database import SessionLocal


async def scrape_and_save_videos(max_items: int = 10):
    """
    采集视频并保存到数据库

    Args:
        max_items: 每个频道最多抓取条数
    """
    print("=" * 60)
    print("开始采集视频...")
    print("=" * 60)

    # 1. 采集视频
    scraper = VideoScraper()
    raw_signals = await scraper.scrape(max_items_per_feed=max_items)

    if not raw_signals:
        print("未采集到任何视频")
        return

    print(f"\n共采集到 {len(raw_signals)} 条视频")

    # 2. 保存到数据库
    db = SessionLocal()
    saved_count = 0

    try:
        for signal in raw_signals:
            # 检查是否已存在
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(
                Resource.url_hash == url_hash
            ).first()

            if existing:
                print(f"跳过已存在: {signal.title[:50]}...")
                continue

            # 创建新记录
            resource = Resource(
                type="video",
                source_name=signal.metadata.get("channel_name", "Unknown"),
                source_url="",  # 可从 OPML 获取
                url=signal.url,
                url_hash=url_hash,
                title=signal.title,
                content=signal.content,
                published_at=signal.source_created_at,
                duration=signal.metadata.get("duration", 0),
                extra_metadata={
                    **signal.metadata,
                    "video_id": signal.metadata.get("video_id"),
                    "thumbnail_url": signal.metadata.get("thumbnail_url"),
                }
            )

            db.add(resource)
            saved_count += 1
            print(f"✓ 保存: {signal.title[:50]}...")

        db.commit()
        print(f"\n成功保存 {saved_count} 条新视频")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
    finally:
        db.close()


async def scrape_with_transcription(max_items: int = 3):
    """
    采集视频并进行转写

    注意: 需要配置 TINGWU_API_KEY 和 TINGWU_APP_KEY

    Args:
        max_items: 每个频道最多抓取条数
    """
    print("=" * 60)
    print("开始采集视频并进行转写...")
    print("=" * 60)

    # 检查 API Key
    import os
    if not os.getenv("TINGWU_API_KEY") or not os.getenv("TINGWU_APP_KEY"):
        print("错误: 未配置通义听悟 API Key")
        print("请在 .env 文件中设置:")
        print("  TINGWU_API_KEY=your_api_key")
        print("  TINGWU_APP_KEY=your_app_key")
        return

    # 1. 采集视频
    scraper = VideoScraper()
    raw_signals = await scraper.scrape(max_items_per_feed=max_items)

    if not raw_signals:
        print("未采集到任何视频")
        return

    print(f"\n共采集到 {len(raw_signals)} 条视频")

    # 2. 转写视频
    transcriber = Transcriber()
    db = SessionLocal()

    try:
        for i, signal in enumerate(raw_signals, 1):
            print(f"\n[{i}/{len(raw_signals)}] 处理: {signal.title[:50]}...")

            # 检查是否已存在
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(
                Resource.url_hash == url_hash
            ).first()

            if existing:
                print("  跳过已存在")
                continue

            # 转写视频
            print("  正在转写...")
            result = await transcriber.transcribe(
                signal.url,
                media_type="video"
            )

            # 保存到数据库
            resource = Resource(
                type="video",
                source_name=signal.metadata.get("channel_name", "Unknown"),
                url=signal.url,
                url_hash=url_hash,
                title=signal.title,
                content=signal.content,
                transcript=result.text if result else None,
                duration=result.duration if result else signal.metadata.get("duration", 0),
                extra_metadata=signal.metadata
            )

            db.add(resource)
            db.commit()

            if result:
                print(f"  ✓ 转写完成: {result.text[:100]}...")
            else:
                print("  ✗ 转写失败")

        print(f"\n处理完成!")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
    finally:
        db.close()


async def get_recent_videos(limit: int = 10):
    """
    获取最近采集的视频

    Args:
        limit: 返回条数
    """
    db = SessionLocal()

    try:
        videos = db.query(Resource).filter(
            Resource.type == "video"
        ).order_by(
            Resource.published_at.desc()
        ).limit(limit).all()

        print(f"\n最近 {len(videos)} 条视频:")
        print("=" * 60)

        for video in videos:
            print(f"\n标题: {video.title}")
            print(f"频道: {video.source_name}")
            print(f"时长: {video.duration} 秒")
            print(f"发布: {video.published_at}")

            metadata = video.extra_metadata or {}
            if metadata.get("video_id"):
                print(f"视频ID: {metadata['video_id']}")
            if metadata.get("thumbnail_url"):
                print(f"缩略图: {metadata['thumbnail_url']}")

            if video.transcript:
                print(f"转写: {video.transcript[:100]}...")

            print("-" * 60)

    finally:
        db.close()


# 使用示例
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "scrape":
            # 仅采集
            asyncio.run(scrape_and_save_videos(max_items=5))

        elif command == "transcribe":
            # 采集 + 转写
            asyncio.run(scrape_with_transcription(max_items=3))

        elif command == "list":
            # 列出最近视频
            asyncio.run(get_recent_videos(limit=10))

        else:
            print("使用方法:")
            print("  python video_example.py scrape      - 仅采集视频")
            print("  python video_example.py transcribe  - 采集并转写")
            print("  python video_example.py list        - 列出最近视频")
    else:
        print("使用方法:")
        print("  python video_example.py scrape      - 仅采集视频")
        print("  python video_example.py transcribe  - 采集并转写")
        print("  python video_example.py list        - 列出最近视频")
