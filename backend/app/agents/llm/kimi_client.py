"""
[INPUT]: 依赖 openai (OpenAI 兼容 SDK), config.py, httpx
[OUTPUT]: 对外提供 KimiClient 类，支持 Kimi K2 系列模型 + Tool Calling
[POS]: agents/llm/ 的核心 LLM 客户端，被 Pipeline 和 MindmapAgent 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import BaseModel

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 模型配置
# ============================================================
class KimiModel(str, Enum):
    """Kimi K2 模型变体"""
    # 推理 + 工具调用 (研究任务)
    THINKING_TURBO = "kimi-k2-thinking-turbo"
    # 高速版 (对话/摘要)
    TURBO_PREVIEW = "kimi-k2-turbo-preview"
    # 标准版 (复杂任务)
    STANDARD = "kimi-k2"


@dataclass
class ModelConfig:
    """模型配置"""
    model: str = KimiModel.THINKING_TURBO
    max_tokens: int = 8192
    temperature: float = 1.0  # Thinking 模型推荐 1.0
    top_p: float = 0.95
    stream: bool = True
    context_limit: int = 250000  # 256K - buffer


# 预设配置
RESEARCH_CONFIG = ModelConfig(
    model=KimiModel.THINKING_TURBO,
    max_tokens=8192,
    temperature=1.0,
)

CHAT_CONFIG = ModelConfig(
    model=KimiModel.TURBO_PREVIEW,
    max_tokens=4096,
    temperature=0.7,
)

SUMMARY_CONFIG = ModelConfig(
    model=KimiModel.TURBO_PREVIEW,
    max_tokens=2048,
    temperature=0.5,
)


# ============================================================
# 消息类型
# ============================================================
@dataclass
class Message:
    """对话消息"""
    role: str  # user, assistant, system, tool
    content: str
    name: Optional[str] = None  # tool name
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为 API 格式"""
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        return msg


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class CompletionResult:
    """完成结果"""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    thinking: Optional[str] = None  # Thinking 模型的推理过程


# ============================================================
# Kimi 客户端
# ============================================================
class KimiClient:
    """
    Kimi K2 LLM 客户端

    支持:
    - 多模型切换 (thinking-turbo, turbo-preview, standard)
    - Tool Calling (OpenAI 兼容格式)
    - 流式输出
    - Thinking 模式 (推理过程可见)

    使用示例:
    ```python
    client = KimiClient()

    # 简单对话
    result = await client.chat([
        Message(role="user", content="什么是 Transformer?")
    ])
    print(result.content)

    # 带工具调用
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "搜索网络",
                "parameters": {...}
            }
        }
    ]
    result = await client.chat(messages, tools=tools)
    if result.tool_calls:
        for tc in result.tool_calls:
            print(f"调用工具: {tc.name}({tc.arguments})")
    ```
    """

    # Kimi API 端点
    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: Kimi API Key，默认从环境变量读取
        """
        self.api_key = api_key or config.kimi_api_key or ""
        self._client: Optional[AsyncOpenAI] = None

    def _ensure_client(self) -> AsyncOpenAI:
        """懒加载客户端"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Kimi API key not configured. Set KIMI_API_KEY environment variable.")
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
            )
        return self._client

    @property
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key)

    # ========== 核心方法 ==========

    async def chat(
        self,
        messages: List[Message],
        config: Optional[ModelConfig] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
    ) -> CompletionResult:
        """
        发送对话请求

        Args:
            messages: 消息列表
            config: 模型配置，默认使用研究配置
            tools: 工具定义列表
            tool_choice: 工具选择策略 (auto, none, required)

        Returns:
            CompletionResult
        """
        client = self._ensure_client()
        cfg = config or RESEARCH_CONFIG

        # 构建请求参数
        params = {
            "model": cfg.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": False,  # 非流式
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        try:
            response: ChatCompletion = await client.chat.completions.create(**params)

            # 解析响应
            choice = response.choices[0]
            message = choice.message

            # 解析工具调用
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {"raw": tc.function.arguments}
                    tool_calls.append(ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    ))

            return CompletionResult(
                content=message.content or "",
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            )

        except Exception as e:
            logger.error(f"Kimi chat error: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[ModelConfig] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            messages: 消息列表
            config: 模型配置
            tools: 工具定义
            tool_choice: 工具选择策略

        Yields:
            文本片段
        """
        client = self._ensure_client()
        cfg = config or RESEARCH_CONFIG

        params = {
            "model": cfg.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": True,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        try:
            stream = await client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Kimi stream error: {e}")
            raise

    # ========== 便捷方法 ==========

    async def research(
        self,
        query: str,
        context: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> CompletionResult:
        """
        研究任务 (使用 thinking-turbo)

        Args:
            query: 研究问题
            context: 上下文材料
            tools: 可用工具

        Returns:
            研究结果
        """
        messages = []

        # 系统提示
        system_prompt = """你是一个专业的研究助手，擅长深度分析和综合信息。

任务要求:
1. 仔细分析用户的研究问题
2. 如果需要更多信息，使用搜索工具获取
3. 综合所有信息，提供深入、结构化的回答
4. 引用来源，确保信息可追溯

输出格式:
- 使用 Markdown 格式
- 包含标题、要点、分析和结论
- 如有不确定的信息，明确标注"""

        messages.append(Message(role="system", content=system_prompt))

        # 上下文
        if context:
            messages.append(Message(role="user", content=f"参考材料:\n\n{context}"))

        # 问题
        messages.append(Message(role="user", content=query))

        return await self.chat(messages, config=RESEARCH_CONFIG, tools=tools)

    async def summarize(
        self,
        text: str,
        max_length: int = 500,
        language: str = "zh",
    ) -> str:
        """
        文本摘要 (使用 turbo-preview)

        Args:
            text: 待摘要文本
            max_length: 最大长度
            language: 输出语言

        Returns:
            摘要文本
        """
        lang_hint = "中文" if language == "zh" else "English"

        messages = [
            Message(role="system", content=f"你是一个专业的文本摘要助手。请用{lang_hint}输出。"),
            Message(role="user", content=f"请为以下内容生成一个不超过{max_length}字的摘要:\n\n{text}"),
        ]

        result = await self.chat(messages, config=SUMMARY_CONFIG)
        return result.content

    async def chat_turn(
        self,
        user_message: str,
        history: List[Message],
        system_prompt: Optional[str] = None,
    ) -> CompletionResult:
        """
        单轮对话 (使用 turbo-preview)

        Args:
            user_message: 用户消息
            history: 历史消息
            system_prompt: 系统提示

        Returns:
            助手回复
        """
        messages = []

        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        messages.extend(history)
        messages.append(Message(role="user", content=user_message))

        return await self.chat(messages, config=CHAT_CONFIG)


# ============================================================
# 全局实例
# ============================================================
kimi_client = KimiClient()
