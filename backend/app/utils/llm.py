# Input: OpenAI API Key (config.py)
# Output: LLM 响应（JSON 格式）
# Position: LLM 调用封装，统一管理 Token 计数、超时控制和重试机制
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, RateLimitError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from app.config import config

# 配置日志
logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM API 客户端封装

    支持：
    - OpenAI (gpt-4o-mini, gpt-4o, etc.)
    - Kimi (moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k)
    - OpenRouter (多模型支持)
    - 其他兼容 OpenAI API 格式的服务

    特性：
    - 智能重试（最多 3 次，指数退避 2-8 秒）
    - 针对超时、连接错误、限流错误自动重试
    - 超时控制（默认 60s，可配置）
    - Token 计数（用于成本控制）
    - 结构化输出（JSON）
    """

    def __init__(self):
        # 根据 provider 配置选择 base_url 和 api_key
        provider = config.llm.provider.lower()

        if provider == "kimi" or provider == "moonshot":
            # Kimi/Moonshot API
            base_url = "https://api.moonshot.cn/v1"
            api_key = config.openai_api_key  # 复用这个字段存储 Kimi API Key
        elif provider == "openai":
            # OpenAI 官方 API
            base_url = None  # 使用默认值
            api_key = config.openai_api_key
        elif provider == "openrouter":
            # OpenRouter API
            base_url = getattr(config.llm, "base_url", "https://openrouter.ai/api/v1")
            api_key = config.openai_api_key  # OpenRouter API Key
        else:
            # 其他兼容 OpenAI 格式的 API（如 Ollama, vLLM）
            base_url = getattr(config.llm, "base_url", None)
            api_key = config.openai_api_key

        # 初始化客户端（使用配置的超时时间，摘要生成一般不需要太长）
        from httpx import Timeout
        # 使用 60 秒超时（摘要生成足够），避免长时间等待
        timeout_seconds = float(config.llm.timeout) if hasattr(config.llm, 'timeout') else 60.0
        timeout = Timeout(
            timeout=timeout_seconds,      # 总超时
            connect=10.0,                 # 连接超时
            read=timeout_seconds,         # 读取超时（关键）
            write=10.0,                   # 写入超时
            pool=5.0                      # 连接池超时
        )

        if base_url:
            # OpenRouter需要额外的headers
            if provider == "openrouter":
                default_headers = {
                    "HTTP-Referer": "https://github.com/yourusername/signal-hunter",  # 可选,用于分析
                    "X-Title": "AI Signal Hunter"  # 可选,显示在OpenRouter dashboard
                }
                self.client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=timeout,
                    default_headers=default_headers
                )
            else:
                self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        else:
            self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)

        self.model = config.llm.model
        self.timeout = config.llm.timeout
        self.max_tokens = config.llm.max_tokens
        self.temperature = config.llm.temperature

        # Token 计数器（简单统计）
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        print(f"[LLM] Initialized with provider={provider}, model={self.model}, timeout={timeout_seconds}s")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APITimeoutError, APIConnectionError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        调用 LLM API（带自动重试机制）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数（默认使用配置值）
            max_tokens: 最大 token 数（默认使用配置值）

        Returns:
            LLM 响应文本

        Raises:
            APITimeoutError: API 超时（重试 3 次后仍失败）
            APIConnectionError: 网络连接错误（重试 3 次后仍失败）
            RateLimitError: API 限流（重试 3 次后仍失败）
            Exception: 其他 API 调用失败（不重试）
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            # 统计 Token
            usage = response.usage
            if usage:
                self.total_input_tokens += usage.prompt_tokens
                self.total_output_tokens += usage.completion_tokens

            return response.choices[0].message.content

        except (APITimeoutError, APIConnectionError, RateLimitError) as e:
            # 这些错误会触发重试，由 @retry 装饰器处理
            logger.warning(f"[LLM] Retryable error occurred: {type(e).__name__}: {e}")
            raise
        except Exception as e:
            # 其他错误不重试，直接抛出
            logger.error(f"[LLM] Non-retryable error occurred: {type(e).__name__}: {e}")
            raise

    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        调用 OpenAI API 并返回 JSON

        在 system_prompt 中要求返回 JSON 格式，此方法会自动解析

        Args:
            system_prompt: 系统提示词（需包含 "返回 JSON" 指令）
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            解析后的 JSON 字典

        Raises:
            json.JSONDecodeError: 返回结果不是有效 JSON
            Exception: API 调用失败
        """
        response_text = await self.call(
            system_prompt, user_prompt, temperature, max_tokens
        )

        # 尝试从 Markdown 代码块中提取 JSON
        # LLM 有时会返回 ```json\n{...}\n``` 格式
        if "```json" in response_text:
            # 提取代码块
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            # 提取普通代码块
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        else:
            json_str = response_text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[LLM] Failed to parse JSON: {response_text}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        """
        获取 Token 使用统计

        Returns:
            {"input": xxx, "output": xxx, "total": xxx}
        """
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "total": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_token_counter(self):
        """重置 Token 计数器"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# 全局单例
llm_client = LLMClient()
