"""
[INPUT]: 依赖 scrapers/* 的各类采集器, processors/* 的过滤/分析/翻译器, models/resource 的 Resource
[OUTPUT]: 对外提供 run_article_pipeline, run_full_pipeline, run_twitter_pipeline, run_podcast_pipeline, run_video_pipeline
[POS]: 核心流水线模块，包含 5 种内容类型的处理流程
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

流水线概览:
- ArticlePipeline: RSS采集 → 全文提取 → 初评过滤 → 深度分析 → 翻译 → 存储
- FullPipeline: 多源采集 (HN/GitHub/arXiv/HF/PH) → 过滤 → 摘要生成 → 存储
- TwitterPipeline: XGoing采集 → 去重 → 直接存储 (跳过LLM)
- PodcastPipeline: RSS采集 → 去重 → 可选转写 → 存储
- VideoPipeline: RSS采集 → 去重 → 可选转写 → 存储

TODO: 未来版本考虑使用 base_pipeline.py 的 BasePipeline 基类重构，提取公共逻辑
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.signal import Signal
from app.models.resource import Resource
from app.processors.filter import SignalFilter
from app.processors.generator import SummaryGenerator
from app.processors.initial_filter import InitialFilter, InitialFilterResult
from app.processors.analyzer import Analyzer, AnalysisResult
from app.processors.translator import Translator
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.github import GitHubScraper
from app.scrapers.huggingface import HuggingFaceScraper
from app.scrapers.twitter import TwitterScraper
from app.scrapers.xgoing import XGoingScraper
from app.scrapers.arxiv import ArXivScraper
from app.scrapers.producthunt import ProductHuntScraper
from app.scrapers.blog import BlogScraper
from app.scrapers.rss import RSSScraper
from app.scrapers.podcast import PodcastScraper
from app.scrapers.video import VideoScraper
from app.scrapers.content_extractor import ContentExtractor, ExtractedContent
from app.scrapers.base import RawSignal
from app.scrapers.favicon import FaviconFetcher
from app.utils.llm import llm_client
from app.services.source_service import SourceService


class PipelineStats:
    """流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0
        self.filtered_count = 0
        self.generated_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class ArticlePipelineStats:
    """文章流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0  # RSS 采集数
        self.extracted_count = 0  # 全文提取成功数
        self.extraction_failed_count = 0  # 全文提取失败数
        self.filter_passed_count = 0  # 初评通过数
        self.filter_rejected_count = 0  # 初评拒绝数
        self.analyzed_count = 0  # 深度分析完成数
        self.translated_count = 0  # 翻译完成数
        self.saved_count = 0  # 保存成功数
        self.failed_count = 0  # 处理失败数
        self.total_input_tokens = 0
        self.total_output_tokens = 0


async def run_article_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 3,
    use_full_analysis: bool = True,
) -> ArticlePipelineStats:
    """
    运行文章处理流水线

    流程：
    1. RSS 采集 - 使用 RSSScraper 获取 RSS 源的文章列表
    2. 全文提取 - 使用 ContentExtractor 提取文章全文 (Playwright)
    3. 初评过滤 - 使用 InitialFilter 进行规则+LLM初评，过滤低价值内容
    4. 深度分析 - 使用 Analyzer 进行三步深度分析
    5. 翻译 - 英文内容使用 Translator 翻译分析结果
    6. 存储 - 保存到 Resource 表

    Args:
        opml_path: OPML 文件路径（可选，默认使用 BestBlogs OPML）
        min_value_score: 初评最低通过分数（0-5），默认 3 分
        use_full_analysis: 是否使用完整三步分析，False 则使用快速单步分析

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

                # 构建 Resource 记录
                resource = Resource(
                    # 类型与来源
                    type="article",
                    source_name=source_name,
                    source_url="",  # RSS 源 URL（可从 OPML 获取）
                    source_icon_url=source_icon_url,
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

    # ========== 9. 记录采集结果 ==========
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
        record_db.close()
    except Exception as e:
        print(f"[ArticlePipeline] Failed to record run: {e}")

    return stats


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

    # 1.1 Hacker News
    if should_run('hn') and config.hackernews.enabled:
        hn_scraper = HackerNewsScraper()
        hn_signals = await hn_scraper.scrape()
        raw_signals.extend(hn_signals)
        print(f"[HN] Scraped {len(hn_signals)} signals")

    # 1.2 GitHub Trending
    if should_run('github') and config.github.enabled:
        github_scraper = GitHubScraper()
        github_signals = await github_scraper.scrape()
        raw_signals.extend(github_signals)
        print(f"[GitHub] Scraped {len(github_signals)} signals")

    # 1.3 Hugging Face
    if should_run('huggingface') and config.huggingface.enabled:
        hf_scraper = HuggingFaceScraper()
        hf_signals = await hf_scraper.scrape()
        raw_signals.extend(hf_signals)
        print(f"[HuggingFace] Scraped {len(hf_signals)} signals")

    # 1.4 Twitter
    if should_run('twitter') and config.twitter.enabled:
        twitter_scraper = TwitterScraper()
        twitter_signals = await twitter_scraper.scrape()
        raw_signals.extend(twitter_signals)
        print(f"[Twitter] Scraped {len(twitter_signals)} signals")

    # 1.5 ArXiv
    if should_run('arxiv') and config.arxiv.enabled:
        arxiv_scraper = ArXivScraper()
        arxiv_signals = await arxiv_scraper.scrape()
        raw_signals.extend(arxiv_signals)
        print(f"[ArXiv] Scraped {len(arxiv_signals)} signals")

    # 1.6 Product Hunt
    if should_run('producthunt') and config.producthunt.enabled:
        ph_scraper = ProductHuntScraper()
        ph_signals = await ph_scraper.scrape()
        raw_signals.extend(ph_signals)
        print(f"[ProductHunt] Scraped {len(ph_signals)} signals")

    # 1.7 Blog/Podcast RSS - 使用 RSSScraper 支持 OPML
    if should_run('blog') and hasattr(config, 'blog') and config.blog.enabled:
        # 使用支持 OPML 的 RSSScraper
        opml_path = config.blog.opml_path if hasattr(config.blog, 'opml_path') else None
        rss_scraper = RSSScraper(opml_path=opml_path)
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
            # final_score = heat_score * 0.6 + quality_score * 0.4
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
                source_name=signal.source.upper(),  # hn, github, huggingface
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
                language="zh",  # 默认中文
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

    # 重置 Token 计数器（下次运行重新计算）
    llm_client.reset_token_counter()

    # ========== 记录采集结果（多源聚合记录到 hackernews） ==========
    try:
        record_db = SessionLocal()
        source_service = SourceService(record_db)
        # FullPipeline 主要是 HN/GitHub/arXiv 等，记录为 hackernews
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


class TwitterPipelineStats:
    """Twitter 流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0  # XGoing 采集数
        self.filter_passed_count = 0  # 初评通过数
        self.filter_rejected_count = 0  # 初评拒绝数
        self.analyzed_count = 0  # 分析完成数
        self.translated_count = 0  # 翻译完成数
        self.saved_count = 0  # 保存成功数
        self.failed_count = 0  # 处理失败数
        self.total_input_tokens = 0
        self.total_output_tokens = 0


async def run_twitter_pipeline(
    opml_path: Optional[str] = None,
    min_value_score: int = 2,
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

    Returns:
        TwitterPipelineStats 统计信息
    """
    stats = TwitterPipelineStats()
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

        # 过滤掉已存在的
        new_signals = [s for s in raw_signals if s.url not in existing_urls]
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[TwitterPipeline] Found {duplicate_count} duplicates, {len(new_signals)} new tweets\n")

        if not new_signals:
            print("[TwitterPipeline] All tweets already exist, exiting.\n")
            return stats

        raw_signals = new_signals

    finally:
        db.close()

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

    return stats


class PodcastPipelineStats:
    """播客流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0  # RSS 采集数
        self.transcribed_count = 0  # 转写成功数
        self.saved_count = 0  # 保存成功数
        self.failed_count = 0  # 处理失败数


async def run_podcast_pipeline(
    opml_path: Optional[str] = None,
    max_items_per_feed: int = 2,
    enable_transcription: bool = True,
    max_daily_transcription: int = 5,
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

    Returns:
        PodcastPipelineStats 统计信息
    """
    stats = PodcastPipelineStats()
    print(f"\n{'='*60}")
    print(f"[PodcastPipeline] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[PodcastPipeline] Transcription: {'Enabled' if enable_transcription else 'Disabled'}")
    print(f"{'='*60}\n")

    # ========== 1. RSS 采集 ==========
    print("[PodcastPipeline] Step 1: Scraping podcasts from RSS feeds...")

    # 使用配置中的 OPML 路径
    if opml_path is None and hasattr(config, 'podcast') and hasattr(config.podcast, 'opml_path'):
        opml_path = config.podcast.opml_path

    podcast_scraper = PodcastScraper()
    raw_signals = await podcast_scraper.scrape(
        opml_path=opml_path,
        max_items_per_feed=max_items_per_feed
    )
    stats.scraped_count = len(raw_signals)

    print(f"[PodcastPipeline] Scraped {stats.scraped_count} podcast episodes\n")

    if not raw_signals:
        print("[PodcastPipeline] No podcasts scraped, exiting.\n")
        return stats

    # ========== 2. URL 去重检查 ==========
    print("[PodcastPipeline] Step 2: Checking for duplicates...")

    db: Session = SessionLocal()
    try:
        # 获取已存在的 URL hash
        existing_urls = set()
        for signal in raw_signals:
            url_hash = Resource.generate_url_hash(signal.url)
            existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
            if existing:
                existing_urls.add(signal.url)

        # 过滤掉已存在的
        new_signals = [s for s in raw_signals if s.url not in existing_urls]
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[PodcastPipeline] Found {duplicate_count} duplicates, {len(new_signals)} new podcasts\n")

        if not new_signals:
            print("[PodcastPipeline] All podcasts already exist, exiting.\n")
            return stats

        raw_signals = new_signals

    finally:
        db.close()

    # ========== 3. 音频转写（可选） ==========
    transcription_enabled = enable_transcription
    transcriber = None

    if transcription_enabled:
        try:
            from app.processors.transcriber import Transcriber
            transcriber = Transcriber()

            if not transcriber.access_key_id or not transcriber.access_key_secret:
                print("[PodcastPipeline] Transcriber 未配置，跳过转写")
                transcription_enabled = False
            else:
                print("[PodcastPipeline] Transcriber 已初始化")

        except ImportError:
            print("[PodcastPipeline] Transcriber 模块未找到，跳过转写")
            transcription_enabled = False

    # 限制转写数量
    items_to_transcribe = raw_signals[:max_daily_transcription] if transcription_enabled else []

    # ========== 4. 存储到数据库 ==========
    print(f"[PodcastPipeline] Step 3: Saving podcasts...")
    if transcription_enabled:
        print(f"[PodcastPipeline] Will transcribe {len(items_to_transcribe)}/{len(raw_signals)} episodes\n")

    db: Session = SessionLocal()
    try:
        for i, signal in enumerate(raw_signals):
            try:
                print(f"  [{i+1}/{len(raw_signals)}] Processing: {signal.title[:50]}...")

                # 获取播客元数据
                metadata = signal.metadata or {}
                audio_url = metadata.get("audio_url", "")

                # 转写音频
                transcribed_text = None
                transcribed_duration = 0

                if transcription_enabled and signal in items_to_transcribe and audio_url:
                    print(f"    -> Transcribing: {audio_url[:60]}...")
                    try:
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
                            print(f"    -> Transcription completed ({len(transcribed_text)} chars)")
                        else:
                            print(f"    -> Transcription failed")
                    except Exception as e:
                        print(f"    -> Transcription error: {e}")

                # 创建 Resource 对象
                resource = Resource(
                    type="podcast",
                    url_hash=Resource.generate_url_hash(signal.url),
                    source_name=metadata.get("podcast_name", "podcast"),
                    source_icon_url=FaviconFetcher.get_favicon(signal.url),
                    url=signal.url,
                    title=signal.title,
                    one_sentence_summary=signal.title,
                    content_markdown=transcribed_text,  # 转写文本
                    content_html=signal.content,  # 原始描述
                    domain="科技播客",
                    tags=["播客", "科技"],
                    score=3,
                    is_featured=False,
                    language="zh",
                    published_at=signal.source_created_at,
                    created_at=datetime.now(),
                    status="published",
                    metadata={
                        "audio_url": audio_url,
                        "duration": transcribed_duration or metadata.get("duration", 0),
                        "transcribed": transcribed_text is not None,
                    },
                )

                db.add(resource)
                db.commit()
                stats.saved_count += 1
                print(f"    -> Saved")

            except Exception as e:
                db.rollback()
                stats.failed_count += 1
                print(f"    -> Error: {e}")

        print(f"\n[PodcastPipeline] Saved {stats.saved_count}/{len(raw_signals)} podcasts\n")

    finally:
        db.close()

    # ========== 统计 ==========
    print(f"{'='*60}")
    print("[PodcastPipeline] Summary:")
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
            source_type="podcast",
            status="success" if stats.failed_count == 0 else "partial",
            fetched_count=stats.scraped_count,
            dedup_filtered_count=len(raw_signals),
            saved_count=stats.saved_count,
            error_message=None if stats.failed_count == 0 else f"Failed: {stats.failed_count}",
        )
        record_db.close()
    except Exception as e:
        print(f"[PodcastPipeline] Failed to record run: {e}")

    return stats


class VideoPipelineStats:
    """视频流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0  # RSS 采集数
        self.transcribed_count = 0  # 转写成功数
        self.saved_count = 0  # 保存成功数
        self.failed_count = 0  # 处理失败数


async def run_video_pipeline(
    opml_path: Optional[str] = None,
    max_items_per_feed: int = 1,
    enable_transcription: bool = True,
    max_daily_transcription: int = 2,
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

    Returns:
        VideoPipelineStats 统计信息
    """
    stats = VideoPipelineStats()
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

        # 过滤掉已存在的
        new_signals = [s for s in raw_signals if s.url not in existing_urls]
        duplicate_count = len(raw_signals) - len(new_signals)

        print(f"[VideoPipeline] Found {duplicate_count} duplicates, {len(new_signals)} new videos\n")

        if not new_signals:
            print("[VideoPipeline] All videos already exist, exiting.\n")
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

                # 创建 Resource 对象
                resource = Resource(
                    type="video",
                    url_hash=Resource.generate_url_hash(signal.url),
                    source_name=metadata.get("channel_name", "youtube"),
                    source_icon_url=FaviconFetcher.get_favicon(signal.url),
                    url=signal.url,
                    title=signal.title,
                    one_sentence_summary=signal.title,
                    content_markdown=transcribed_text,  # 转写文本
                    content_html=signal.content,  # 原始描述
                    domain="科技视频",
                    tags=["视频", "AI", "科技"],
                    score=3,
                    is_featured=False,
                    language=metadata.get("language", "en"),
                    published_at=signal.source_created_at,
                    created_at=datetime.now(),
                    status="published",
                    metadata={
                        "video_id": metadata.get("video_id"),
                        "thumbnail_url": metadata.get("thumbnail_url"),
                        "duration": transcribed_duration or metadata.get("duration", 0),
                        "transcribed": transcribed_text is not None,
                    },
                )

                db.add(resource)
                db.commit()
                stats.saved_count += 1
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

    return stats
