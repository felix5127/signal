# Input: RSS OPML 文件, RawSignal 数据
# Output: 数据库中的 Resource 记录
# Position: 文章流水线模块，处理 RSS 采集 → 全文提取 → 分析 → 翻译 → 存储
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
文章处理流水线

完整的文章处理流程：
1. RSS 采集 - 使用 RSSScraper 获取 RSS 源的文章列表
2. URL 去重 - 检查数据库中是否已存在
3. 全文提取 - 使用 ContentExtractor 提取文章全文 (Playwright)
4. 初评过滤 - 使用 InitialFilter 进行规则+LLM初评，过滤低价值内容
5. 深度分析 - 使用 Analyzer 进行三步深度分析
6. 翻译 - 英文内容使用 Translator 翻译分析结果
7. 存储 - 保存到 Resource 表
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.processors.initial_filter import InitialFilter, InitialFilterResult
from app.processors.analyzer import Analyzer, AnalysisResult
from app.processors.translator import Translator
from app.scrapers.rss import RSSScraper
from app.scrapers.content_extractor import ContentExtractor, ExtractedContent
from app.scrapers.base import RawSignal
from app.scrapers.favicon import FaviconFetcher
from app.utils.llm import llm_client

from app.tasks.pipeline.stats import ArticlePipelineStats


async def run_article_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 3,
    use_full_analysis: bool = True,
    resource_type: str = "article",
) -> ArticlePipelineStats:
    """
    运行文章处理流水线

    Args:
        opml_path: OPML 文件路径（可选，默认使用 BestBlogs OPML）
        min_value_score: 初评最低通过分数（0-5），默认 3 分
        use_full_analysis: 是否使用完整三步分析，False 则使用快速单步分析
        resource_type: 资源类型（article/podcast/video），默认 article

    Returns:
        ArticlePipelineStats 统计信息
    """
    stats = ArticlePipelineStats()
    print(f"\n{'='*60}")
    print(f"[ArticlePipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # ========== 1. RSS 采集 ==========
    print("[ArticlePipeline] Step 1: Scraping RSS feeds...")

    rss_scraper = RSSScraper(opml_path=opml_path)
    raw_signals = await rss_scraper.scrape()
    stats.scraped_count = len(raw_signals)

    print(f"[ArticlePipeline] Scraped {stats.scraped_count} articles from RSS feeds\n")

    if not raw_signals:
        print("[ArticlePipeline] No articles scraped, exiting.\n")
        return stats

    # ========== 2. URL 去重检查 ==========
    print("[ArticlePipeline] Step 2: Checking for duplicates...")

    db: Session = SessionLocal()
    try:
        # 获取已存在的 URL hash
        existing_hashes = set()
        for signal in raw_signals:
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                existing_hashes.add(signal.url)

        # 过滤掉已存在的
        new_signals = [s for s in raw_signals if s.url not in existing_hashes]
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[ArticlePipeline] Found {duplicate_count} duplicates, {len(new_signals)} new articles\n")

        if not new_signals:
            print("[ArticlePipeline] All articles already exist, exiting.\n")
            return stats

        raw_signals = new_signals

    finally:
        db.close()

    # ========== 3. 全文提取 ==========
    print("[ArticlePipeline] Step 3: Extracting full content...")

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
            print(f"    -> Failed: {e}")

    print(f"\n[ArticlePipeline] Extracted {stats.extracted_count}/{len(raw_signals)} articles\n")

    if not extracted_contents:
        print("[ArticlePipeline] No content extracted, exiting.\n")
        return stats

    # ========== 4. 初评过滤 ==========
    print("[ArticlePipeline] Step 4: Initial filtering (Rule + LLM)...")

    initial_filter = InitialFilter()
    filtered_items: List[tuple[RawSignal, ExtractedContent, InitialFilterResult]] = []

    for i, (signal, content) in enumerate(extracted_contents):
        try:
            print(f"  [{i+1}/{len(extracted_contents)}] Filtering: {signal.title[:50]}...")

            # 获取来源名称
            source_name = signal.metadata.get("source_name", "") if signal.metadata else ""

            # 进行初评
            filter_result = await initial_filter.filter(
                title=signal.title,
                content=content.markdown,
                url=signal.url,
                source=source_name,
            )

            if filter_result.ignore or filter_result.value < min_value_score:
                stats.filter_rejected_count += 1
                print(f"    -> Rejected: {filter_result.reason} (value={filter_result.value})")
            else:
                filtered_items.append((signal, content, filter_result))
                stats.filter_passed_count += 1
                print(f"    -> Passed: value={filter_result.value}, lang={filter_result.language}")

        except Exception as e:
            stats.failed_count += 1
            print(f"    -> Error: {e}")

    print(
        f"\n[ArticlePipeline] {stats.filter_passed_count}/{len(extracted_contents)} passed filter "
        f"(min_value={min_value_score})\n"
    )

    if not filtered_items:
        print("[ArticlePipeline] No articles passed filter, exiting.\n")
        return stats

    # ========== 5. 深度分析 ==========
    print("[ArticlePipeline] Step 5: Deep analysis (3-step LLM)...")

    analyzer = Analyzer()
    analyzed_items: List[tuple[RawSignal, ExtractedContent, InitialFilterResult, AnalysisResult]] = []

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
            print(f"    -> Error: {e}")

    print(f"\n[ArticlePipeline] Analyzed {stats.analyzed_count}/{len(filtered_items)} articles\n")

    if not analyzed_items:
        print("[ArticlePipeline] No articles analyzed, exiting.\n")
        return stats

    # ========== 6. 翻译（英文内容） ==========
    print("[ArticlePipeline] Step 6: Translating English content...")

    translator = Translator()
    final_items: List[tuple[RawSignal, ExtractedContent, InitialFilterResult, AnalysisResult, Optional[dict]]] = []

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
                print(f"    -> Translation error (using original): {e}")
                translated_analysis = None
        else:
            print(f"  [{i+1}/{len(analyzed_items)}] Skipping (Chinese): {signal.title[:50]}...")

        final_items.append((signal, content, filter_result, analysis, translated_analysis))

    print(f"\n[ArticlePipeline] Translated {stats.translated_count} English articles\n")

    # ========== 7. 存储到数据库 ==========
    print("[ArticlePipeline] Step 7: Saving to database...")

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

                # 获取来源信息
                source_name = signal.metadata.get("source_name", "") if signal.metadata else ""
                author = signal.metadata.get("author", "") if signal.metadata else ""

                # 获取来源图标
                source_icon_url = FaviconFetcher.get_favicon(signal.url)

                # 获取缩略图 (从 RSS metadata)
                thumbnail_url = signal.metadata.get("thumbnail_url") if signal.metadata else None

                # 构建 Resource 记录
                resource = Resource(
                    # 类型与来源
                    type=resource_type,
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
                    },
                )

                db.add(resource)
                stats.saved_count += 1
                print(
                    f"  -> Saved: {signal.title[:50]}... "
                    f"(score={analysis.score}, domain={analysis.domain})"
                )

            except Exception as e:
                stats.failed_count += 1
                print(f"  -> Save error: {e}")

        db.commit()
        print(f"\n[ArticlePipeline] Successfully saved {stats.saved_count} resources\n")

    except Exception as e:
        db.rollback()
        print(f"\n[ArticlePipeline] Database error: {e}\n")
        stats.failed_count += len(final_items) - stats.saved_count

    finally:
        db.close()

    # ========== 8. Token 统计 ==========
    token_usage = llm_client.get_token_usage()
    stats.total_input_tokens = token_usage["input"]
    stats.total_output_tokens = token_usage["output"]

    print(f"{'='*60}")
    print("[ArticlePipeline] Summary:")
    print(f"  - RSS Scraped: {stats.scraped_count}")
    print(f"  - Content Extracted: {stats.extracted_count} (failed: {stats.extraction_failed_count})")
    print(f"  - Filter Passed: {stats.filter_passed_count} (rejected: {stats.filter_rejected_count})")
    print(f"  - Analyzed: {stats.analyzed_count}")
    print(f"  - Translated: {stats.translated_count}")
    print(f"  - Saved: {stats.saved_count}")
    print(f"  - Failed: {stats.failed_count}")
    print(f"  - Input tokens: {stats.total_input_tokens:,}")
    print(f"  - Output tokens: {stats.total_output_tokens:,}")
    print(f"  - Total tokens: {stats.total_input_tokens + stats.total_output_tokens:,}")
    print(f"{'='*60}\n")

    # 重置 Token 计数器
    llm_client.reset_token_counter()

    return stats
