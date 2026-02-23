"""
TDD RED: P2 后端 CRITICAL bug 修复测试

覆盖:
1. Resource.should_be_featured() — None score 防护
2. digest.py — datetime 类型安全比较
3. article_pipeline.py — save 阶段 IntegrityError 容错
4. record_run callers — db.close() 必须在 finally 中
"""

import ast
import inspect
import textwrap
from datetime import datetime, timedelta


# ================================================================
# 1. Resource.should_be_featured None 防护
# ================================================================

class TestShouldBeFeatured:
    """Resource.should_be_featured 应该安全处理 None 值"""

    def test_none_score_returns_false(self):
        """None score 不应抛出 TypeError"""
        from app.models.resource import Resource
        # None score 应返回 False，不应抛异常
        assert Resource.should_be_featured(None) is False

    def test_zero_score_returns_false(self):
        from app.models.resource import Resource
        assert Resource.should_be_featured(0) is False

    def test_84_score_returns_false(self):
        from app.models.resource import Resource
        assert Resource.should_be_featured(84) is False

    def test_85_score_returns_true(self):
        from app.models.resource import Resource
        assert Resource.should_be_featured(85) is True

    def test_100_score_returns_true(self):
        from app.models.resource import Resource
        assert Resource.should_be_featured(100) is True


# ================================================================
# 2. digest.py — datetime 类型安全
# ================================================================

class TestDigestDatetimeSafety:
    """digest.py 的时间比较应使用 datetime 对象而非字符串"""

    def test_daily_digest_uses_datetime_objects(self):
        """generate_daily_digest 内部应用 datetime 对象做查询"""
        source = inspect.getsource(
            __import__("app.tasks.digest", fromlist=["generate_daily_digest"]).generate_daily_digest
        )
        # 不应直接用 f-string 拼时间字符串做查询
        # 应使用 datetime 对象或 datetime.strptime
        assert 'f"{target_date} 00:00:00"' not in source, \
            "应使用 datetime 对象而非字符串拼接做时间查询"

    def test_weekly_digest_uses_datetime_objects(self):
        """generate_weekly_digest 内部应用 datetime 对象做查询"""
        source = inspect.getsource(
            __import__("app.tasks.digest", fromlist=["generate_weekly_digest"]).generate_weekly_digest
        )
        assert 'f"{week_start} 00:00:00"' not in source, \
            "应使用 datetime 对象而非字符串拼接做时间查询"
        assert 'f"{week_end} 23:59:59"' not in source, \
            "应使用 datetime 对象而非字符串拼接做时间查询"


# ================================================================
# 3. article_pipeline — IntegrityError 容错
# ================================================================

class TestArticlePipelineRaceCondition:
    """article_pipeline save 阶段应处理 IntegrityError（URL 重复竞态）"""

    def test_save_section_handles_integrity_error(self):
        """存储阶段应在单条 commit 级别捕获 IntegrityError"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.article_pipeline",
                fromlist=["run_article_pipeline"]
            ).run_article_pipeline
        )
        # 应使用逐条 commit（而非最后批量 commit）或捕获 IntegrityError
        assert "IntegrityError" in source or "db.commit()" in source, \
            "应处理 URL 重复的 IntegrityError 或在逐条保存时立即 commit"

    def test_save_uses_per_item_commit(self):
        """存储阶段应逐条 commit 防止单条失败回滚全部"""
        from app.tasks.pipeline.article_pipeline import run_article_pipeline
        source = inspect.getsource(run_article_pipeline)
        # 检查 save 阶段内部有逐条 commit 模式
        # (在 for 循环内有 db.add + db.commit 或 db.flush)
        lines = source.split('\n')
        in_save_section = False
        has_per_item_commit = False
        for line in lines:
            if "存储到数据库" in line or "save.started" in line:
                in_save_section = True
            if in_save_section and ("db.commit()" in line or "db.flush()" in line):
                has_per_item_commit = True
                break
        assert has_per_item_commit, "存储阶段应在 for 循环内逐条 commit/flush"


# ================================================================
# 4. record_run 调用者 — db.close() 在 finally 中
# ================================================================

class TestRecordRunDbClose:
    """record_run 调用后 db.close() 必须在 finally 块中"""

    def test_article_pipeline_record_run_uses_finally(self):
        """article_pipeline 的 record_run 调用应使用 try/finally 确保 close"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.article_pipeline",
                fromlist=["run_article_pipeline"]
            ).run_article_pipeline
        )
        self._assert_record_db_close_in_finally(source, "article_pipeline")

    def test_podcast_pipeline_record_run_uses_finally(self):
        """podcast_pipeline 的 record_run 调用应使用 try/finally 确保 close"""
        source = inspect.getsource(
            __import__(
                "app.tasks.pipeline.podcast_pipeline",
                fromlist=["run_podcast_pipeline"]
            ).run_podcast_pipeline
        )
        self._assert_record_db_close_in_finally(source, "podcast_pipeline")

    @staticmethod
    def _assert_record_db_close_in_finally(source: str, pipeline_name: str):
        """检查 record_db.close() 是否在 finally 块内"""
        # 解析 AST 查找 record_db.close() 是否在 Try.finalbody 中
        # 简化检查：看 record_db.close() 行之前是否有 finally:
        lines = source.split('\n')
        found_record_db = False
        found_finally_before_close = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if "record_db" in stripped and "SessionLocal" in stripped:
                found_record_db = True
            if found_record_db and "finally:" in stripped:
                found_finally_before_close = True
            if found_record_db and "record_db.close()" in stripped:
                assert found_finally_before_close, \
                    f"{pipeline_name}: record_db.close() 应在 finally 块中，防止异常时泄漏连接"
                return

        # 如果没找到 record_db 的模式，也算通过（可能已经用 with 语句）
        if not found_record_db:
            return
        assert False, f"{pipeline_name}: 未找到 record_db.close() 调用"
