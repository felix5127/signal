"""
[INPUT]: 依赖 database 的 SessionLocal, models/resource 的 Resource, scrapers/favicon 的 FaviconFetcher
[OUTPUT]: 对外提供 PipelineStats, BasePipeline
[POS]: 流水线公共基类，提供去重检查、保存逻辑、进度打印等通用功能
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set

from app.database import SessionLocal
from app.models.resource import Resource


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
