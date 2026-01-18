"""
[INPUT]: 依赖 llm/kimi_client, outline_agent 的大纲
[OUTPUT]: 对外提供 DialogueAgent 类，播客对话生成
[POS]: podcast 的对话生成 Agent
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from app.agents.llm.kimi_client import kimi_client, Message, CHAT_CONFIG
from app.agents.podcast.outline_agent import PodcastOutline, PodcastSection

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

@dataclass
class DialogueTurn:
    """对话轮次"""
    speaker: str  # "host" or "guest"
    text: str
    emotion: str = "neutral"  # neutral, excited, thoughtful, humorous


@dataclass
class PodcastDialogue:
    """播客对话"""
    outline: PodcastOutline
    turns: List[DialogueTurn]
    total_word_count: int


# ============================================================
# 对话生成 Agent
# ============================================================

class DialogueAgent:
    """
    播客对话生成 Agent

    功能:
    - 根据大纲生成完整对话脚本
    - 分配说话人
    - 控制对话节奏

    使用示例:
    ```python
    agent = DialogueAgent()

    dialogue = await agent.generate_dialogue(
        outline=podcast_outline,
        research_content="研究报告内容...",
    )

    for turn in dialogue.turns:
        print(f"{turn.speaker}: {turn.text}")
    ```
    """

    SYSTEM_PROMPT = """你是一个专业的播客编剧，擅长编写自然流畅的双人对话。

## 任务
根据播客大纲和研究内容，生成完整的对话脚本。

## 对话风格
- 自然口语化，避免书面语
- 主持人 (host): 引导话题，提出问题，做总结
- 嘉宾 (guest): 深入分析，分享见解，举例说明
- 保持互动感，有问有答
- 适当加入语气词和过渡句

## 输出格式
请严格按照以下 JSON 格式输出:

```json
{
  "turns": [
    {"speaker": "host", "text": "主持人说的话", "emotion": "neutral"},
    {"speaker": "guest", "text": "嘉宾说的话", "emotion": "excited"}
  ]
}
```

## emotion 选项
- neutral: 平和
- excited: 兴奋
- thoughtful: 沉思
- humorous: 幽默

## 注意事项
- 每段话不要太长 (50-150 字)
- 保持对话节奏，避免长篇大论
- 适当加入互动 (提问、回应、附和)
- 开头要吸引人，结尾要有力"""

    def __init__(self):
        """初始化 Agent"""
        self.llm = kimi_client

    async def generate_dialogue(
        self,
        outline: PodcastOutline,
        research_content: str,
    ) -> PodcastDialogue:
        """
        生成播客对话

        Args:
            outline: 播客大纲
            research_content: 研究内容

        Returns:
            播客对话
        """
        all_turns = []

        # 生成开场
        opening_turns = await self._generate_section_dialogue(
            section_title="开场",
            section_notes=outline.opening_hook,
            research_excerpt=research_content[:500],
            is_opening=True,
        )
        all_turns.extend(opening_turns)

        # 生成每个章节的对话
        for section in outline.sections:
            section_turns = await self._generate_section_dialogue(
                section_title=section.title,
                section_notes="\n".join(section.key_points),
                research_excerpt=research_content[:2000],
                speaker_notes=section.speaker_notes,
            )
            all_turns.extend(section_turns)

        # 生成结尾
        closing_turns = await self._generate_section_dialogue(
            section_title="结尾",
            section_notes=outline.closing_cta,
            research_excerpt="",
            is_closing=True,
        )
        all_turns.extend(closing_turns)

        # 计算总字数
        total_words = sum(len(turn.text) for turn in all_turns)

        return PodcastDialogue(
            outline=outline,
            turns=all_turns,
            total_word_count=total_words,
        )

    async def _generate_section_dialogue(
        self,
        section_title: str,
        section_notes: str,
        research_excerpt: str,
        speaker_notes: Optional[Dict[str, str]] = None,
        is_opening: bool = False,
        is_closing: bool = False,
    ) -> List[DialogueTurn]:
        """
        生成章节对话

        Args:
            section_title: 章节标题
            section_notes: 章节要点
            research_excerpt: 研究内容片段
            speaker_notes: 说话人提示
            is_opening: 是否开场
            is_closing: 是否结尾

        Returns:
            对话轮次列表
        """
        context = ""
        if is_opening:
            context = "这是播客的开场白，需要吸引听众注意力，介绍本期话题。"
        elif is_closing:
            context = "这是播客的结尾，需要总结要点，感谢收听，并给出行动号召。"
        else:
            context = f"这是关于「{section_title}」的讨论章节。"

        speaker_hints = ""
        if speaker_notes:
            speaker_hints = f"\n主持人提示: {speaker_notes.get('host', '')}\n嘉宾提示: {speaker_notes.get('guest', '')}"

        user_prompt = f"""请生成以下章节的对话脚本：

## 章节信息
- 标题: {section_title}
- 要点: {section_notes}
{speaker_hints}

## 上下文
{context}

## 参考内容
{research_excerpt[:1000] if research_excerpt else "无额外参考内容"}

请输出 JSON 格式的对话。每段对话 50-150 字，生成 4-8 轮对话。"""

        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        try:
            result = await self.llm.chat(messages=messages, config=CHAT_CONFIG)

            # 解析 JSON
            dialogue_data = self._extract_json(result.content)
            turns = dialogue_data.get("turns", [])

            return [
                DialogueTurn(
                    speaker=t.get("speaker", "host"),
                    text=t.get("text", ""),
                    emotion=t.get("emotion", "neutral"),
                )
                for t in turns
                if t.get("text")
            ]

        except Exception as e:
            logger.error(f"Failed to generate section dialogue: {e}")
            # 返回默认对话
            return [
                DialogueTurn(
                    speaker="host",
                    text=f"接下来我们来聊聊{section_title}。",
                    emotion="neutral",
                ),
                DialogueTurn(
                    speaker="guest",
                    text=section_notes[:100] if section_notes else "好的，让我来分享一些见解。",
                    emotion="neutral",
                ),
            ]

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
