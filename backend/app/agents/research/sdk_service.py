"""
[INPUT]: 依赖 anthropic SDK, tools.py, prompts.py, session_store.py
[OUTPUT]: 对外提供 ResearchSDKService 类，被 api/research.py 消费
[POS]: agents/research/ 的服务层，是 Anthropic API 的唯一集成点
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import os
import re
import structlog
from typing import AsyncIterator, Optional
from dataclasses import dataclass

import anthropic

from .tools import RESEARCH_TOOLS, execute_tool
from .prompts import (
    CHAT_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    MINDMAP_SYSTEM_PROMPT,
    AGENT_MODEL_MAP,
    AGENT_TOOL_PERMISSIONS,
    AGENT_LIMITS,
)
from .session_store import SessionStore

logger = structlog.get_logger()


# ============================================================
# SSE 事件类型
# ============================================================
@dataclass(frozen=True)
class SSEEvent:
    """SSE 事件 — 5 种简化事件类型"""
    event: str     # text / tool_start / tool_end / done / error
    data: str      # JSON 序列化数据

    def serialize(self) -> str:
        return f"event: {self.event}\ndata: {self.data}\n\n"


# ============================================================
# 研究模块 SDK 服务
# ============================================================
class ResearchSDKService:
    """
    Anthropic API 集成服务 (通过智谱代理)

    职责:
    - 管理 Anthropic 客户端实例
    - 为不同 Agent 类型构建消息和工具配置
    - 实现 Tool Use 循环 (自动调用工具并回注结果)
    - 提供流式聊天、报告生成、思维导图生成的统一接口
    - SSE 事件序列化
    """

    def __init__(self) -> None:
        self._api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
        self._base_url = os.getenv("ANTHROPIC_BASE_URL")
        self._session_store = SessionStore()
        self._client: Optional[anthropic.AsyncAnthropic] = None

        if self._api_key:
            kwargs = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = anthropic.AsyncAnthropic(**kwargs)
        else:
            logger.warning("research.sdk.init.no_api_key",
                           msg="ANTHROPIC_API_KEY 未配置，研究模块不可用")

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._client is not None

    # ============================================================
    # 流式聊天
    # ============================================================
    async def chat_stream(
        self,
        project_id: str,
        message: str,
    ) -> AsyncIterator[SSEEvent]:
        """流式对话 — 自动加载对话历史，返回 SSE 事件迭代器"""
        system_prompt = CHAT_SYSTEM_PROMPT.format(project_id=project_id)

        # 加载历史消息，实现连续对话记忆
        history = await self._session_store.load_history(project_id, limit=20)

        async for event in self._run_agent_stream(
            agent_type="chat",
            system_prompt=system_prompt,
            user_message=message,
            project_id=project_id,
            history=history,
        ):
            yield event

    # ============================================================
    # 报告生成
    # ============================================================
    async def report_stream(
        self,
        project_id: str,
        topic: Optional[str] = None,
    ) -> AsyncIterator[SSEEvent]:
        """流式生成报告"""
        system_prompt = REPORT_SYSTEM_PROMPT.format(project_id=project_id)
        user_message = topic or "请综合项目中所有源材料，生成一份全面的研究报告。"

        async for event in self._run_agent_stream(
            agent_type="report",
            system_prompt=system_prompt,
            user_message=user_message,
            project_id=project_id,
        ):
            yield event

    # ============================================================
    # 思维导图生成
    # ============================================================
    async def mindmap_stream(
        self,
        project_id: str,
        topic: Optional[str] = None,
    ) -> AsyncIterator[SSEEvent]:
        """流式生成思维导图"""
        system_prompt = MINDMAP_SYSTEM_PROMPT.format(project_id=project_id)
        user_message = topic or "请分析项目中所有源材料，生成一个思维导图。"

        async for event in self._run_agent_stream(
            agent_type="mindmap",
            system_prompt=system_prompt,
            user_message=user_message,
            project_id=project_id,
        ):
            yield event

    # ============================================================
    # 内部: Agent 流式执行 (含 Tool Use 循环)
    # ============================================================
    async def _run_agent_stream(
        self,
        agent_type: str,
        system_prompt: str,
        user_message: str,
        project_id: str,
        history: Optional[list[dict]] = None,
    ) -> AsyncIterator[SSEEvent]:
        """
        统一的 Agent 流式执行引擎

        实现 Anthropic Tool Use 循环:
        1. 发送消息给 Claude
        2. 如果 Claude 请求调用工具 (stop_reason=tool_use):
           a. 执行工具
           b. 将结果回注
           c. 继续对话
        3. 如果 Claude 输出文本 (stop_reason=end_turn):
           a. 流式输出文本
           b. 结束
        """
        model = AGENT_MODEL_MAP[agent_type]
        limits = AGENT_LIMITS[agent_type]

        # 过滤当前 Agent 允许使用的工具
        allowed = set(AGENT_TOOL_PERMISSIONS.get(agent_type, []))
        tools = [t for t in RESEARCH_TOOLS if t["name"] in allowed]

        # 构建消息列表: 历史 + 当前消息
        messages = list(history) if history else []
        messages.append({"role": "user", "content": user_message})
        references = []
        turn_count = 0
        max_turns = limits["max_turns"]

        try:
            while turn_count < max_turns:
                turn_count += 1

                # 流式调用 Anthropic API
                full_text = ""
                tool_use_blocks = []

                async with self._client.messages.stream(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=tools,
                    messages=messages,
                ) as stream:
                    async for event in stream:
                        # 文本增量
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                full_text += event.delta.text
                                yield SSEEvent(
                                    event="text",
                                    data=json.dumps(
                                        {"delta": event.delta.text},
                                        ensure_ascii=False,
                                    ),
                                )

                        # 工具调用开始
                        elif event.type == "content_block_start":
                            if hasattr(event.content_block, "name"):
                                yield SSEEvent(
                                    event="tool_start",
                                    data=json.dumps(
                                        {"tool": event.content_block.name},
                                        ensure_ascii=False,
                                    ),
                                )

                # 获取完整响应
                final_message = await stream.get_final_message()

                # 收集工具调用
                for block in final_message.content:
                    if block.type == "tool_use":
                        tool_use_blocks.append(block)

                # 如果没有工具调用，对话结束
                if final_message.stop_reason != "tool_use" or not tool_use_blocks:
                    break

                # 执行工具调用并回注结果
                messages.append({"role": "assistant", "content": final_message.content})
                tool_results = []

                for tool_block in tool_use_blocks:
                    result_text = await execute_tool(tool_block.name, tool_block.input)

                    # 从搜索结果中提取引用
                    refs = _extract_references(result_text)
                    references.extend(refs)

                    yield SSEEvent(
                        event="tool_end",
                        data=json.dumps(
                            {
                                "tool": tool_block.name,
                                "success": True,
                                "references": refs,
                            },
                            ensure_ascii=False,
                        ),
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result_text,
                    })

                messages.append({"role": "user", "content": tool_results})

            # 完成事件
            yield SSEEvent(
                event="done",
                data=json.dumps(
                    {"references": references},
                    ensure_ascii=False,
                ),
            )

        except Exception as e:
            logger.error("research.agent.stream.failed",
                         agent_type=agent_type, error=str(e))
            yield SSEEvent(
                event="error",
                data=json.dumps(
                    {"error": str(e)},
                    ensure_ascii=False,
                ),
            )


def _extract_references(text: str) -> list[dict]:
    """从工具调用结果中提取引用来源信息"""
    refs = []
    try:
        matches = re.findall(
            r'\[(\d+)\]\s+(.+?)\n\s+URL:\s+(\S+)',
            text,
        )
        for _, title, url in matches:
            if url and url.strip():
                refs.append({"title": title.strip(), "url": url.strip()})
    except Exception:
        pass
    return refs


# ============================================================
# 全局单例
# ============================================================
research_sdk_service = ResearchSDKService()
