# Input: RSS OPML 文件, RawSignal 数据
# Output: 数据库中的 Resource 记录
# Position: 文章流水线模块，处理 RSS 采集 → 去重(Deduper) → 全文提取 → 统一过滤(UnifiedFilter) → 深度分析 → 翻译 → 存储 → 飞书追踪(DataTracker)
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
文章处理流水线

完整的文章处理流程：
1. RSS 采集 - 使用 RSSScraper 获取 RSS 源的文章列表
2. URL 去重 - 使用 Deduper 进行三层去重（URL + 标题相似度 + 内容指纹）
3. 全文提取 - 使用 ContentExtractor 提取文章全文 (Playwright)
4. 统一过滤 - 使用 UnifiedFilter 进行规则+LLM过滤，>=3 分通过
5. 深度分析 - 使用 Analyzer 进行三步深度分析
6. 翻译 - 英文内容使用 Translator 翻译分析结果
7. 存储 - 保存到 Resource 表
8. Token 统计 - 记录 LLM 用量
9. 采集记录 - SourceService.record_run()
10. 飞书追踪 - DataTracker.flush() 写入飞书多维表格
"""

from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.processors.unified_filter import UnifiedFilter, FilterResult
from app.processors.deduper import Deduper
from app.services.prompt_service import prompt_service
from app.processors.analyzer import Analyzer, AnalysisResult
from app.processors.translator import Translator
from app.scrapers.rss import RSSScraper
from app.scrapers.content_extractor import ContentExtractor, ExtractedContent
from app.scrapers.base import RawSignal
from app.scrapers.favicon import FaviconFetcher
from app.utils.llm import llm_client
from app.services.source_service import SourceService
from app.services.data_tracker import DataTracker

from app.tasks.pipeline.stats import ArticlePipelineStats

logger = structlog.get_logger("pipeline")


async def run_article_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 3,
    use_full_analysis: bool = True,
    dry_run: bool = False,
) -> ArticlePipelineStats:
    """
    运行文章处理流水线

    流程：
    1. RSS 采集 - 使用 RSSScraper 获取 RSS 源的文章列表
    2. URL 去重 - 使用 Deduper 进行三层去重（URL + 标题相似度 + 内容指纹）
    3. 全文提取 - 使用 ContentExtractor 提取文章全文 (Playwright)
    4. 统一过滤 - 使用 UnifiedFilter 进行规则+LLM过滤，>=3 分通过
    5. 深度分析 - 使用 Analyzer 进行三步深度分析
    6. 翻译 - 英文内容使用 Translator 翻译分析结果
    7. 存储 - 保存到 Resource 表

    Args:
        opml_path: OPML 文件路径（可选，默认使用 BestBlogs OPML）
        min_value_score: [DEPRECATED] 已弃用，UnifiedFilter 使用 PASS_THRESHOLD=3
        use_full_analysis: 是否使用完整三步分析，False 则使用快速单步分析
        dry_run: 试运行模式，执行采集+去重+提取+过滤但不写入数据库

    Returns:
        ArticlePipelineStats 统计信息
    """
    stats = ArticlePipelineStats()
    tracker = DataTracker(pipeline="article")  # 数据追踪器
    logger.info("article.pipeline.started")

    # ========== 1. RSS 采集 ==========
    logger.info("article.scrape.started")

    # 从配置获取每个 feed 的最大条目数
    max_items = config.blog.max_items_per_feed if hasattr(config, 'blog') else 3
    rss_scraper = RSSScraper(opml_path=opml_path, max_items_per_feed=max_items)
    raw_signals = await rss_scraper.scrape()
    stats.scraped_count = len(raw_signals)

    logger.info("article.scrape.completed", count=stats.scraped_count)

    if not raw_signals:
        logger.info("article.scrape.empty")
        await tracker.flush()
        return stats

    # ========== 2. URL 去重检查 ==========
    logger.info("article.dedupe.started", items_in=len(raw_signals))

    deduper = Deduper()

    # 批量去重
    items_for_dedup = [{"url": s.url, "title": s.title, "signal": s} for s in raw_signals]
    deduped_items = deduper.dedupe_batch(items_for_dedup)

    # 构建去重后的 URL 集合
    deduped_urls = {item["url"] for item in deduped_items}

    # 追踪被过滤的重复项
    for signal in raw_signals:
        if signal.url not in deduped_urls:
            source_name = signal.metadata.get("source_name", "RSS") if signal.metadata else "RSS"
            tracker.track_filtered(
                title=signal.title,
                url=signal.url,
                source=source_name,
                reason="重复内容",
                stage="dedup",
            )

    new_signals = [item["signal"] for item in deduped_items]
    duplicate_count = len(raw_signals) - len(new_signals)

    logger.info("article.dedupe.completed", duplicates=duplicate_count, new_count=len(new_signals))

    if not new_signals:
        logger.info("article.dedupe.all_duplicates")
        await tracker.flush()
        return stats

    raw_signals = new_signals

    # ========== 3. 全文提取 ==========
    logger.info("article.extract.started", items_in=len(raw_signals))

    content_extractor = ContentExtractor()
    extracted_contents: List[tuple[RawSignal, Optional[ExtractedContent]]] = []

    for i, signal in enumerate(raw_signals):
        try:
            print(f"  [{i+1}/{len(raw_signals)}] Extracting: {signal.title[:50]}...")
            content = await content_extractor.extract(signal.url)

            if content and content.markdown:
                extracted_contents.append((signal, content))
                stats.extracted_count += 1
                print(f"    -> Success ({content.word_count} words, {content.read_time} min read)")
            else:
                stats.extraction_failed_count += 1
                print(f"    -> Failed: No content extracted")

        except Exception as e:
            stats.extraction_failed_count += 1
            logger.warning("article.extract.item_failed", url=signal.url[:80], error=str(e))

    logger.info("article.extract.completed",
                items_out=stats.extracted_count, failed=stats.extraction_failed_count)

    if not extracted_contents:
        logger.info("article.extract.empty")
        await tracker.flush()
        return stats

    # ========== 4. 统一过滤 ==========
    logger.info("article.filter.started", items_in=len(extracted_contents))

    from app.services.ai_service import AIService
    ai_service = AIService()
    unified_filter = UnifiedFilter(prompt_service=prompt_service, ai_service=ai_service)
    filtered_items: List[tuple[RawSignal, ExtractedContent, FilterResult]] = []

    for i, (signal, content) in enumerate(extracted_contents):
        try:
            print(f"  [{i+1}/{len(extracted_contents)}] Filtering: {signal.title[:50]}...")

            # 获取来源名称
            source_name = signal.metadata.get("source_name", "") if signal.metadata else ""

            # 检查是否白名单源（暂时都不是白名单，后续从 Source 表获取）
            source_is_whitelist = False

            filter_result = await unified_filter.filter(
                title=signal.title,
                content=content.markdown,
                url=signal.url,
                source_name=source_name,
                source_is_whitelist=source_is_whitelist,
            )

            if not filter_result.passed:
                stats.filter_rejected_count += 1
                print(f"    -> Rejected: {filter_result.reason} (score={filter_result.score})")
                # 追踪被过滤的内容
                tracker.track_filtered(
                    title=signal.title,
                    url=signal.url,
                    source=source_name or "RSS",
                    reason=filter_result.reason,
                    stage="llm",
                    score=filter_result.score,
                )
            else:
                filtered_items.append((signal, content, filter_result))
                stats.filter_passed_count += 1
                print(f"    -> Passed: score={filter_result.score}, lang={filter_result.language}")

        except Exception as e:
            stats.failed_count += 1
            logger.error("article.filter.item_error", url=signal.url[:80], error=str(e))

    logger.info("article.filter.completed",
                passed=stats.filter_passed_count, rejected=stats.filter_rejected_count,
                threshold=unified_filter.PASS_THRESHOLD)

    if not filtered_items:
        logger.info("article.filter.all_rejected")
        await tracker.flush()
        return stats

    # ========== dry_run 提前返回 ==========
    if dry_run:
        logger.info("article.pipeline.dry_run_complete",
                     scraped=stats.scraped_count,
                     extracted=stats.extracted_count,
                     filter_passed=stats.filter_passed_count,
                     filter_rejected=stats.filter_rejected_count,
                     would_analyze=len(filtered_items))
        await tracker.flush()
        return stats

    # ========== 5. 深度分析 ==========
    logger.info("article.analyze.started", items_in=len(filtered_items))

    analyzer = Analyzer()
    analyzed_items: List[tuple[RawSignal, ExtractedContent, FilterResult, AnalysisResult]] = []

    for i, (signal, content, filter_result) in enumerate(filtered_items):
        try:
            print(f"  [{i+1}/{len(filtered_items)}] Analyzing: {signal.title[:50]}...")

            # 获取来源名称
            source_name = signal.metadata.get("source_name", "") if signal.metadata else ""

            # 执行三步分析或快速分析
            if use_full_analysis:
                analysis = await analyzer.full_analyze(
                    content=content.markdown,
                    title=signal.title,
                    source=source_name,
                    url=signal.url,
                    language=filter_result.language,
                )
            else:
                analysis = await analyzer.quick_analyze(
                    content=content.markdown,
                    title=signal.title,
                    source=source_name,
                    url=signal.url,
                    language=filter_result.language,
                )

            analyzed_items.append((signal, content, filter_result, analysis))
            stats.analyzed_count += 1
            print(f"    -> Score: {analysis.score}, Domain: {analysis.domain}")

        except Exception as e:
            stats.failed_count += 1
            logger.error("article.analyze.item_error", url=signal.url[:80], error=str(e))

    logger.info("article.analyze.completed", items_out=stats.analyzed_count, items_in=len(filtered_items))

    if not analyzed_items:
        logger.info("article.analyze.empty")
        await tracker.flush()
        return stats

    # ========== 6. 翻译（英文内容） ==========
    logger.info("article.translate.started", items_in=len(analyzed_items))

    translator = Translator()
    final_items: List[tuple[RawSignal, ExtractedContent, FilterResult, AnalysisResult, Optional[dict]]] = []

    for i, (signal, content, filter_result, analysis) in enumerate(analyzed_items):
        translated_analysis = None

        if filter_result.language == "en":
            try:
                print(f"  [{i+1}/{len(analyzed_items)}] Translating: {signal.title[:50]}...")

                # 翻译分析结果
                analysis_dict = analysis.to_dict()
                translated_analysis = await translator.translate_analysis(analysis_dict)

                # 翻译标题
                translated_title = await translator.translate_title(signal.title)
                translated_analysis["title_translated"] = translated_title

                stats.translated_count += 1
                print(f"    -> Translation completed")

            except Exception as e:
                logger.warning("article.translate.item_error", url=signal.url[:80], error=str(e))
                translated_analysis = None
        else:
            print(f"  [{i+1}/{len(analyzed_items)}] Skipping (Chinese): {signal.title[:50]}...")

        final_items.append((signal, content, filter_result, analysis, translated_analysis))

    logger.info("article.translate.completed", translated=stats.translated_count)

    # ========== 7. 存储到数据库 ==========
    logger.info("article.save.started", items_in=len(final_items))

    db: Session = SessionLocal()
    try:
        for signal, content, filter_result, analysis, translated in final_items:
            try:
                # 检查是否已存在（二次检查，防止并发）
                url_hash = Resource.generate_url_hash(signal.url)
                existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
                if existing:
                    print(f"  -> Duplicate (skip): {signal.url}")
                    continue

                # 获取来源信息（截断防止 varchar 溢出）
                source_name = (signal.metadata.get("source_name", "") if signal.metadata else "")[:255]
                author = (signal.metadata.get("author", "") if signal.metadata else "")[:255]

                # 获取来源图标
                source_icon_url = FaviconFetcher.get_favicon(signal.url)

                # 获取缩略图 (RSS metadata 优先, OG Image 兜底)
                thumbnail_url = signal.metadata.get("thumbnail_url") if signal.metadata else None
                if not thumbnail_url and content.og_image_url:
                    thumbnail_url = content.og_image_url

                # 构建 Resource 记录
                resource = Resource(
                    # 类型与来源
                    type="article",
                    source_name=source_name,
                    source_url="",  # RSS 源 URL（可从 OPML 获取）
                    source_icon_url=source_icon_url,
                    thumbnail_url=thumbnail_url,
                    url=signal.url,
                    url_hash=url_hash,

                    # 原始内容
                    title=signal.title,
                    title_translated=translated.get("title_translated") if translated else (signal.title if filter_result.language == "zh" else None),
                    author=author,
                    content_markdown=content.markdown,
                    content_html=content.html,
                    word_count=content.word_count,
                    read_time=content.read_time,

                    # 分析结果（截断防止 varchar 溢出）
                    one_sentence_summary=(analysis.one_sentence_summary or "")[:500],
                    one_sentence_summary_zh=(translated.get("oneSentenceSummary") if translated else (analysis.one_sentence_summary if filter_result.language == "zh" else None) or "")[:500],
                    summary=analysis.summary,
                    summary_zh=translated.get("summary") if translated else (analysis.summary if filter_result.language == "zh" else None),
                    main_points=[{"point": p.point, "explanation": p.explanation} for p in analysis.main_points],
                    main_points_zh=translated.get("mainPoints") if translated else ([{"point": p.point, "explanation": p.explanation} for p in analysis.main_points] if filter_result.language == "zh" else None),
                    key_quotes=analysis.key_quotes,
                    key_quotes_zh=translated.get("keyQuotes") if translated else (analysis.key_quotes if filter_result.language == "zh" else None),

                    # 分类与标签（截断防止 varchar 溢出）
                    domain=(analysis.domain or "")[:100],
                    subdomain=(analysis.subdomain or "")[:100],
                    tags=analysis.tags,

                    # 评分
                    score=analysis.score,
                    is_featured=Resource.should_be_featured(analysis.score),

                    # LLM 过滤结果
                    llm_score=filter_result.score,
                    llm_reason=filter_result.reason,
                    llm_prompt_version=filter_result.prompt_version,

                    # 状态
                    language=filter_result.language,
                    status="published",

                    # 时间戳
                    published_at=signal.source_created_at,
                    analyzed_at=datetime.now(),

                    # 元数据
                    extra_metadata={
                        "unified_filter": {
                            "score": filter_result.score,
                            "reason": filter_result.reason,
                            "is_whitelist": filter_result.is_whitelist,
                            "prompt_version": filter_result.prompt_version,
                        },
                        "rss_metadata": signal.metadata,
                    },
                )

                db.add(resource)
                stats.saved_count += 1
                print(
                    f"  -> Saved: {signal.title[:50]}... "
                    f"(score={analysis.score}, domain={analysis.domain})"
                )

                # 追踪收录的内容
                tracker.track_collected(
                    title=signal.title,
                    url=signal.url,
                    source=source_name or "RSS",
                    reason=f"LLM 评分 {filter_result.score} 分，深度分析评分 {analysis.score}",
                    stage="save",
                    score=analysis.score,
                )

            except Exception as e:
                stats.failed_count += 1
                logger.error("article.save.item_error", url=signal.url[:80], error=str(e))

        db.commit()
        logger.info("article.save.completed", saved=stats.saved_count)

    except Exception as e:
        db.rollback()
        logger.error("article.save.db_error", error=str(e))
        stats.failed_count += len(final_items) - stats.saved_count

    finally:
        db.close()

    # ========== 8. Token 统计 ==========
    token_usage = llm_client.get_token_usage()
    stats.total_input_tokens = token_usage["input"]
    stats.total_output_tokens = token_usage["output"]

    logger.info("article.pipeline.summary",
                scraped=stats.scraped_count,
                extracted=stats.extracted_count,
                extraction_failed=stats.extraction_failed_count,
                filter_passed=stats.filter_passed_count,
                filter_rejected=stats.filter_rejected_count,
                analyzed=stats.analyzed_count,
                translated=stats.translated_count,
                saved=stats.saved_count,
                failed=stats.failed_count,
                input_tokens=stats.total_input_tokens,
                output_tokens=stats.total_output_tokens)

    # 重置 Token 计数器
    llm_client.reset_token_counter()

    # ========== 9. 记录采集结果 ==========
    record_db = None
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        source_service.record_run(
            source_type="blog",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            rule_filtered_count=stats.extracted_count,
            dedup_filtered_count=stats.filter_passed_count,
            llm_filtered_count=stats.analyzed_count,
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
    except Exception as e:
        logger.error("article.record_run.failed", error=str(e))
    finally:
        if record_db:
            record_db.close()

    # ========== 10. 写入追踪数据到飞书 ==========
    logger.info("article.tracking.flushing")
    # 保存统计数据（flush 后 records 会被清空）
    tracking_collected = tracker.collected_count
    tracking_filtered = tracker.filtered_count
    try:
        success_count = await tracker.flush()
        logger.info("article.tracking.flushed",
                    collected=tracking_collected, filtered=tracking_filtered, written=success_count)
    except Exception as e:
        logger.warning("article.tracking.flush_failed", error=str(e))

    return stats
