"""
[INPUT]: 依赖 feishu_service 的飞书 API 封装
[OUTPUT]: 对外提供 DataTracker 类和 TrackingRecord 数据类，支持 pipeline 数据追踪
[POS]: services 的数据追踪器，在 pipeline 各节点调用，收集并批量写入追踪记录
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

数据追踪器:
- 在 pipeline 各节点调用 track() 收集记录
- 支持 collected/filtered 两种状态
- 支持 dedup/language/domain/llm/whitelist 等阶段标记
- flush() 批量写入飞书，失败不影响主流程
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

from app.services.feishu_service import feishu_service


# ==============================================================================
#                             数据结构
# ==============================================================================

@dataclass
class TrackingRecord:
    """
    追踪记录

    Attributes:
        title: 内容标题
        url: 原始链接
        source: 数据来源 (HN/GitHub/RSS/Twitter 等)
        timestamp: 采集时间
        status: 状态 (collected=收录, filtered=过滤)
        reason: 收录/过滤原因
        stage: 处理阶段 (dedup/language/domain/llm/whitelist/save)
        score: LLM 评分 (可选)
        pipeline: 流水线类型 (article/full/twitter/podcast/video)
    """
    title: str
    url: str
    source: str
    timestamp: datetime
    status: Literal["collected", "filtered"]
    reason: str
    stage: str
    score: Optional[int] = None
    pipeline: str = "article"

    def to_feishu_fields(self) -> dict:
        """
        转换为飞书多维表格字段格式

        飞书字段类型映射:
        - 标题: 文本
        - URL: 链接
        - 来源: 单选
        - 时间: 日期时间 (毫秒时间戳)
        - 状态: 单选
        - 原因: 文本
        - 阶段: 单选
        - 评分: 数字
        - 流水线: 单选
        """
        fields = {
            "标题": self.title[:100] if self.title else "",  # 限制长度
            "URL": {"link": self.url, "text": self.url[:50]} if self.url else {"link": "", "text": ""},
            "来源": self.source,
            "时间": int(self.timestamp.timestamp() * 1000),  # 飞书需要毫秒时间戳
            "状态": "收录" if self.status == "collected" else "过滤",
            "原因": self.reason[:500] if self.reason else "",  # 限制长度
            "阶段": self._map_stage(self.stage),
            "流水线": self._map_pipeline(self.pipeline),
        }

        if self.score is not None:
            fields["评分"] = self.score

        return fields

    @staticmethod
    def _map_stage(stage: str) -> str:
        """阶段名称映射"""
        mapping = {
            "dedup": "去重",
            "language": "语言过滤",
            "domain": "领域过滤",
            "llm": "LLM 过滤",
            "whitelist": "白名单",
            "save": "存储",
            "extraction": "全文提取",
            "analysis": "深度分析",
            "translation": "翻译",
        }
        return mapping.get(stage, stage)

    @staticmethod
    def _map_pipeline(pipeline: str) -> str:
        """流水线名称映射"""
        mapping = {
            "article": "文章",
            "full": "多源",
            "twitter": "推特",
            "podcast": "播客",
            "video": "视频",
        }
        return mapping.get(pipeline, pipeline)


# ==============================================================================
#                             DATA TRACKER
# ==============================================================================

class DataTracker:
    """
    数据追踪器

    使用方式:
    ```python
    tracker = DataTracker(pipeline="article")

    # 记录被过滤的内容
    tracker.track(TrackingRecord(
        title="Example Article",
        url="https://example.com",
        source="RSS",
        timestamp=datetime.now(),
        status="filtered",
        reason="重复内容",
        stage="dedup",
    ))

    # 记录被收录的内容
    tracker.track(TrackingRecord(
        title="Good Article",
        url="https://example.com/good",
        source="RSS",
        timestamp=datetime.now(),
        status="collected",
        reason="LLM 评分 4 分",
        stage="llm",
        score=4,
    ))

    # 批量写入飞书
    await tracker.flush()
    ```
    """

    def __init__(self, pipeline: str = "article"):
        self.pipeline = pipeline
        self.records: list[TrackingRecord] = []

    def track(self, record: TrackingRecord):
        """添加追踪记录"""
        # 设置默认 pipeline
        if not record.pipeline or record.pipeline == "article":
            record.pipeline = self.pipeline
        self.records.append(record)

    def track_filtered(
        self,
        title: str,
        url: str,
        source: str,
        reason: str,
        stage: str,
        score: Optional[int] = None,
    ):
        """快捷方法: 记录被过滤的内容"""
        self.track(TrackingRecord(
            title=title,
            url=url,
            source=source,
            timestamp=datetime.now(),
            status="filtered",
            reason=reason,
            stage=stage,
            score=score,
            pipeline=self.pipeline,
        ))

    def track_collected(
        self,
        title: str,
        url: str,
        source: str,
        reason: str,
        stage: str,
        score: Optional[int] = None,
    ):
        """快捷方法: 记录被收录的内容"""
        self.track(TrackingRecord(
            title=title,
            url=url,
            source=source,
            timestamp=datetime.now(),
            status="collected",
            reason=reason,
            stage=stage,
            score=score,
            pipeline=self.pipeline,
        ))

    async def flush(self) -> int:
        """
        批量写入飞书

        Returns:
            成功写入的记录数
        """
        if not self.records:
            return 0

        # 转换为飞书字段格式
        feishu_records = [r.to_feishu_fields() for r in self.records]

        # 写入飞书 (异步，失败不影响主流程)
        try:
            success_count = await feishu_service.batch_create_records(feishu_records)
            print(f"[DataTracker] Flushed {success_count}/{len(self.records)} records to Feishu")

            # 清空已写入的记录
            self.records.clear()
            return success_count

        except Exception as e:
            print(f"[DataTracker] Flush failed (non-blocking): {e}")
            # 失败后清空，避免重复写入
            self.records.clear()
            return 0

    def __len__(self) -> int:
        return len(self.records)

    @property
    def collected_count(self) -> int:
        """已收录数量"""
        return sum(1 for r in self.records if r.status == "collected")

    @property
    def filtered_count(self) -> int:
        """已过滤数量"""
        return sum(1 for r in self.records if r.status == "filtered")
