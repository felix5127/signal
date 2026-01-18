"""
[INPUT]: 依赖 llm/kimi_client, tools/tavily_search, tools/vector_search, langgraph
[OUTPUT]: 对外提供 ResearchAgent 类，执行研究任务
[POS]: agents/research/ 的核心 Agent，被 API 端点消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID
import asyncio

from app.agents.llm.kimi_client import (
    KimiClient,
    kimi_client,
    Message,
    CompletionResult,
    RESEARCH_CONFIG,
)
from app.agents.tools.tavily_search import TavilySearchTool, tavily_tool
from app.agents.tools.vector_search import VectorSearchTool, vector_search_tool

logger = logging.getLogger(__name__)


# ============================================================
# 研究状态
# ============================================================
class ResearchPhase(str, Enum):
    """研究阶段"""
    INIT = "init"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ResearchState:
    """研究状态"""
    project_id: UUID
    query: str
    phase: ResearchPhase = ResearchPhase.INIT
    context: str = ""
    search_results: List[Dict] = field(default_factory=list)
    vector_results: List[Dict] = field(default_factory=list)
    thinking: str = ""
    output: str = ""
    error: Optional[str] = None
    iterations: int = 0
    max_iterations: int = 5
    tokens_used: int = 0


@dataclass
class ResearchProgress:
    """研究进度"""
    phase: str
    message: str
    progress: float  # 0-1
    data: Optional[Dict] = None


# ============================================================
# 研究 Agent
# ============================================================
class ResearchAgent:
    """
    研究助手 Agent

    功能:
    - 分析研究问题
    - 搜索网络资料 (Tavily)
    - 搜索项目材料 (向量搜索)
    - 综合生成报告

    使用示例:
    ```python
    agent = ResearchAgent()

    # 执行研究
    result = await agent.research(
        project_id="uuid",
        query="什么是 RAG？",
        context="项目相关背景...",
    )

    # 流式执行
    async for progress in agent.research_stream(project_id, query):
        print(progress.message)
    ```
    """

    # 工具定义
    TOOLS = [
        tavily_tool.tool_definition,
        vector_search_tool.tool_definition,
    ]

    # 系统提示
    SYSTEM_PROMPT = """你是一个专业的研究助手，擅长深度分析和信息综合。

## 任务
根据用户的研究问题，使用可用工具搜索信息，然后综合生成深入的研究报告。

## 可用工具
1. **tavily_search**: 搜索互联网获取最新信息
2. **vector_search**: 在项目材料中搜索相关内容

## 工作流程
1. **分析问题**: 理解用户的研究需求，识别关键概念
2. **搜索信息**:
   - 先用 vector_search 搜索项目内已有材料
   - 再用 tavily_search 搜索网络补充信息
3. **综合分析**: 整合所有信息，进行深入分析
4. **生成报告**: 输出结构化的研究报告

## 输出格式
使用 Markdown 格式，包含:
- **摘要**: 1-2 句核心结论
- **背景**: 问题背景和重要性
- **主要发现**: 分点列出关键信息
- **分析**: 深入分析和洞察
- **来源**: 引用的资料链接

## 注意事项
- 确保信息准确，标注不确定的内容
- 引用来源，保证可追溯
- 使用中文输出
- 控制在 1500 字以内"""

    def __init__(
        self,
        llm: Optional[KimiClient] = None,
        tavily: Optional[TavilySearchTool] = None,
        vector: Optional[VectorSearchTool] = None,
    ):
        """
        初始化 Agent

        Args:
            llm: LLM 客户端
            tavily: Tavily 搜索工具
            vector: 向量搜索工具
        """
        self.llm = llm or kimi_client
        self.tavily = tavily or tavily_tool
        self.vector = vector or vector_search_tool

    @property
    def is_available(self) -> bool:
        """检查 Agent 是否可用"""
        return self.llm.is_available

    async def research(
        self,
        project_id: UUID,
        query: str,
        context: Optional[str] = None,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        执行研究

        Args:
            project_id: 项目 ID
            query: 研究问题
            context: 额外上下文
            max_iterations: 最大迭代次数

        Returns:
            研究结果
        """
        state = ResearchState(
            project_id=project_id,
            query=query,
            context=context or "",
            max_iterations=max_iterations,
        )

        try:
            # 执行研究流程
            async for progress in self._run_research(state):
                logger.debug(f"Research progress: {progress.phase} - {progress.message}")

            return {
                "success": True,
                "query": state.query,
                "output": state.output,
                "search_results": state.search_results,
                "vector_results": state.vector_results,
                "tokens_used": state.tokens_used,
                "iterations": state.iterations,
            }

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "success": False,
                "query": state.query,
                "error": str(e),
            }

    async def research_stream(
        self,
        project_id: UUID,
        query: str,
        context: Optional[str] = None,
        max_iterations: int = 5,
    ) -> AsyncGenerator[ResearchProgress, None]:
        """
        流式执行研究

        Args:
            project_id: 项目 ID
            query: 研究问题
            context: 额外上下文
            max_iterations: 最大迭代次数

        Yields:
            研究进度
        """
        state = ResearchState(
            project_id=project_id,
            query=query,
            context=context or "",
            max_iterations=max_iterations,
        )

        async for progress in self._run_research(state):
            yield progress

    async def _run_research(self, state: ResearchState) -> AsyncGenerator[ResearchProgress, None]:
        """
        运行研究流程

        Args:
            state: 研究状态

        Yields:
            进度更新
        """
        # 阶段 1: 初始化
        state.phase = ResearchPhase.INIT
        yield ResearchProgress(
            phase=state.phase.value,
            message="开始研究...",
            progress=0.0,
        )

        # 构建消息
        messages = [Message(role="system", content=self.SYSTEM_PROMPT)]

        if state.context:
            messages.append(Message(
                role="user",
                content=f"项目背景材料:\n\n{state.context[:5000]}",
            ))

        messages.append(Message(
            role="user",
            content=f"研究问题: {state.query}",
        ))

        # 阶段 2: LLM 分析 + 工具调用
        while state.iterations < state.max_iterations:
            state.iterations += 1
            state.phase = ResearchPhase.ANALYZING

            yield ResearchProgress(
                phase=state.phase.value,
                message=f"分析中 (第 {state.iterations} 轮)...",
                progress=0.1 + state.iterations * 0.15,
            )

            try:
                # 调用 LLM
                result = await self.llm.chat(
                    messages=messages,
                    config=RESEARCH_CONFIG,
                    tools=self.TOOLS,
                )

                state.tokens_used += result.usage.get("total_tokens", 0)

                # 检查是否有工具调用
                if result.tool_calls:
                    state.phase = ResearchPhase.SEARCHING

                    for tool_call in result.tool_calls:
                        yield ResearchProgress(
                            phase=state.phase.value,
                            message=f"正在搜索: {tool_call.name}",
                            progress=0.3 + state.iterations * 0.1,
                        )

                        # 执行工具
                        tool_result = await self._execute_tool(
                            tool_call.name,
                            tool_call.arguments,
                            str(state.project_id),
                        )

                        # 保存结果
                        if tool_call.name == "tavily_search":
                            state.search_results.append(tool_result)
                        elif tool_call.name == "vector_search":
                            state.vector_results.append(tool_result)

                        # 添加工具调用和结果到消息
                        messages.append(Message(
                            role="assistant",
                            content="",
                            tool_calls=[{
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.name,
                                    "arguments": json.dumps(tool_call.arguments),
                                },
                            }],
                        ))
                        messages.append(Message(
                            role="tool",
                            content=json.dumps(tool_result, ensure_ascii=False),
                            tool_call_id=tool_call.id,
                        ))

                else:
                    # 没有工具调用，生成最终输出
                    state.phase = ResearchPhase.SYNTHESIZING
                    yield ResearchProgress(
                        phase=state.phase.value,
                        message="生成研究报告...",
                        progress=0.8,
                    )

                    state.output = result.content
                    state.phase = ResearchPhase.COMPLETED

                    yield ResearchProgress(
                        phase=state.phase.value,
                        message="研究完成",
                        progress=1.0,
                        data={"output": state.output},
                    )

                    return

            except Exception as e:
                logger.error(f"Research iteration error: {e}")
                state.phase = ResearchPhase.FAILED
                state.error = str(e)

                yield ResearchProgress(
                    phase=state.phase.value,
                    message=f"研究失败: {e}",
                    progress=1.0,
                )
                return

        # 达到最大迭代次数，强制生成输出
        state.phase = ResearchPhase.SYNTHESIZING
        yield ResearchProgress(
            phase=state.phase.value,
            message="达到最大迭代次数，生成报告...",
            progress=0.9,
        )

        # 最后一次调用，强制生成输出
        messages.append(Message(
            role="user",
            content="请根据已收集的信息，生成最终研究报告。",
        ))

        result = await self.llm.chat(messages=messages, config=RESEARCH_CONFIG)
        state.output = result.content
        state.phase = ResearchPhase.COMPLETED

        yield ResearchProgress(
            phase=state.phase.value,
            message="研究完成",
            progress=1.0,
            data={"output": state.output},
        )

    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        project_id: str,
    ) -> Dict[str, Any]:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 参数
            project_id: 项目 ID

        Returns:
            工具结果
        """
        try:
            if tool_name == "tavily_search":
                return await self.tavily.execute(**arguments)
            elif tool_name == "vector_search":
                arguments["project_id"] = project_id
                return await self.vector.execute(**arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"error": str(e)}


# ============================================================
# Chat Agent
# ============================================================
class ChatAgent:
    """
    对话 Agent

    用于研究项目内的问答对话。
    """

    SYSTEM_PROMPT = """你是一个研究项目的智能助手。

## 任务
回答用户关于研究材料的问题。你可以使用 vector_search 工具搜索项目中的相关内容。

## 输出要求
- 简洁明了
- 引用具体来源
- 承认不确定的地方"""

    def __init__(
        self,
        llm: Optional[KimiClient] = None,
        vector: Optional[VectorSearchTool] = None,
    ):
        self.llm = llm or kimi_client
        self.vector = vector or vector_search_tool

    async def chat(
        self,
        project_id: UUID,
        message: str,
        history: Optional[List[Message]] = None,
    ) -> CompletionResult:
        """
        对话

        Args:
            project_id: 项目 ID
            message: 用户消息
            history: 历史消息

        Returns:
            回复
        """
        from app.agents.llm.kimi_client import CHAT_CONFIG

        messages = [Message(role="system", content=self.SYSTEM_PROMPT)]

        if history:
            messages.extend(history)

        messages.append(Message(role="user", content=message))

        return await self.llm.chat(
            messages=messages,
            config=CHAT_CONFIG,
            tools=[self.vector.tool_definition],
        )
