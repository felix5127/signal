# Input: RSSScraper, ContentExtractor, BatchFilterProcessor, BatchAnalyzerProcessor, BatchTranslatorProcessor, BatchDBOperator
# Output: 数据库中的 Resource 记录（并发优化版）
# Position: 优化版流水线，使用异步任务队列和并发处理提升性能
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.models.task import TaskStatus
from app.processors.initial_filter import InitialFilterResult
from app.processors.analyzer import AnalysisResult
from app.processors.batch_processor import (
    BatchFilterProcessor,
    BatchAnalyzerProcessor,
    BatchTranslatorProcessor,
)
from app.scrapers.base import RawSignal
from app.scrapers.rss import RSSScraper
from app.scrapers.content_extractor import ContentExtractor, ExtractedContent
from app.tasks.queue import AsyncTaskQueue, TaskProgress, batch_extractor
from app.utils.batch_db import batch_db
from app.utils.llm import llm_client
import logging

logger = logging.getLogger(__name__)


class OptimizedPipelineStats:
    """优化版流水线统计"""

    def __init__(self):
        self.scraped_count = 0
        self.duplicate_count = 0
        self.extracted_count = 0
        self.extraction_failed_count = 0
        self.filter_passed_count = 0
        self.filter_rejected_count = 0
        self.analyzed_count = 0
        self.analyze_failed_count = 0
        self.translated_count = 0
        self.translate_failed_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_duration_seconds = 0


async def run_optimized_article_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 3,
    use_full_analysis: bool = True,
    max_concurrent_extraction: int = 10,
    max_concurrent_analysis: int = 3,
    max_concurrent_translation: int = 5,
    max_items_to_process: Optional[int] = None,
    skip_first_n: int = 0,
) -> OptimizedPipelineStats:
    """
    运行优化版文章处理流水线

    优化点：
    1. 全文提取并发（10 个并发）
    2. 初评过滤并发（5 个 LLM 并发）
    3. 深度分析并发（3 个并发，分析耗时长）
    4. 翻译并发（5 个并发）
    5. 数据库批量插入（50 个一批）

    流程：
    1. RSS 采集
    2. URL 去重（批量查询）
    3. 全文提取（并发）
    4. 初评过滤（并发）
    5. 深度分析（并发）
    6. 翻译（并发，仅英文）
    7. 批量存储

    Args:
        opml_path: OPML 文件路径
        min_value_score: 初评最低通过分数
        use_full_analysis: 是否使用完整三步分析
        max_concurrent_extraction: 全文提取最大并发数
        max_concurrent_analysis: 深度分析最大并发数
        max_concurrent_translation: 翻译最大并发数
        max_items_to_process: 最大处理文章数（用于测试）
        skip_first_n: 跳过前 N 篇文章（用于跳过低质量内容）

    Returns:
        OptimizedPipelineStats 统计信息
    """
    import time
    start_time = time.time()
    stats = OptimizedPipelineStats()

    print(f"\n{'='*60}")
    print(f"[OptimizedPipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # ========== 1. RSS 采集 ==========
    print("[OptimizedPipeline] Step 1: Scraping RSS feeds...")

    rss_scraper = RSSScraper(opml_path=opml_path)
    raw_signals = await rss_scraper.scrape()
    stats.scraped_count = len(raw_signals)

    print(f"[OptimizedPipeline] Scraped {stats.scraped_count} articles\n")

    if not raw_signals:
        print("[OptimizedPipeline] No articles scraped, exiting.\n")
        return stats

    # ========== 2. URL 去重（批量查询） ==========
    print("[OptimizedPipeline] Step 2: Checking for duplicates (batch query)...")

    db: Session = SessionLocal()
    try:
        # 批量查询已存在的 URL hash
        url_hashes = [Resource.generate_url_hash(s.url) for s in raw_signals]
        existing = db.query(Resource.url_hash).filter(
            Resource.url_hash.in_(url_hashes)
        ).all()
        existing_hashes = set(e[0] for e in existing)

        # 过滤掉已存在的
        new_signals = [s for s in raw_signals if s.url not in existing_hashes]
        stats.duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[OptimizedPipeline] Found {stats.duplicate_count} duplicates, {len(new_signals)} new articles\n")

        if not new_signals:
            print("[OptimizedPipeline] All articles already exist, exiting.\n")
            return stats

        raw_signals = new_signals

        # 跳过前 N 篇（用于跳过低质量内容）
        if skip_first_n > 0 and len(raw_signals) > skip_first_n:
            print(f"[OptimizedPipeline] Skipping first {skip_first_n} articles\n")
            raw_signals = raw_signals[skip_first_n:]

        # 限制处理数量（用于测试）
        if max_items_to_process and len(raw_signals) > max_items_to_process:
            print(f"[OptimizedPipeline] Limiting to {max_items_to_process} articles (test mode)\n")
            raw_signals = raw_signals[:max_items_to_process]

    finally:
        db.close()

    # ========== 3. 全文提取（并发） ==========
    print("[OptimizedPipeline] Step 3: Extracting full content (concurrent)...")

    content_extractor = ContentExtractor()
    extractor = batch_extractor
    extractor.max_concurrent = max_concurrent_extraction

    # 创建任务
    queue = AsyncTaskQueue(max_concurrent=max_concurrent_extraction)
    task_id = await queue.create_task(
        task_type="content_extraction",
        total_items=len(raw_signals),
        metadata={"source": "article_pipeline"},
    )

    db = SessionLocal()
    try:
        progress = TaskProgress(task_id, len(raw_signals), db)
        await queue.start_task(task_id)

        # 批量提取
        extraction_results = await extractor.extract_batch(
            urls=[s.url for s in raw_signals],
            content_extractor=content_extractor,
            task_id=task_id,
            progress=progress,
        )

        # 统计结果
        extracted_items: List[Tuple[RawSignal, ExtractedContent]] = []
        for (success, content), signal in zip(extraction_results, raw_signals):
            if success and content and content.markdown:
                extracted_items.append((signal, content))
                stats.extracted_count += 1
            else:
                stats.extraction_failed_count += 1

        await queue.complete_task(task_id, result={
            "extracted": stats.extracted_count,
            "failed": stats.extraction_failed_count,
        })

        print(f"[OptimizedPipeline] Extracted {stats.extracted_count}/{len(raw_signals)} articles\n")

    finally:
        db.close()

    if not extracted_items:
        print("[OptimizedPipeline] No content extracted, exiting.\n")
        return stats

    # ========== 4. 初评过滤（并发） ==========
    print("[OptimizedPipeline] Step 4: Initial filtering (concurrent LLM)...")

    batch_filter = BatchFilterProcessor(max_concurrent=5)

    # 构建过滤项
    filter_items = []
    for signal, content in extracted_items:
        source_name = signal.metadata.get("source_name", "") if signal.metadata else ""
        filter_items.append({
            "title": signal.title,
            "content": content.markdown,
            "url": signal.url,
            "source": source_name,
        })

    # 批量过滤
    filter_results = await batch_filter.filter_batch(filter_items)

    # 统计结果
    filtered_items: List[Tuple[RawSignal, ExtractedContent, InitialFilterResult]] = []
    for (success, filter_result), (signal, content) in zip(filter_results, extracted_items):
        if success and filter_result and not filter_result.ignore and filter_result.value >= min_value_score:
            filtered_items.append((signal, content, filter_result))
            stats.filter_passed_count += 1
        else:
            stats.filter_rejected_count += 1
            reason = filter_result.reason if filter_result else "Filter error"
            value = filter_result.value if filter_result else 0
            logger.info(f"  [REJECT] {signal.title[:50]}... (reason={reason}, value={value})")

    print(f"[OptimizedPipeline] {stats.filter_passed_count}/{len(extracted_items)} passed filter\n")

    if not filtered_items:
        print("[OptimizedPipeline] No articles passed filter, exiting.\n")
        return stats

    # ========== 5. 深度分析（并发） ==========
    print("[OptimizedPipeline] Step 5: Deep analysis (concurrent LLM)...")

    batch_analyzer = BatchAnalyzerProcessor(max_concurrent=max_concurrent_analysis)

    # 构建分析项
    analyze_items = []
    for signal, content, filter_result in filtered_items:
        source_name = signal.metadata.get("source_name", "") if signal.metadata else ""
        analyze_items.append({
            "content": content.markdown,
            "title": signal.title,
            "source": source_name,
            "url": signal.url,
            "language": filter_result.language,
        })

    # 批量分析
    analysis_results = await batch_analyzer.analyze_batch(
        items=analyze_items,
        use_full_analysis=use_full_analysis,
    )

    # 统计结果
    analyzed_items: List[Tuple[RawSignal, ExtractedContent, InitialFilterResult, AnalysisResult]] = []
    for (success, analysis), (signal, content, filter_result) in zip(analysis_results, filtered_items):
        if success and analysis:
            analyzed_items.append((signal, content, filter_result, analysis))
            stats.analyzed_count += 1
        else:
            stats.analyze_failed_count += 1

    print(f"[OptimizedPipeline] Analyzed {stats.analyzed_count}/{len(filtered_items)} articles\n")

    if not analyzed_items:
        print("[OptimizedPipeline] No articles analyzed, exiting.\n")
        return stats

    # ========== 6. 翻译（并发，仅英文） ==========
    print("[OptimizedPipeline] Step 6: Translating English content (concurrent)...")

    batch_translator = BatchTranslatorProcessor(max_concurrent=max_concurrent_translation)

    # 筛选需要翻译的（英文内容）
    translate_items = []
    translate_indices = []
    for i, (signal, content, filter_result, analysis) in enumerate(analyzed_items):
        if filter_result.language == "en":
            translate_items.append({
                "title": signal.title,
                "analysis_dict": analysis.to_dict(),
            })
            translate_indices.append(i)

    # 批量翻译
    translated_results = await batch_translator.translate_batch(translate_items)

    # 构建翻译映射
    translation_map = {}
    for idx, (success, translated) in enumerate(translated_results):
        original_idx = translate_indices[idx]
        if success and translated:
            translation_map[original_idx] = translated
        else:
            stats.translate_failed_count += 1
            translation_map[original_idx] = None

    stats.translated_count = len(translate_items) - stats.translate_failed_count

    # 合并所有结果
    final_items = []
    for i, (signal, content, filter_result, analysis) in enumerate(analyzed_items):
        translated = translation_map.get(i)
        final_items.append((signal, content, filter_result, analysis, translated))

    print(f"[OptimizedPipeline] Translated {stats.translated_count} English articles\n")

    # ========== 7. 批量存储 ==========
    print("[OptimizedPipeline] Step 7: Bulk saving to database...")

    # 构建 Resource 对象列表
    resources = []
    for signal, content, filter_result, analysis, translated in final_items:
        source_name = signal.metadata.get("source_name", "") if signal.metadata else ""
        author = signal.metadata.get("author", "") if signal.metadata else ""

        resource = Resource(
            # 类型与来源
            type="article",
            source_name=source_name,
            source_url="",
            url=signal.url,
            url_hash=Resource.generate_url_hash(signal.url),

            # 原始内容
            title=signal.title,
            title_translated=translated.get("title_translated") if translated else (signal.title if filter_result.language == "zh" else None),
            author=author,
            content_markdown=content.markdown,
            content_html=content.html,
            word_count=content.word_count,
            read_time=content.read_time,

            # 分析结果
            one_sentence_summary=analysis.one_sentence_summary,
            one_sentence_summary_zh=translated.get("oneSentenceSummary") if translated else (analysis.one_sentence_summary if filter_result.language == "zh" else None),
            summary=analysis.summary,
            summary_zh=translated.get("summary") if translated else (analysis.summary if filter_result.language == "zh" else None),
            main_points=[{"point": p.point, "explanation": p.explanation} for p in analysis.main_points],
            main_points_zh=translated.get("mainPoints") if translated else ([{"point": p.point, "explanation": p.explanation} for p in analysis.main_points] if filter_result.language == "zh" else None),
            key_quotes=analysis.key_quotes,
            key_quotes_zh=translated.get("keyQuotes") if translated else (analysis.key_quotes if filter_result.language == "zh" else None),

            # 分类与标签
            domain=analysis.domain,
            subdomain=analysis.subdomain,
            tags=analysis.tags,

            # 评分
            score=analysis.score,
            is_featured=Resource.should_be_featured(analysis.score),

            # 状态
            language=filter_result.language,
            status="published",

            # 时间戳
            published_at=signal.source_created_at,
            analyzed_at=datetime.now(),

            # 元数据
            metadata={
                "initial_filter": {
                    "value": filter_result.value,
                    "summary": filter_result.summary,
                    "reason": filter_result.reason,
                },
                "rss_metadata": signal.metadata,
                "pipeline": "optimized_v2",
            },
        )
        resources.append(resource)

    # 批量插入
    db: Session = SessionLocal()
    try:
        save_stats = await batch_db.bulk_insert_resources(db, resources)
        stats.saved_count = save_stats["inserted"]
        stats.failed_count = save_stats["failed"]
        print(f"[OptimizedPipeline] Saved {stats.saved_count} resources\n")

    except Exception as e:
        logger.error(f"[OptimizedPipeline] Database error: {e}")
        stats.failed_count = len(resources)

    finally:
        db.close()

    # ========== 8. 统计总结 ==========
    stats.total_duration_seconds = time.time() - start_time

    token_usage = llm_client.get_token_usage()
    stats.total_input_tokens = token_usage["input"]
    stats.total_output_tokens = token_usage["output"]

    print(f"{'='*60}")
    print("[OptimizedPipeline] Summary:")
    print(f"  - RSS Scraped: {stats.scraped_count}")
    print(f"  - Duplicates: {stats.duplicate_count}")
    print(f"  - Content Extracted: {stats.extracted_count} (failed: {stats.extraction_failed_count})")
    print(f"  - Filter Passed: {stats.filter_passed_count} (rejected: {stats.filter_rejected_count})")
    print(f"  - Analyzed: {stats.analyzed_count} (failed: {stats.analyze_failed_count})")
    print(f"  - Translated: {stats.translated_count} (failed: {stats.translate_failed_count})")
    print(f"  - Saved: {stats.saved_count}")
    print(f"  - Failed: {stats.failed_count}")
    print(f"  - Input tokens: {stats.total_input_tokens:,}")
    print(f"  - Output tokens: {stats.total_output_tokens:,}")
    print(f"  - Total tokens: {stats.total_input_tokens + stats.total_output_tokens:,}")
    print(f"  - Duration: {stats.total_duration_seconds:.1f}s ({stats.total_duration_seconds/60:.1f}m)")
    print(f"  - Throughput: {stats.scraped_count/max(stats.total_duration_seconds, 1):.2f} articles/sec")
    print(f"{'='*60}\n")

    # 重置 Token 计数器
    llm_client.reset_token_counter()

    return stats
