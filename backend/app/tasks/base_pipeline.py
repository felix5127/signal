"""
[INPUT]: 依赖 database 的 SessionLocal, models/resource 的 Resource, scrapers/favicon 的 FaviconFetcher
[OUTPUT]: 对外提供 PipelineStats, BasePipeline
[POS]: 流水线公共基类，提供去重检查、保存逻辑、进度打印等通用功能
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set, Optional, Any, TypeVar, Generic
from contextlib import contextmanager

from app.database import SessionLocal
from app.models.resource import Resource
from app.services.source_service import SourceService

T = TypeVar('T')  # 输入类型
R = TypeVar('R')  # 结果类型


@dataclass
class PipelineStats:
    """
    统一流水线统计类

    所有流水线共用的统计数据结构，支持不同类型的计数。
    """
    # 采集阶段
    scraped_count: int = 0
    duplicate_count: int = 0

    # 提取阶段
    extracted_count: int = 0
    extraction_failed_count: int = 0

    # 过滤阶段
    filter_passed_count: int = 0
    filter_rejected_count: int = 0

    # 分析阶段
    analyzed_count: int = 0

    # 翻译阶段
    translated_count: int = 0

    # 转写阶段（播客/视频）
    transcribed_count: int = 0

    # 存储阶段
    saved_count: int = 0
    failed_count: int = 0

    # Token 统计
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def print_summary(self, pipeline_name: str):
        """打印统计摘要"""
        print(f"{'='*60}")
        print(f"[{pipeline_name}] Summary:")
        print(f"  - Scraped: {self.scraped_count}")
        if self.duplicate_count:
            print(f"  - Duplicates: {self.duplicate_count}")
        if self.extracted_count or self.extraction_failed_count:
            print(f"  - Extracted: {self.extracted_count} (failed: {self.extraction_failed_count})")
        if self.filter_passed_count or self.filter_rejected_count:
            print(f"  - Filter Passed: {self.filter_passed_count} (rejected: {self.filter_rejected_count})")
        if self.analyzed_count:
            print(f"  - Analyzed: {self.analyzed_count}")
        if self.translated_count:
            print(f"  - Translated: {self.translated_count}")
        if self.transcribed_count:
            print(f"  - Transcribed: {self.transcribed_count}")
        print(f"  - Saved: {self.saved_count}")
        print(f"  - Failed: {self.failed_count}")
        if self.total_input_tokens or self.total_output_tokens:
            print(f"  - Input tokens: {self.total_input_tokens:,}")
            print(f"  - Output tokens: {self.total_output_tokens:,}")
            print(f"  - Total tokens: {self.total_input_tokens + self.total_output_tokens:,}")
        print(f"{'='*60}\n")


class BasePipeline:
    """
    流水线基类

    提供所有流水线共用的功能：
    - URL 去重检查
    - 批量保存到数据库
    - 进度打印
    - 统计更新
    """

    def __init__(self, pipeline_name: str):
        """
        初始化流水线

        Args:
            pipeline_name: 流水线名称，用于日志打印
        """
        self.pipeline_name = pipeline_name
        self.stats = PipelineStats()

    def print_header(self):
        """打印流水线开始头部"""
        print(f"\n{'='*60}")
        print(f"[{self.pipeline_name}] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

    def print_step(self, step_num: int, description: str):
        """打印步骤开始"""
        print(f"[{self.pipeline_name}] Step {step_num}: {description}")

    def print_progress(self, current: int, total: int, item_name: str, status: str = ""):
        """打印进度"""
        status_str = f" -> {status}" if status else ""
        print(f"  [{current}/{total}] {item_name[:50]}...{status_str}")

    def check_duplicates(self, urls: List[str]) -> Set[str]:
        """
        检查 URL 去重

        Args:
            urls: URL 列表

        Returns:
            Set[str]: 已存在的 URL 集合
        """
        db = SessionLocal()
        try:
            existing_urls = set()
            for url in urls:
                url_hash = Resource.generate_url_hash(url)
                existing = db.query(Resource).filter(Resource.url_hash == url_hash).first()
                if existing:
                    existing_urls.add(url)
            return existing_urls
        finally:
            db.close()

    def filter_new_items(self, items: List, url_getter) -> List:
        """
        过滤掉已存在的项目

        Args:
            items: 项目列表
            url_getter: 获取 URL 的函数，如 lambda x: x.url

        Returns:
            List: 过滤后的新项目列表
        """
        urls = [url_getter(item) for item in items]
        existing_urls = self.check_duplicates(urls)

        new_items = [item for item in items if url_getter(item) not in existing_urls]
        self.stats.duplicate_count = len(items) - len(new_items)

        print(f"[{self.pipeline_name}] Found {self.stats.duplicate_count} duplicates, {len(new_items)} new items\n")

        return new_items

    def print_summary(self):
        """打印统计摘要"""
        self.stats.print_summary(self.pipeline_name)

    @contextmanager
    def db_session(self):
        """
        数据库会话上下文管理器

        Usage:
            with self.db_session() as db:
                db.add(resource)
                db.commit()
        """
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def record_run(
        self,
        source_type: str,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """
        记录流水线运行结果

        Args:
            source_type: 数据源类型 (blog/twitter/podcast/video/hackernews)
            status: 运行状态 (success/partial/failed)
            error_message: 错误信息
        """
        try:
            with self.db_session() as db:
                source_service = SourceService(db)
                source_service.record_run(
                    source_type=source_type,
                    status=status,
                    fetched_count=self.stats.scraped_count,
                    rule_filtered_count=self.stats.extracted_count,
                    dedup_filtered_count=self.stats.filter_passed_count,
                    llm_filtered_count=self.stats.analyzed_count,
                    saved_count=self.stats.saved_count,
                    error_message=error_message,
                )
        except Exception as e:
            print(f"[{self.pipeline_name}] Failed to record run: {e}")

    def update_token_usage(self, llm_client):
        """
        更新 Token 使用统计

        Args:
            llm_client: LLM 客户端实例（需要有 get_token_usage 方法）
        """
        if hasattr(llm_client, 'get_token_usage'):
            usage = llm_client.get_token_usage()
            self.stats.total_input_tokens = usage.get("input", 0)
            self.stats.total_output_tokens = usage.get("output", 0)

    def reset_token_counter(self, llm_client):
        """
        重置 Token 计数器

        Args:
            llm_client: LLM 客户端实例
        """
        if hasattr(llm_client, 'reset_token_counter'):
            llm_client.reset_token_counter()

    async def run(self) -> PipelineStats:
        """
        运行流水线

        子类应该实现此方法来定义具体的流水线逻辑。
        """
        raise NotImplementedError("Subclasses must implement run()")


# ============================================================
# 带步骤的流水线基类
# ============================================================

class StepBasedPipeline(BasePipeline, ABC):
    """
    基于步骤的流水线基类

    提供更结构化的流水线实现，子类只需实现各个步骤的具体逻辑。

    使用示例:
    ```python
    class MyPipeline(StepBasedPipeline):
        def __init__(self):
            super().__init__("MyPipeline", source_type="blog")

        async def scrape(self) -> List[RawSignal]:
            # 实现采集逻辑
            return signals

        async def filter(self, items: List) -> List:
            # 实现过滤逻辑
            return filtered_items

        async def process(self, items: List) -> List:
            # 实现处理逻辑
            return processed_items

        async def save(self, items: List) -> int:
            # 实现保存逻辑
            return saved_count
    ```
    """

    def __init__(self, pipeline_name: str, source_type: str):
        """
        初始化步骤化流水线

        Args:
            pipeline_name: 流水线名称
            source_type: 数据源类型，用于记录运行结果
        """
        super().__init__(pipeline_name)
        self.source_type = source_type

    @abstractmethod
    async def scrape(self) -> List[Any]:
        """
        采集步骤

        Returns:
            采集到的原始数据列表
        """
        pass

    async def dedupe(self, items: List[Any]) -> List[Any]:
        """
        去重步骤

        默认使用 filter_new_items 方法，子类可重写。

        Args:
            items: 原始数据列表

        Returns:
            去重后的数据列表
        """
        return self.filter_new_items(items, lambda x: x.url)

    async def filter(self, items: List[Any]) -> List[Any]:
        """
        过滤步骤

        默认不过滤，子类可重写。

        Args:
            items: 待过滤数据列表

        Returns:
            过滤后的数据列表
        """
        return items

    async def process(self, items: List[Any]) -> List[Any]:
        """
        处理步骤 (分析、转写等)

        默认不处理，子类可重写。

        Args:
            items: 待处理数据列表

        Returns:
            处理后的数据列表
        """
        return items

    @abstractmethod
    async def save(self, items: List[Any]) -> int:
        """
        保存步骤

        Args:
            items: 待保存数据列表

        Returns:
            保存成功的数量
        """
        pass

    async def run(self) -> PipelineStats:
        """
        运行流水线

        按顺序执行: scrape -> dedupe -> filter -> process -> save
        """
        self.print_header()

        # 1. 采集
        self.print_step(1, "Scraping...")
        items = await self.scrape()
        self.stats.scraped_count = len(items)
        print(f"[{self.pipeline_name}] Scraped {self.stats.scraped_count} items\n")

        if not items:
            print(f"[{self.pipeline_name}] No items scraped, exiting.\n")
            return self.stats

        # 2. 去重
        self.print_step(2, "Checking duplicates...")
        items = await self.dedupe(items)

        if not items:
            print(f"[{self.pipeline_name}] All items are duplicates, exiting.\n")
            return self.stats

        # 3. 过滤
        self.print_step(3, "Filtering...")
        items = await self.filter(items)
        self.stats.filter_passed_count = len(items)

        if not items:
            print(f"[{self.pipeline_name}] No items passed filter, exiting.\n")
            return self.stats

        # 4. 处理
        self.print_step(4, "Processing...")
        items = await self.process(items)

        if not items:
            print(f"[{self.pipeline_name}] No items processed, exiting.\n")
            return self.stats

        # 5. 保存
        self.print_step(5, "Saving...")
        self.stats.saved_count = await self.save(items)

        # 打印摘要
        self.print_summary()

        # 记录运行结果
        status = "success" if self.stats.failed_count == 0 else "partial"
        error_msg = f"Failed: {self.stats.failed_count}" if self.stats.failed_count > 0 else None
        self.record_run(self.source_type, status, error_msg)

        return self.stats
