"""
[INPUT]: 依赖 llm/kimi_client 生成播客大纲
[OUTPUT]: 对外提供 OutlineAgent 类，播客大纲生成
[POS]: podcast 的大纲生成 Agent
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from uuid import UUID

from app.agents.llm.kimi_client import kimi_client, Message, CHAT_CONFIG

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

@dataclass
class PodcastSection:
    """播客章节"""
    title: str
    duration_seconds: int
    key_points: List[str]
    speaker_notes: Dict[str, str] = field(default_factory=dict)


@dataclass
class PodcastOutline:
    """播客大纲"""
    title: str
    description: str
    total_duration_seconds: int
    hosts: List[str]
    sections: List[PodcastSection]
    opening_hook: str
    closing_cta: str


# ============================================================
# 大纲生成 Agent
# ============================================================

class OutlineAgent:
    """
    播客大纲生成 Agent

    功能:
    - 根据研究报告生成播客大纲
    - 确定章节结构
    - 分配说话人

    使用示例:
    ```python
    agent = OutlineAgent()

    outline = await agent.generate_outline(
        research_content="研究报告内容...",
        target_duration=600,  # 10 分钟
    )

    print(outline.title)
    for section in outline.sections:
        print(f"- {section.title}")
    ```
    """

    SYSTEM_PROMPT = """你是一个专业的播客制作人，擅长将研究报告转化为引人入胜的播客节目。

## 任务
根据提供的研究内容，生成一份播客大纲。

## 节目风格
- 双人对话形式 (主持人 + 嘉宾)
- 主持人负责引导话题、提问
- 嘉宾负责深入解读、分享见解
- 保持专业但不失亲和力

## 输出格式
请严格按照以下 JSON 格式输出:

```json
{
  "title": "播客标题",
  "description": "一句话描述",
  "hosts": ["主持人", "嘉宾"],
  "opening_hook": "开场吸引语 (30秒)",
  "sections": [
    {
      "title": "章节标题",
      "duration_seconds": 120,
      "key_points": ["要点1", "要点2"],
      "speaker_notes": {
        "host": "主持人说什么",
        "guest": "嘉宾说什么"
      }
    }
  ],
  "closing_cta": "结束语和行动号召"
}
```

## 注意事项
- 控制总时长在目标时长范围内
- 每个章节 2-3 分钟
- 开头要有吸引力
- 结尾要有行动号召"""

    def __init__(self):
        """初始化 Agent"""
        self.llm = kimi_client

    async def generate_outline(
        self,
        research_content: str,
        target_duration: int = 600,
        custom_title: Optional[str] = None,
        hosts: Optional[List[str]] = None,
    ) -> PodcastOutline:
        """
        生成播客大纲

        Args:
            research_content: 研究报告内容
            target_duration: 目标时长 (秒)
            custom_title: 自定义标题
            hosts: 主持人列表

        Returns:
            播客大纲
        """
        # 构建提示
        user_prompt = f"""请为以下研究内容生成播客大纲：

## 研究内容
{research_content[:5000]}

## 要求
- 目标时长: {target_duration // 60} 分钟
- 双人对话形式
{"- 标题: " + custom_title if custom_title else ""}
{"- 主持人: " + ", ".join(hosts) if hosts else ""}

请输出 JSON 格式的大纲。"""

        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        try:
            result = await self.llm.chat(messages=messages, config=CHAT_CONFIG)

            # 解析 JSON
            outline_data = self._extract_json(result.content)

            return PodcastOutline(
                title=outline_data.get("title", "未命名播客"),
                description=outline_data.get("description", ""),
                total_duration_seconds=target_duration,
                hosts=outline_data.get("hosts", ["主持人", "嘉宾"]),
                sections=[
                    PodcastSection(
                        title=s.get("title", ""),
                        duration_seconds=s.get("duration_seconds", 120),
                        key_points=s.get("key_points", []),
                        speaker_notes=s.get("speaker_notes", {}),
                    )
                    for s in outline_data.get("sections", [])
                ],
                opening_hook=outline_data.get("opening_hook", ""),
                closing_cta=outline_data.get("closing_cta", ""),
            )

        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            # 返回默认大纲
            return PodcastOutline(
                title=custom_title or "研究分享",
                description="深度解读研究报告",
                total_duration_seconds=target_duration,
                hosts=hosts or ["主持人", "嘉宾"],
                sections=[
                    PodcastSection(
                        title="开场介绍",
                        duration_seconds=60,
                        key_points=["欢迎收听", "本期主题"],
                    ),
                    PodcastSection(
                        title="核心内容",
                        duration_seconds=target_duration - 120,
                        key_points=["主要发现", "深度分析"],
                    ),
                    PodcastSection(
                        title="总结与展望",
                        duration_seconds=60,
                        key_points=["关键结论", "后续行动"],
                    ),
                ],
                opening_hook="欢迎收听本期节目",
                closing_cta="感谢收听，下期见",
            )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON

        Args:
            text: 包含 JSON 的文本

        Returns:
            解析后的字典
        """
        import re

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
