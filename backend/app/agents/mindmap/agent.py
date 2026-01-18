"""
[INPUT]: 依赖 llm/kimi_client，研究内容文本
[OUTPUT]: 对外提供 MindmapAgent 类，概念图/思维导图生成
[POS]: mindmap 的核心 Agent，生成 Mermaid 格式图表
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.agents.llm.kimi_client import kimi_client, Message, CHAT_CONFIG

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class DiagramType(str, Enum):
    """图表类型"""
    MINDMAP = "mindmap"      # 思维导图
    FLOWCHART = "flowchart"  # 流程图
    SEQUENCE = "sequence"    # 时序图
    CLASS = "class"          # 类图
    ER = "er"                # ER 图


@dataclass
class MindmapResult:
    """概念图生成结果"""
    success: bool
    diagram_type: DiagramType
    mermaid_code: str
    title: str
    description: str
    error: Optional[str] = None


# ============================================================
# 概念图生成 Agent
# ============================================================

class MindmapAgent:
    """
    概念图生成 Agent

    功能:
    - 根据研究内容生成 Mermaid 格式图表
    - 支持多种图表类型
    - 自动提取关键概念和关系

    使用示例:
    ```python
    agent = MindmapAgent()

    result = await agent.generate_mindmap(
        content="研究报告内容...",
        diagram_type=DiagramType.MINDMAP,
    )

    print(result.mermaid_code)
    ```
    """

    SYSTEM_PROMPT = """你是一个专业的信息架构师，擅长将复杂内容提炼为清晰的可视化图表。

## 任务
根据用户提供的研究内容，生成 Mermaid 格式的图表。

## 图表类型指南

### mindmap (思维导图)
用于展示概念层次和关联。适合：
- 知识结构
- 概念分类
- 主题展开

语法示例:
```mermaid
mindmap
  root((主题))
    分支1
      子项1
      子项2
    分支2
      子项3
```

### flowchart (流程图)
用于展示流程和决策。适合：
- 工作流程
- 决策逻辑
- 系统架构

语法示例:
```mermaid
flowchart TD
    A[开始] --> B{判断}
    B -->|是| C[操作1]
    B -->|否| D[操作2]
```

### sequence (时序图)
用于展示交互过程。适合：
- API 调用
- 消息传递
- 系统交互

### class (类图)
用于展示实体关系。适合：
- 数据模型
- 系统模块
- 类结构

## 输出格式
请严格按照以下 JSON 格式输出:

```json
{
  "title": "图表标题",
  "description": "图表描述 (一句话)",
  "mermaid_code": "完整的 Mermaid 代码 (不要包含 ```mermaid 标记)"
}
```

## 注意事项
- Mermaid 代码必须语法正确
- 节点文字简洁 (3-8 个字)
- 适当使用分支和层级
- 避免过于复杂 (最多 20 个节点)
- 使用中文标签"""

    def __init__(self):
        """初始化 Agent"""
        self.llm = kimi_client

    async def generate_mindmap(
        self,
        content: str,
        diagram_type: DiagramType = DiagramType.MINDMAP,
        focus: Optional[str] = None,
    ) -> MindmapResult:
        """
        生成概念图

        Args:
            content: 研究内容
            diagram_type: 图表类型
            focus: 聚焦主题 (可选)

        Returns:
            概念图结果
        """
        type_hints = {
            DiagramType.MINDMAP: "生成思维导图，展示核心概念和层次关系",
            DiagramType.FLOWCHART: "生成流程图，展示流程步骤和决策点",
            DiagramType.SEQUENCE: "生成时序图，展示交互过程和消息流",
            DiagramType.CLASS: "生成类图，展示实体和关系",
            DiagramType.ER: "生成 ER 图，展示数据实体关系",
        }

        user_prompt = f"""请为以下内容生成 {diagram_type.value} 图表。

## 图表要求
{type_hints.get(diagram_type, "生成图表")}
{f"聚焦主题: {focus}" if focus else ""}

## 内容
{content[:4000]}

请输出 JSON 格式的结果，包含 title, description, mermaid_code 三个字段。"""

        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        try:
            result = await self.llm.chat(messages=messages, config=CHAT_CONFIG)

            # 解析 JSON
            data = self._extract_json(result.content)

            mermaid_code = data.get("mermaid_code", "")
            # 清理 mermaid 标记
            mermaid_code = self._clean_mermaid_code(mermaid_code)

            return MindmapResult(
                success=True,
                diagram_type=diagram_type,
                mermaid_code=mermaid_code,
                title=data.get("title", "概念图"),
                description=data.get("description", ""),
            )

        except Exception as e:
            logger.error(f"Failed to generate mindmap: {e}")
            return MindmapResult(
                success=False,
                diagram_type=diagram_type,
                mermaid_code="",
                title="",
                description="",
                error=str(e),
            )

    async def generate_summary_mindmap(
        self,
        content: str,
        max_depth: int = 3,
    ) -> MindmapResult:
        """
        生成内容摘要思维导图

        Args:
            content: 研究内容
            max_depth: 最大层级深度

        Returns:
            思维导图结果
        """
        user_prompt = f"""请为以下研究内容生成一个简洁的思维导图摘要。

## 要求
- 最多 {max_depth} 层深度
- 中心主题概括全文
- 一级分支为核心要点 (3-5 个)
- 二级分支为关键细节
- 节点文字精炼 (3-8 字)

## 内容
{content[:4000]}

请输出 JSON 格式的结果。"""

        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        try:
            result = await self.llm.chat(messages=messages, config=CHAT_CONFIG)
            data = self._extract_json(result.content)

            mermaid_code = self._clean_mermaid_code(data.get("mermaid_code", ""))

            return MindmapResult(
                success=True,
                diagram_type=DiagramType.MINDMAP,
                mermaid_code=mermaid_code,
                title=data.get("title", "内容摘要"),
                description=data.get("description", ""),
            )

        except Exception as e:
            logger.error(f"Failed to generate summary mindmap: {e}")
            return MindmapResult(
                success=False,
                diagram_type=DiagramType.MINDMAP,
                mermaid_code="",
                title="",
                description="",
                error=str(e),
            )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取 JSON"""
        # 尝试找到 JSON 块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1)

        # 尝试找到 { 开头的 JSON
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start != -1 and json_end != -1:
            text = text[json_start:json_end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {text[:200]}")
            return {}

    def _clean_mermaid_code(self, code: str) -> str:
        """清理 Mermaid 代码"""
        # 移除 ```mermaid 和 ``` 标记
        code = re.sub(r'^```mermaid\s*', '', code.strip())
        code = re.sub(r'\s*```$', '', code.strip())
        return code.strip()


# ============================================================
# 单例
# ============================================================

mindmap_agent = MindmapAgent()
