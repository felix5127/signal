"""
TDD RED: P3 后端 HIGH bug 修复测试

覆盖:
1. Feishu 配置验证 — enabled=True 但 app_id/app_secret 空时应禁用
2. Summary 字段截断 — 所有 pipeline 创建 Resource 时须截断 one_sentence_summary
3. Timezone 一致性 — digest.py 的日期计算应与 Resource.created_at 使用相同时区
"""

import inspect


# ================================================================
# 1. Feishu 配置验证
# ================================================================

class TestFeishuConfigValidation:
    """FeishuService 应在 app_id/app_secret 为空时自动禁用"""

    def test_feishu_has_is_configured_method(self):
        """FeishuService 应有 is_configured() 方法检查配置完整性"""
        from app.services.feishu_service import FeishuService
        assert hasattr(FeishuService, "is_configured"), \
            "FeishuService 需要 is_configured() 方法来检查配置完整性"

    def test_feishu_empty_config_not_configured(self):
        """空 app_id/app_secret 时 is_configured 返回 False"""
        from app.services.feishu_service import FeishuService
        service = FeishuService.__new__(FeishuService)
        service.app_id = ""
        service.app_secret = ""
        service.app_token = ""
        service.table_id = ""
        service.enabled = True
        assert not service.is_configured()

    def test_feishu_valid_config_is_configured(self):
        """配置完整时 is_configured 返回 True"""
        from app.services.feishu_service import FeishuService
        service = FeishuService.__new__(FeishuService)
        service.app_id = "cli_xxxx"
        service.app_secret = "secret"
        service.app_token = "token"
        service.table_id = "tbl_xxxx"
        service.enabled = True
        assert service.is_configured()


# ================================================================
# 2. Summary 字段截断
# ================================================================

class TestSummaryTruncation:
    """所有 pipeline 创建 Resource 时须截断 one_sentence_summary (String(500))"""

    def test_podcast_pipeline_truncates_summary(self):
        """podcast_pipeline 创建 Resource 时应截断 one_sentence_summary"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.podcast_pipeline",
                fromlist=["run_podcast_pipeline"]
            ).run_podcast_pipeline
        )
        # 应在 one_sentence_summary= 赋值处有 [:500] 截断
        assert "one_sentence_summary=signal.title[:500]" in source or \
               "one_sentence_summary=(signal.title" in source and "[:500]" in source, \
            "podcast_pipeline 的 one_sentence_summary 应截断为 500 字符"

    def test_twitter_pipeline_truncates_summary(self):
        """twitter_pipeline 创建 Resource 时应截断 one_sentence_summary"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.twitter_pipeline",
                fromlist=["run_twitter_pipeline"]
            ).run_twitter_pipeline
        )
        assert "one_sentence_summary=signal.title[:500]" in source or \
               "one_sentence_summary=(signal.title" in source and "[:500]" in source, \
            "twitter_pipeline 的 one_sentence_summary 应截断为 500 字符"

    def test_video_pipeline_truncates_summary(self):
        """video_pipeline 创建 Resource 时应截断 one_sentence_summary"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.video_pipeline",
                fromlist=["run_video_pipeline"]
            ).run_video_pipeline
        )
        assert "one_sentence_summary=signal.title[:500]" in source or \
               "one_sentence_summary=(signal.title" in source and "[:500]" in source, \
            "video_pipeline 的 one_sentence_summary 应截断为 500 字符"


# ================================================================
# 3. Timezone 一致性
# ================================================================

class TestTimezoneConsistency:
    """digest.py 应使用 datetime.now() 与 Resource.created_at 一致"""

    def test_daily_digest_uses_now_not_utcnow(self):
        """generate_daily_digest 应使用 datetime.now() 而非 datetime.utcnow()"""
        source = inspect.getsource(
            __import__("app.tasks.digest", fromlist=["generate_daily_digest"]).generate_daily_digest
        )
        # Resource.created_at 默认使用 datetime.now，digest 查询也应一致
        assert "datetime.utcnow()" not in source, \
            "digest 应使用 datetime.now() 与 Resource.created_at 保持一致"

    def test_weekly_digest_uses_now_not_utcnow(self):
        """generate_weekly_digest 应使用 datetime.now() 而非 datetime.utcnow()"""
        source = inspect.getsource(
            __import__("app.tasks.digest", fromlist=["generate_weekly_digest"]).generate_weekly_digest
        )
        assert "datetime.utcnow()" not in source, \
            "digest 应使用 datetime.now() 与 Resource.created_at 保持一致"
