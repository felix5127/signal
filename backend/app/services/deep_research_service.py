# Input: Resource对象, 研究策略
# Output: ResearchResult
# Position: Deep Research统一服务入口,负责策略选择、成本控制、缓存管理

from datetime import datetime, timedelta
from typing import Optional, Callable
from enum import Enum

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal
from app.models.resource import Resource
from app.utils.llm import LLMClient
from app.processors.deep_research import (
    BaseResearchEngine,
    ResearchResult,
    LightweightResearchEngine,
)
from app.processors.deep_research.search_providers import TavilySearchProvider


class ResearchStrategy(str, Enum):
    """研究策略"""

    LIGHTWEIGHT = "lightweight"  # V1轻量级
    FULL_AGENT = "full_agent"  # V2完整Multi-Agent (预留)
    AUTO = "auto"  # 自动选择


class DeepResearchService:
    """
    Deep Research 统一服务入口

    职责:
      - 策略选择
      - 成本控制
      - 缓存管理
      - 错误处理
      - 每日限额检查
    """

    def __init__(self):
        self.llm = LLMClient()
        self.search = self._create_search_provider()

        # 初始化不同策略的引擎
        self.engines = {
            ResearchStrategy.LIGHTWEIGHT: LightweightResearchEngine(
                llm_client=self.llm,
                search_provider=self.search,
                config={
                    "max_questions": config.deep_research.max_questions,
                    "max_searches_per_question": config.deep_research.max_searches_per_question,
                    "report_max_tokens": config.deep_research.report_max_tokens,
                },
            ),
            # V2预留
            # ResearchStrategy.FULL_AGENT: FullAgentResearchEngine(...)
        }

    async def generate_research(
        self,
        resource: Resource,
        strategy: ResearchStrategy = ResearchStrategy.AUTO,
        force_regenerate: bool = False,
        progress_callback: Optional[Callable] = None,
    ) -> ResearchResult:
        """
        生成深度研究报告

        Args:
            resource: 资源对象
            strategy: 研究策略 (auto会自动选择最优策略)
            force_regenerate: 强制重新生成,忽略缓存
            progress_callback: 进度回调函数

        Returns:
            ResearchResult: 研究结果

        Raises:
            HTTPException: 成本超限、每日限额等错误
        """

        # 1. 检查缓存
        if not force_regenerate and resource.deep_dive:
            if resource.deep_dive_generated_at:
                cache_age = datetime.now() - resource.deep_dive_generated_at
                cache_hours = config.deep_research.cache_duration_hours

                if cache_age.total_seconds() < cache_hours * 3600:
                    print(
                        f"[DeepResearch] 使用缓存 (生成于 {resource.deep_dive_generated_at})"
                    )
                    return self._load_from_cache(resource)

        # 2. 选择策略
        selected_strategy = self._select_strategy(resource, strategy)
        print(f"[DeepResearch] 选择策略: {selected_strategy}")

        # 3. 成本检查
        engine = self.engines[selected_strategy]
        engine.set_progress_callback(progress_callback)  # 设置进度回调
        estimated_cost = await engine.estimate_cost(resource)

        if estimated_cost > config.deep_research.max_cost_per_report:
            raise HTTPException(
                status_code=400,
                detail=f"预估成本 ${estimated_cost:.2f} 超过单篇限额 ${config.deep_research.max_cost_per_report}",
            )

        # 4. 每日限额检查
        await self._check_daily_limit()

        # 5. 执行研究
        print(f"[DeepResearch] 开始生成报告 (预估成本: ${estimated_cost:.4f})...")
        result = await engine.research(resource, max_cost=estimated_cost * 1.2)

        # 6. 保存到数据库
        await self._save_to_database(resource, result, selected_strategy)

        return result

    def _select_strategy(
        self, resource: Resource, requested: ResearchStrategy
    ) -> ResearchStrategy:
        """
        策略选择逻辑

        Args:
            resource: 资源对象
            requested: 用户请求的策略

        Returns:
            ResearchStrategy: 最终选择的策略
        """

        if requested != ResearchStrategy.AUTO:
            # 用户显式指定策略
            if requested == ResearchStrategy.FULL_AGENT:
                # TODO: V2实现后移除此检查
                print("[DeepResearch] Full Agent暂未实现,降级为Lightweight")
                return ResearchStrategy.LIGHTWEIGHT
            return requested

        # 自动选择逻辑
        # V1阶段: 总是使用lightweight
        # V2阶段: 根据资源质量选择
        #   - 高分资源 → Full Agent (更深入)
        #   - 普通资源 → Lightweight (快速)

        # TODO: V2时启用
        # if resource.score >= 85:
        #     return ResearchStrategy.FULL_AGENT

        return ResearchStrategy.LIGHTWEIGHT

    async def _check_daily_limit(self):
        """
        检查每日生成限额

        Raises:
            HTTPException: 超过每日限额
        """
        db = SessionLocal()
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            count = (
                db.query(Resource)
                .filter(Resource.deep_dive_generated_at >= today)
                .count()
            )

            max_reports = config.deep_research.max_reports_per_day

            if count >= max_reports:
                raise HTTPException(
                    status_code=429,
                    detail=f"已达到每日Deep Research限额 ({max_reports}篇)",
                )

            print(f"[DeepResearch] 今日已生成: {count}/{max_reports}")

        finally:
            db.close()

    async def _save_to_database(
        self, resource: Resource, result: ResearchResult, strategy: ResearchStrategy
    ):
        """
        保存研究结果到数据库

        Args:
            resource: 资源对象
            result: 研究结果
            strategy: 使用的策略
        """
        import json

        db = SessionLocal()
        try:
            # 更新resource对象
            db_resource = db.query(Resource).filter(Resource.id == resource.id).first()
            if db_resource:
                db_resource.deep_dive = result.content
                db_resource.deep_dive_generated_at = result.generated_at
                db_resource.deep_dive_tokens = result.tokens_used
                db_resource.deep_dive_cost = result.cost_usd
                db_resource.deep_dive_strategy = strategy.value
                db_resource.deep_dive_sources = json.dumps(result.sources)
                db_resource.deep_dive_metadata = json.dumps(result.metadata)

                db.commit()
                print(f"[DeepResearch] 已保存到数据库 (ID: {resource.id})")
        finally:
            db.close()

    def _load_from_cache(self, resource: Resource) -> ResearchResult:
        """
        从数据库缓存加载结果

        Args:
            resource: 资源对象

        Returns:
            ResearchResult: 缓存的研究结果
        """
        import json

        sources = []
        if resource.deep_dive_sources:
            try:
                sources = json.loads(resource.deep_dive_sources)
            except json.JSONDecodeError:
                sources = []

        metadata = {}
        if resource.deep_dive_metadata:
            try:
                metadata = json.loads(resource.deep_dive_metadata)
            except json.JSONDecodeError:
                metadata = {}

        return ResearchResult(
            content=resource.deep_dive,
            sources=sources,
            tokens_used=resource.deep_dive_tokens or 0,
            cost_usd=resource.deep_dive_cost or 0.0,
            research_steps=[],
            metadata={**metadata, "from_cache": True},
            generated_at=resource.deep_dive_generated_at,
        )

    def _create_search_provider(self):
        """
        创建搜索提供商

        根据配置选择不同的搜索实现

        Returns:
            BaseSearchProvider: 搜索提供商实例
        """
        provider = config.deep_research.search_provider

        if provider == "tavily":
            return TavilySearchProvider()
        # elif provider == "jina":
        #     return JinaSearchProvider()
        else:
            raise ValueError(f"Unknown search provider: {provider}")
