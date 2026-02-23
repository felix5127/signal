# ================================================================
# 播客管线优化测试
# 覆盖: 配置默认值, 日期过滤, 调度独立性, 指标计算
# ================================================================

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass


# ── 配置默认值测试 ──

class TestPodcastConfig:
    """播客配置默认值测试"""

    def test_max_items_per_feed_default(self):
        """每源抓取数应为 5（而非旧值 2）"""
        from app.config import PodcastConfig
        cfg = PodcastConfig()
        assert cfg.max_items_per_feed == 5

    def test_max_daily_items_default(self):
        """每日转写上限应为 20（而非旧值 5）"""
        from app.config import PodcastConfig
        cfg = PodcastConfig()
        assert cfg.max_daily_items == 20

    def test_transcribe_enabled_default(self):
        """转写默认应启用"""
        from app.config import PodcastConfig
        cfg = PodcastConfig()
        assert cfg.transcribe_enabled is True


# ── 播客日期过滤测试 ──

class TestPodcastDateFiltering:
    """播客采集器应仅取最近 7 天的集数"""

    def test_parse_duration_hhmmss(self):
        """时长解析 HH:MM:SS 格式"""
        from app.scrapers.podcast import PodcastScraper
        assert PodcastScraper._parse_duration("01:30:00") == 5400
        assert PodcastScraper._parse_duration("00:45:30") == 2730

    def test_parse_duration_mmss(self):
        """时长解析 MM:SS 格式"""
        from app.scrapers.podcast import PodcastScraper
        assert PodcastScraper._parse_duration("45:30") == 2730

    def test_parse_duration_seconds(self):
        """时长解析纯秒数"""
        from app.scrapers.podcast import PodcastScraper
        assert PodcastScraper._parse_duration("3600") == 3600

    def test_parse_duration_empty(self):
        """空时长返回 0"""
        from app.scrapers.podcast import PodcastScraper
        assert PodcastScraper._parse_duration("") == 0
        assert PodcastScraper._parse_duration(None) == 0

    def test_scraper_has_max_age_days_param(self):
        """scrape_single_feed 应接受 max_age_days 参数"""
        from app.scrapers.podcast import PodcastScraper
        import inspect
        sig = inspect.signature(PodcastScraper.scrape_single_feed)
        assert "max_age_days" in sig.parameters

    def test_scraper_scrape_has_max_age_days_param(self):
        """scrape 应接受 max_age_days 参数"""
        from app.scrapers.podcast import PodcastScraper
        import inspect
        sig = inspect.signature(PodcastScraper.scrape)
        assert "max_age_days" in sig.parameters


# ── 调度独立性测试 ──

class TestPodcastSchedulerIndependence:
    """播客调度应独立于文章调度"""

    def test_scheduled_podcast_pipeline_exists(self):
        """应存在独立的 scheduled_podcast_pipeline 函数"""
        from app.scheduler_jobs import scheduled_podcast_pipeline
        assert callable(scheduled_podcast_pipeline)

    def test_scheduled_main_pipeline_no_podcast(self):
        """scheduled_main_pipeline 不应再包含播客"""
        import inspect
        from app.scheduler_jobs import scheduled_main_pipeline
        source_code = inspect.getsource(scheduled_main_pipeline)
        assert "run_podcast_pipeline" not in source_code
        assert "podcast" not in source_code.lower() or "podcast" in source_code.lower().split("article")[0] is False


# ── 指标计算测试 ──

class TestPodcastPipelineMetrics:
    """播客管线指标计算测试"""

    def test_pipeline_uses_config_defaults(self):
        """run_podcast_pipeline 默认参数应从 config 读取"""
        import inspect
        from app.tasks.pipeline.podcast_pipeline import run_podcast_pipeline
        sig = inspect.signature(run_podcast_pipeline)
        # 不再硬编码 max_items_per_feed=2, max_daily_transcription=5
        # 应使用 config.podcast 的值
        params = sig.parameters
        # max_items_per_feed 默认值不应是 2
        if "max_items_per_feed" in params:
            default = params["max_items_per_feed"].default
            assert default != 2, "max_items_per_feed 不应硬编码为 2，应使用 config 值"
