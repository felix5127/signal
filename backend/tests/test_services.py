# 服务层测试
# 测试SignalService的业务逻辑

import pytest
from sqlalchemy.orm import Session

from app.services.signal_service import SignalService
from app.middlewares.validation import SignalFilter
from app.models.signal import Signal


class TestSignalService:
    """SignalService测试类"""

    def test_get_signals_empty_db(self, db: Session):
        """测试空数据库获取信号列表"""
        service = SignalService(db)
        filters = SignalFilter()

        items, total = service.get_signals(filters, limit=10, offset=0)

        assert total == 0
        assert items == []

    def test_get_signals_with_data(self, db: Session, sample_signals: list[Signal]):
        """测试获取信号列表"""
        service = SignalService(db)
        filters = SignalFilter()

        items, total = service.get_signals(filters, limit=10, offset=0)

        assert total == 10
        assert len(items) == 10
        assert items[0]["id"] is not None
        assert items[0]["title"] is not None

    def test_get_signals_with_filter_by_source(self, db: Session, sample_signals: list[Signal]):
        """测试按来源筛选"""
        service = SignalService(db)
        filters = SignalFilter(source="github")

        items, total = service.get_signals(filters, limit=10, offset=0)

        # 所有示例信号都是github来源
        assert total == 10
        assert all(item["source"] == "github" for item in items)

    def test_get_signals_with_filter_by_min_score(self, db: Session, sample_signals: list[Signal]):
        """测试按最低评分筛选"""
        service = SignalService(db)
        filters = SignalFilter(min_score=4)

        items, total = service.get_signals(filters, limit=10, offset=0)

        # 应该只有final_score >= 4的信号
        assert total > 0
        assert all(item["final_score"] >= 4 for item in items)

    def test_get_signals_with_search(self, db: Session, sample_signals: list[Signal]):
        """测试搜索功能"""
        service = SignalService(db)
        filters = SignalFilter(search="Repository 1")

        items, total = service.get_signals(filters, limit=10, offset=0)

        # 应该找到标题包含"Repository 1"的信号
        assert total > 0
        assert any("Repository 1" in item["title"] for item in items)

    def test_get_signals_with_pagination(self, db: Session, sample_signals: list[Signal]):
        """测试分页功能"""
        service = SignalService(db)
        filters = SignalFilter()

        # 第一页
        items1, total1 = service.get_signals(filters, limit=5, offset=0)
        assert len(items1) == 5
        assert total1 == 10

        # 第二页
        items2, total2 = service.get_signals(filters, limit=5, offset=5)
        assert len(items2) == 5
        assert total2 == 10

        # 确保两页的数据不重复
        ids1 = {item["id"] for item in items1}
        ids2 = {item["id"] for item in items2}
        assert ids1.isdisjoint(ids2)

    def test_get_signal_by_id_exists(self, db: Session, sample_signal: Signal):
        """测试获取存在的信号"""
        service = SignalService(db)

        signal = service.get_signal_by_id(sample_signal.id)

        assert signal is not None
        assert signal["id"] == sample_signal.id
        assert signal["title"] == sample_signal.title

    def test_get_signal_by_id_not_exists(self, db: Session):
        """测试获取不存在的信号"""
        service = SignalService(db)

        signal = service.get_signal_by_id(99999)

        assert signal is None

    def test_get_signal_stats(self, db: Session, sample_signals: list[Signal]):
        """测试获取统计数据"""
        service = SignalService(db)

        stats = service.get_signal_stats()

        assert stats["total_signals"] == 10
        assert "by_source" in stats
        assert "by_category" in stats
        assert "by_score" in stats
        assert "average_scores" in stats

        # 验证来源统计
        assert stats["by_source"]["github"] == 10

        # 验证平均分
        assert stats["average_scores"]["final"] > 0

    def test_signal_to_dict(self, db: Session, sample_signal: Signal):
        """测试信号对象转换为字典"""
        service = SignalService(db)

        signal_dict = service._signal_to_dict(sample_signal)

        assert signal_dict["id"] == sample_signal.id
        assert signal_dict["title"] == sample_signal.title
        assert signal_dict["source"] == sample_signal.source
        assert "tags" in signal_dict
        assert isinstance(signal_dict["tags"], list)
