"""
[INPUT]: 依赖 app.utils.llm (LLMClient), app.config
[OUTPUT]: 对外提供 PodcastAnalyzer 类，生成章节和 Q&A 数据
[POS]: processors/ 的播客内容分析器，从转录文本提取结构化信息
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from app.utils.llm import LLMClient
from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Chapter:
    """章节"""
    time: int  # 时间戳（秒）
    title: str  # 章节标题
    summary: Optional[str] = None  # 章节摘要


@dataclass
class QAPair:
    """问答对"""
    question: str  # 问题
    answer: str  # 回答
    timestamp: Optional[int] = None  # 对应时间戳（秒）


@dataclass
class PodcastAnalysisResult:
    """播客分析结果"""
    chapters: List[Chapter]
    qa_pairs: List[QAPair]
    raw_response: Optional[str] = None


# ============================================================
# 播客内容分析器
# ============================================================

class PodcastAnalyzer:
    """
    播客内容分析器

    从转录文本中提取：
    - 章节信息（时间戳 + 标题 + 摘要）
    - Q&A 对（问题 + 回答 + 时间戳）

    使用示例:
    ```python
    analyzer = PodcastAnalyzer()
    result = await analyzer.analyze(transcript, duration=3600)
    print(result.chapters)
    print(result.qa_pairs)
    ```
    """

    # --------------------------------------------------------
    # Prompt 模板
    # --------------------------------------------------------

    CHAPTER_PROMPT = """你是一个专业的播客内容分析师。请分析以下播客转录文本，提取章节信息。

播客时长: {duration} 秒
转录文本:
{transcript}

请分析内容，提取 5-10 个章节。每个章节包含：
- time: 预估的开始时间（秒），基于内容在全文中的位置比例估算
- title: 章节标题（10-20字，概括该部分主题）
- summary: 章节摘要（30-50字，概括该部分内容）

返回 JSON 格式：
```json
{{
  "chapters": [
    {{"time": 0, "title": "开场与嘉宾介绍", "summary": "主持人介绍本期主题和嘉宾背景"}},
    {{"time": 300, "title": "...", "summary": "..."}}
  ]
}}
```

重要：
1. 时间戳应基于内容位置估算（例如：某段内容在全文 30% 位置，时长 3600 秒，则 time ≈ 1080）
2. 章节标题要简洁有力，突出主题
3. 章节摘要要概括该部分的核心内容"""

    QA_PROMPT = """你是一个专业的播客内容分析师。请分析以下播客转录文本，提取问答对。

转录文本:
{transcript}

请从内容中提取有价值的问答对，包括：
- 明确的问答环节
- 隐含的问题和回答（如"很多人会问..."）
- 关键知识点（可以转化为问答形式）

每个问答对包含：
- question: 问题（清晰简洁）
- answer: 回答（100-200字，完整概括）
- timestamp: 预估的时间戳（秒，可选）

返回 JSON 格式：
```json
{{
  "qa_pairs": [
    {{"question": "AI 会取代程序员吗？", "answer": "短期内不会...", "timestamp": 600}},
    {{"question": "...", "answer": "..."}}
  ]
}}
```

重要：
1. 提取 5-15 个有价值的问答对
2. 问题要具有代表性，是听众可能关心的
3. 回答要完整准确，忠于原文观点"""

    def __init__(self):
        """初始化分析器"""
        self.llm = LLMClient()

    async def analyze(
        self,
        transcript: str,
        duration: Optional[int] = None,
    ) -> PodcastAnalysisResult:
        """
        分析播客转录文本

        Args:
            transcript: 转录文本
            duration: 播客时长（秒），用于估算时间戳

        Returns:
            PodcastAnalysisResult: 分析结果
        """
        if not transcript or len(transcript) < 100:
            logger.warning("[PodcastAnalyzer] 转录文本太短，跳过分析")
            return PodcastAnalysisResult(chapters=[], qa_pairs=[])

        # 截取前 15000 字符（约 7500 字，避免超出 LLM 上下文限制）
        truncated = transcript[:15000]
        duration = duration or 3600  # 默认 1 小时

        # 并行分析章节和 Q&A
        chapters = await self._extract_chapters(truncated, duration)
        qa_pairs = await self._extract_qa_pairs(truncated)

        return PodcastAnalysisResult(
            chapters=chapters,
            qa_pairs=qa_pairs,
        )

    async def _extract_chapters(
        self,
        transcript: str,
        duration: int,
    ) -> List[Chapter]:
        """提取章节信息"""
        try:
            prompt = self.CHAPTER_PROMPT.format(
                transcript=transcript,
                duration=duration,
            )
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            # 解析 JSON
            data = self._parse_json_response(response)
            chapters = data.get("chapters", [])

            return [
                Chapter(
                    time=ch.get("time", 0),
                    title=ch.get("title", ""),
                    summary=ch.get("summary"),
                )
                for ch in chapters
                if ch.get("title")
            ]
        except Exception as e:
            logger.error(f"[PodcastAnalyzer] 提取章节失败: {e}")
            return []

    async def _extract_qa_pairs(self, transcript: str) -> List[QAPair]:
        """提取问答对"""
        try:
            prompt = self.QA_PROMPT.format(transcript=transcript)
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            # 解析 JSON
            data = self._parse_json_response(response)
            qa_pairs = data.get("qa_pairs", [])

            return [
                QAPair(
                    question=qa.get("question", ""),
                    answer=qa.get("answer", ""),
                    timestamp=qa.get("timestamp"),
                )
                for qa in qa_pairs
                if qa.get("question") and qa.get("answer")
            ]
        except Exception as e:
            logger.error(f"[PodcastAnalyzer] 提取 Q&A 失败: {e}")
            return []

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        # 尝试提取 JSON 块
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("[PodcastAnalyzer] JSON 解析失败，尝试修复")
            # 尝试找到 { 和 } 之间的内容
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(json_str[start:end])
            return {}


# ============================================================
# 全局实例
# ============================================================

podcast_analyzer = PodcastAnalyzer()
