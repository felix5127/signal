# [INPUT]: 依赖 utils/llm.py (LLMClient), config.py (config)
# [OUTPUT]: 对外提供 AIService, AICallResult, FailurePolicy, CostTracker
# [POS]: 统一 AI 调用层，提供一致的失败策略、JSON 解析、成本追踪
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import json
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

import structlog

from app.config import config

logger = structlog.get_logger("ai_service")


# ============================================================
# 数据类型定义
# ============================================================

@dataclass(frozen=True)
class AICallResult:
    """AI 调用结果 (统一返回类型)"""
    success: bool
    data: Optional[dict] = None           # 解析后的 JSON
    raw_response: Optional[str] = None    # LLM 原始响应
    error: Optional[str] = None           # 错误信息
    tokens_used: int = 0                  # Token 消耗
    cost_usd: float = 0.0                 # 估算成本
    retries: int = 0                      # 重试次数
    duration_ms: float = 0.0              # 调用耗时 (ms)


class FailurePolicy(Enum):
    """AI 调用失败时的行为策略"""
    REJECT = "reject"                     # 失败即拒绝 (用于 filter)
    PENDING_REVIEW = "pending"            # 标记为待人工审核
    RETRY_THEN_SKIP = "skip"             # 重试后跳过 (用于非关键步骤)
    FALLBACK = "fallback"                 # 使用降级值


class JSONParseError(Exception):
    """JSON 解析失败"""
    pass


# ============================================================
# 成本追踪
# ============================================================

class CostTracker:
    """
    LLM 调用成本追踪

    按模型估算每次调用成本，按天聚合统计。
    """

    # 价格表 (per 1M tokens, USD)
    PRICING = {
        # OpenRouter / Direct
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
        # Moonshot / Kimi
        "moonshot-v1-8k": {"input": 0.012, "output": 0.012},
        "moonshot-v1-32k": {"input": 0.024, "output": 0.024},
        "moonshot-v1-128k": {"input": 0.06, "output": 0.06},
    }

    # 默认价格 (未知模型)
    DEFAULT_PRICING = {"input": 1.0, "output": 3.0}

    def __init__(self):
        self._daily_cost: float = 0.0
        self._daily_calls: int = 0
        self._daily_reset_date: Optional[date] = None
        self._task_costs: dict[str, float] = {}

    def _ensure_daily_reset(self):
        """每日重置计数器"""
        today = date.today()
        if self._daily_reset_date != today:
            self._daily_cost = 0.0
            self._daily_calls = 0
            self._daily_reset_date = today

    def estimate(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        task_id: Optional[str] = None,
    ) -> float:
        """
        估算单次调用成本

        Args:
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
            model: 模型名称
            task_id: 任务 ID (可选，用于分组统计)

        Returns:
            估算成本 (USD)
        """
        self._ensure_daily_reset()

        pricing = self.PRICING.get(model, self.DEFAULT_PRICING)
        cost = (
            input_tokens * pricing["input"] / 1_000_000
            + output_tokens * pricing["output"] / 1_000_000
        )

        self._daily_cost += cost
        self._daily_calls += 1

        if task_id:
            self._task_costs[task_id] = self._task_costs.get(task_id, 0.0) + cost

        return cost

    def get_daily_summary(self) -> dict:
        """获取每日成本摘要"""
        self._ensure_daily_reset()
        return {
            "date": str(self._daily_reset_date),
            "total_cost_usd": round(self._daily_cost, 4),
            "total_calls": self._daily_calls,
            "task_costs": {k: round(v, 4) for k, v in self._task_costs.items()},
        }


# ============================================================
# AIService — 统一 AI 调用服务
# ============================================================

class AIService:
    """
    统一 AI 调用服务

    职责:
    1. 统一的 LLM 调用接口 (call_json / call_text)
    2. 统一的失败策略 (FailurePolicy)
    3. 多策略 JSON 解析 (代码块 → 正则 → 大括号匹配)
    4. 成本追踪 (按任务/按模型)
    5. 调用统计 (成功率/延迟/Token)
    """

    def __init__(self, llm_client=None):
        """
        初始化 AIService

        Args:
            llm_client: LLMClient 实例 (可选，默认使用全局单例)
        """
        if llm_client is None:
            from app.utils.llm import llm_client as default_client
            llm_client = default_client
        self._client = llm_client
        self._cost_tracker = CostTracker()

    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        failure_policy: FailurePolicy = FailurePolicy.REJECT,
        fallback_value: Optional[dict] = None,
        task_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> AICallResult:
        """
        统一的 JSON 调用接口

        改进:
        - 统一的失败策略 (不再各模块自行决定)
        - 多层 JSON 解析: markdown代码块 -> 正则 -> 大括号匹配
        - 自动成本追踪
        - 结构化日志
        """
        start_time = time.monotonic()
        try:
            raw = await self._client.call(
                system_prompt,
                user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 多策略 JSON 解析
            data = self._parse_json(raw)

            # 成本追踪 (通过 LLMClient 的 Token 计数近似)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            cost = self._cost_tracker.estimate(
                input_tokens=len(system_prompt + user_prompt) // 4,  # 粗略估算
                output_tokens=len(raw) // 4,
                model=self._client.model,
                task_id=task_id,
            )

            logger.info(
                "ai.call_json.success",
                model=self._client.model,
                duration_ms=round(elapsed_ms, 1),
                cost_usd=round(cost, 6),
                task_id=task_id,
            )

            return AICallResult(
                success=True,
                data=data,
                raw_response=raw,
                cost_usd=cost,
                duration_ms=elapsed_ms,
            )

        except JSONParseError as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "ai.call_json.parse_failed",
                error=str(e),
                policy=failure_policy.value,
                task_id=task_id,
                duration_ms=round(elapsed_ms, 1),
            )
            return self._apply_failure_policy(failure_policy, fallback_value, e)

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "ai.call_json.failed",
                error=str(e),
                error_type=type(e).__name__,
                policy=failure_policy.value,
                task_id=task_id,
                duration_ms=round(elapsed_ms, 1),
            )
            return self._apply_failure_policy(failure_policy, fallback_value, e)

    async def call_text(
        self,
        system_prompt: str,
        user_prompt: str,
        failure_policy: FailurePolicy = FailurePolicy.RETRY_THEN_SKIP,
        task_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> AICallResult:
        """
        统一的纯文本调用接口

        用于不需要 JSON 解析的场景 (如翻译)。
        """
        start_time = time.monotonic()
        try:
            raw = await self._client.call(
                system_prompt,
                user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            elapsed_ms = (time.monotonic() - start_time) * 1000
            cost = self._cost_tracker.estimate(
                input_tokens=len(system_prompt + user_prompt) // 4,
                output_tokens=len(raw) // 4,
                model=self._client.model,
                task_id=task_id,
            )

            logger.info(
                "ai.call_text.success",
                model=self._client.model,
                duration_ms=round(elapsed_ms, 1),
                task_id=task_id,
            )

            return AICallResult(
                success=True,
                data=None,
                raw_response=raw,
                cost_usd=cost,
                duration_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "ai.call_text.failed",
                error=str(e),
                error_type=type(e).__name__,
                policy=failure_policy.value,
                task_id=task_id,
                duration_ms=round(elapsed_ms, 1),
            )
            return self._apply_failure_policy(failure_policy, None, e)

    def get_daily_cost(self) -> float:
        """获取当日累计成本"""
        return self._cost_tracker.get_daily_summary()["total_cost_usd"]

    def get_cost_summary(self) -> dict:
        """获取完整成本摘要"""
        return self._cost_tracker.get_daily_summary()

    # ============================================================
    # JSON 解析 — 多策略 fallback
    # ============================================================

    def _parse_json(self, raw: str) -> dict:
        """
        多策略 JSON 解析

        优先级:
        1. 提取 ```json ... ``` 代码块
        2. 提取 ``` ... ``` 普通代码块
        3. 正则匹配首个 JSON 对象
        4. 大括号平衡匹配
        5. 直接尝试 json.loads
        """
        if not raw or not raw.strip():
            raise JSONParseError("空响应")

        raw_stripped = raw.strip()

        # 策略 1: 提取 ```json ... ``` 代码块
        json_block_match = re.search(r"```json\s*\n?(.*?)\n?\s*```", raw_stripped, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 策略 2: 提取 ``` ... ``` 普通代码块
        code_block_match = re.search(r"```\s*\n?(.*?)\n?\s*```", raw_stripped, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 策略 3: 大括号平衡匹配 (处理嵌套 JSON)
        first_brace = raw_stripped.find("{")
        if first_brace != -1:
            depth = 0
            for i, ch in enumerate(raw_stripped[first_brace:], start=first_brace):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw_stripped[first_brace:i + 1])
                        except json.JSONDecodeError:
                            break

        # 策略 4: 正则匹配首个简单 JSON 对象 (无嵌套)
        json_obj_match = re.search(r"\{[^{}]*\}", raw_stripped)
        if json_obj_match:
            try:
                return json.loads(json_obj_match.group())
            except json.JSONDecodeError:
                pass

        # 策略 5: 直接尝试 json.loads
        try:
            return json.loads(raw_stripped)
        except json.JSONDecodeError:
            pass

        raise JSONParseError(f"所有 JSON 解析策略均失败, 原始响应: {raw_stripped[:200]}")

    # ============================================================
    # 失败策略处理
    # ============================================================

    def _apply_failure_policy(
        self,
        policy: FailurePolicy,
        fallback: Optional[dict],
        error: Exception,
    ) -> AICallResult:
        """根据策略返回失败结果"""
        error_msg = str(error)

        if policy == FailurePolicy.REJECT:
            return AICallResult(success=False, error=error_msg)

        if policy == FailurePolicy.PENDING_REVIEW:
            return AICallResult(
                success=False,
                error=error_msg,
                data={"status": "pending_review"},
            )

        if policy == FailurePolicy.FALLBACK and fallback is not None:
            logger.info(
                "ai.failure_policy.fallback",
                error=error_msg,
                fallback_keys=list(fallback.keys()),
            )
            return AICallResult(success=True, data=fallback)

        # RETRY_THEN_SKIP 或 FALLBACK 无降级值
        return AICallResult(success=False, error=error_msg)
