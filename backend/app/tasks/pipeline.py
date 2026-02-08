"""
[INPUT]: 依赖 scrapers/twitter+blog+rss, processors/filter+generator, models/resource, services/source_service
[OUTPUT]: 对外提供 run_full_pipeline (多源聚合流水线)
[POS]: 遗留流水线文件，仅保留 FullPipeline；其余流水线已迁移到 pipeline/ 子目录
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

说明:
此文件仅保留 run_full_pipeline 函数，供 pipeline/full_pipeline.py 通过 importlib 加载。
其余流水线函数（article/twitter/podcast/video）已迁移到 pipeline/ 子目录中各自的模块。

⚠️ 此文件被 pipeline/ 目录遮蔽（Python 包优先级），
只能通过 full_pipeline.py 的 importlib.util.spec_from_file_location 显式加载。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.processors.filter import SignalFilter
from app.processors.generator import SummaryGenerator
from app.scrapers.twitter import TwitterScraper
from app.scrapers.rss import RSSScraper
from app.scrapers.favicon import FaviconFetcher
from app.utils.llm import llm_client
from app.services.source_service import SourceService

from app.tasks.pipeline.stats import PipelineStats


async def run_full_pipeline(sources: list[str] | None = None) -> PipelineStats:
    """
    运行完整的信号处理流水线（向后兼容）

    Args:
        sources: 可选的数据源列表，如 ['twitter', 'hn']。
                 如果为 None，则运行所有启用的数据源。

    流程：
    1. 数据采集（HN Scraper）
    2. 去重 + LLM 过滤
    3. LLM 摘要生成
    4. 存储到数据库

    Returns:
        PipelineStats 统计信息
    """
    # DEBUG: 打印 sources 参数
    print(f"[DEBUG] run_full_pipeline called with sources={sources}, type={type(sources)}")
    stats = PipelineStats()
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if sources:
        print(f"[Pipeline] Sources: {', '.join(sources)}")
    print(f"{'='*60}\n")

    # ========== 1. 数据采集 ==========
    print("[Pipeline] Step 1: Scraping signals from sources...")

    raw_signals = []

    # 辅助函数：检查数据源是否应该运行
    def should_run(source_name: str) -> bool:
        if sources is None:
            return True  # 运行所有源
        return source_name in sources

    # 1.4 Twitter
    if should_run('twitter') and config.twitter.enabled:
        twitter_scraper = TwitterScraper()
        twitter_signals = await twitter_scraper.scrape()
        raw_signals.extend(twitter_signals)
        print(f"[Twitter] Scraped {len(twitter_signals)} signals")

    # 1.7 Blog/Podcast RSS - 使用 RSSScraper 支持 OPML
    if should_run('blog') and hasattr(config, 'blog') and config.blog.enabled:
        # 使用支持 OPML 的 RSSScraper
        opml_path = config.blog.opml_path if hasattr(config.blog, 'opml_path') else None
        max_items = config.blog.max_items_per_feed if hasattr(config.blog, 'max_items_per_feed') else 3
        rss_scraper = RSSScraper(opml_path=opml_path, max_items_per_feed=max_items)
        rss_signals = await rss_scraper.scrape()
        raw_signals.extend(rss_signals)
        print(f"[Blog] Scraped {len(rss_signals)} signals")

    stats.scraped_count = len(raw_signals)
    print(f"\n[Pipeline] Total scraped: {stats.scraped_count} signals from all sources\n")

    if not raw_signals:
        print("[Pipeline] No signals scraped, exiting.\n")
        return stats

    # ========== 2. 过滤 ==========
    print("[Pipeline] Step 2: Filtering signals...")

    signal_filter = SignalFilter(dedup_enabled=config.filter.dedup_enabled)
    filter_results = await signal_filter.filter_batch(raw_signals)

    # 统计通过过滤的信号
    passed_signals = []
    passed_filter_results = []

    for i, (signal, filter_result) in enumerate(zip(raw_signals, filter_results)):
        if filter_result.passed:
            passed_signals.append(signal)
            passed_filter_results.append(filter_result)
            print(
                f"  [PASS] [{i+1}] {signal.title[:60]}... "
                f"(matched: {', '.join(filter_result.matched_conditions)})"
            )
        else:
            print(f"  [REJECT] [{i+1}] {signal.title[:60]}... (reason: {filter_result.reason})")

    stats.filtered_count = len(passed_signals)
    print(
        f"\n[Pipeline] {stats.filtered_count}/{stats.scraped_count} signals passed filter "
        f"({stats.filtered_count/stats.scraped_count*100:.1f}%)\n"
    )

    if not passed_signals:
        print("[Pipeline] No signals passed filter, exiting.\n")
        return stats

    # ========== 3. 摘要生成 ==========
    print("[Pipeline] Step 3: Generating summaries...")

    generator = SummaryGenerator()
    matched_conditions_list = [fr.matched_conditions for fr in passed_filter_results]
    summary_results = await generator.generate_batch(
        passed_signals, matched_conditions_list
    )

    stats.generated_count = len(summary_results)
    print(f"[Pipeline] Generated {stats.generated_count} summaries\n")

    # ========== 4. 存储到数据库 ==========
    print("[Pipeline] Step 4: Saving to database...")

    db: Session = SessionLocal()
    try:
        for signal, filter_result, summary_result in zip(
            passed_signals, passed_filter_results, summary_results
        ):
            # 计算 final_score（转换为 0-100）
            final_score = int(
                (summary_result.heat_score * 0.6 + summary_result.quality_score * 0.4) * 10
            )

            # 检查是否已存在（URL 去重）
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                print(f"  -> Duplicate URL, skipping: {signal.url}")
                continue

            # 获取来源图标
            source_icon_url = FaviconFetcher.get_favicon(signal.url)

            # 映射分类名称
            category_mapping = {
                "开源工具": "软件编程",
                "AI模型": "人工智能",
                "AI应用": "人工智能",
                "技术产品": "产品设计",
                "行业动态": "商业科技",
            }
            domain = category_mapping.get(summary_result.category, summary_result.category)

            # 创建 Resource 记录
            resource = Resource(
                # 类型与来源
                type="article",
                source_name=signal.source.upper(),
                source_url="",
                source_icon_url=source_icon_url,
                url=signal.url,
                url_hash=url_hash,

                # 原始内容
                title=signal.title,
                author=signal.metadata.get("author", "") if signal.metadata else "",
                content_html=signal.content,

                # 分析结果
                one_sentence_summary=summary_result.one_liner,
                summary=summary_result.summary,

                # 分类与标签
                domain=domain,
                tags=summary_result.tags,

                # 评分（转换为 0-100）
                score=final_score,
                is_featured=Resource.should_be_featured(final_score),

                # 状态
                language="zh",
                status="published",

                # 时间戳
                published_at=signal.source_created_at,
                analyzed_at=datetime.now(),

                # 元数据
                extra_metadata={
                    "original_category": summary_result.category,
                    "matched_conditions": filter_result.matched_conditions,
                    "heat_score": summary_result.heat_score,
                    "quality_score": summary_result.quality_score,
                },
            )

            db.add(resource)
            stats.saved_count += 1
            print(
                f"  -> Saved: {signal.title[:60]}... "
                f"(score: {final_score}, domain: {domain})"
            )

        db.commit()
        print(f"\n[Pipeline] Successfully saved {stats.saved_count} resources to database\n")

    except Exception as e:
        db.rollback()
        print(f"\n[Pipeline] Database error: {e}\n")
        stats.failed_count = stats.generated_count - stats.saved_count

    finally:
        db.close()

    # ========== 5. Token 统计 ==========
    token_usage = llm_client.get_token_usage()
    stats.total_input_tokens = token_usage["input"]
    stats.total_output_tokens = token_usage["output"]

    print(f"{'='*60}")
    print("[Pipeline] Summary:")
    print(f"  - Scraped: {stats.scraped_count}")
    print(f"  - Filtered: {stats.filtered_count} ({stats.filtered_count/stats.scraped_count*100:.1f}%)" if stats.scraped_count > 0 else "  - Filtered: 0")
    print(f"  - Generated: {stats.generated_count}")
    print(f"  - Saved: {stats.saved_count}")
    print(f"  - Failed: {stats.failed_count}")
    print(f"  - Input tokens: {stats.total_input_tokens:,}")
    print(f"  - Output tokens: {stats.total_output_tokens:,}")
    print(f"  - Total tokens: {stats.total_input_tokens + stats.total_output_tokens:,}")
    print(f"{'='*60}\n")

    # 重置 Token 计数器
    llm_client.reset_token_counter()

    # ========== 记录采集结果 ==========
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        source_service.record_run(
            source_type="hackernews",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            llm_filtered_count=stats.filtered_count,
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
        record_db.close()
    except Exception as e:
        print(f"[Pipeline] Failed to record run: {e}")

    return stats
