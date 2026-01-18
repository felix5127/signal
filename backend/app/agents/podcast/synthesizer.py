"""
[INPUT]: 依赖 outline_agent, dialogue_agent, cosyvoice_client
[OUTPUT]: 对外提供 PodcastSynthesizer 类，完整播客生成
[POS]: podcast 的合成器，整合大纲/对话/TTS
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from pathlib import Path

from app.agents.podcast.outline_agent import OutlineAgent, PodcastOutline
from app.agents.podcast.dialogue_agent import DialogueAgent, PodcastDialogue
from app.agents.podcast.cosyvoice_client import (
    CosyVoiceClient,
    cosyvoice_client,
    VoicePreset,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class PodcastPhase(str, Enum):
    """播客生成阶段"""
    INIT = "init"
    OUTLINE = "outline"
    DIALOGUE = "dialogue"
    SYNTHESIS = "synthesis"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PodcastProgress:
    """播客生成进度"""
    phase: str
    message: str
    progress: float  # 0-1
    data: Optional[Dict] = None


@dataclass
class PodcastResult:
    """播客生成结果"""
    success: bool
    outline: Optional[PodcastOutline] = None
    dialogue: Optional[PodcastDialogue] = None
    audio_path: Optional[str] = None
    duration_seconds: int = 0
    error: Optional[str] = None


# ============================================================
# 播客合成器
# ============================================================

class PodcastSynthesizer:
    """
    播客合成器

    功能:
    - 整合大纲生成、对话生成、TTS 合成
    - 流式进度反馈
    - 完整的播客生成流水线

    使用示例:
    ```python
    synthesizer = PodcastSynthesizer()

    # 同步生成
    result = await synthesizer.generate_podcast(
        research_content="研究报告内容...",
        target_duration=600,
    )
    print(result.audio_path)

    # 流式生成
    async for progress in synthesizer.generate_podcast_stream(
        research_content="研究报告内容...",
        target_duration=600,
    ):
        print(progress.message)
    ```
    """

    # 默认音色配置
    DEFAULT_VOICES = {
        "host": VoicePreset.LONGXIAOCHUN,   # 主持人: 温和男声
        "guest": VoicePreset.LONGXIAOXIA,   # 嘉宾: 温柔女声
    }

    def __init__(
        self,
        outline_agent: Optional[OutlineAgent] = None,
        dialogue_agent: Optional[DialogueAgent] = None,
        tts_client: Optional[CosyVoiceClient] = None,
    ):
        """
        初始化合成器

        Args:
            outline_agent: 大纲生成 Agent
            dialogue_agent: 对话生成 Agent
            tts_client: TTS 客户端
        """
        self.outline_agent = outline_agent or OutlineAgent()
        self.dialogue_agent = dialogue_agent or DialogueAgent()
        self.tts_client = tts_client or cosyvoice_client

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.tts_client.is_available

    async def generate_podcast(
        self,
        research_content: str,
        target_duration: int = 600,
        title: Optional[str] = None,
        output_dir: Optional[str] = None,
        voices: Optional[Dict[str, str]] = None,
    ) -> PodcastResult:
        """
        生成播客

        Args:
            research_content: 研究内容
            target_duration: 目标时长 (秒)
            title: 播客标题
            output_dir: 输出目录
            voices: 音色配置

        Returns:
            播客结果
        """
        result = PodcastResult(success=False)

        try:
            # 1. 生成大纲
            logger.info("Generating podcast outline...")
            outline = await self.outline_agent.generate_outline(
                research_content=research_content,
                target_duration=target_duration,
                custom_title=title,
            )
            result.outline = outline

            # 2. 生成对话
            logger.info("Generating podcast dialogue...")
            dialogue = await self.dialogue_agent.generate_dialogue(
                outline=outline,
                research_content=research_content,
            )
            result.dialogue = dialogue

            # 3. TTS 合成
            logger.info("Synthesizing podcast audio...")
            synthesis_result = await self._synthesize_audio(
                dialogue=dialogue,
                output_dir=output_dir,
                voices=voices,
            )

            result.audio_path = synthesis_result.output_path
            result.duration_seconds = synthesis_result.total_duration_ms // 1000
            result.success = True

            logger.info(f"Podcast generated: {result.audio_path}")

        except Exception as e:
            logger.error(f"Failed to generate podcast: {e}")
            result.error = str(e)

        return result

    async def generate_podcast_stream(
        self,
        research_content: str,
        target_duration: int = 600,
        title: Optional[str] = None,
        output_dir: Optional[str] = None,
        voices: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[PodcastProgress, None]:
        """
        流式生成播客

        Args:
            research_content: 研究内容
            target_duration: 目标时长 (秒)
            title: 播客标题
            output_dir: 输出目录
            voices: 音色配置

        Yields:
            生成进度
        """
        yield PodcastProgress(
            phase=PodcastPhase.INIT.value,
            message="开始生成播客...",
            progress=0.0,
        )

        try:
            # 1. 生成大纲
            yield PodcastProgress(
                phase=PodcastPhase.OUTLINE.value,
                message="正在生成播客大纲...",
                progress=0.1,
            )

            outline = await self.outline_agent.generate_outline(
                research_content=research_content,
                target_duration=target_duration,
                custom_title=title,
            )

            yield PodcastProgress(
                phase=PodcastPhase.OUTLINE.value,
                message=f"大纲生成完成: {outline.title}",
                progress=0.2,
                data={"title": outline.title, "sections": len(outline.sections)},
            )

            # 2. 生成对话
            yield PodcastProgress(
                phase=PodcastPhase.DIALOGUE.value,
                message="正在生成对话脚本...",
                progress=0.3,
            )

            dialogue = await self.dialogue_agent.generate_dialogue(
                outline=outline,
                research_content=research_content,
            )

            yield PodcastProgress(
                phase=PodcastPhase.DIALOGUE.value,
                message=f"对话生成完成: {len(dialogue.turns)} 轮对话",
                progress=0.5,
                data={"turns": len(dialogue.turns), "word_count": dialogue.total_word_count},
            )

            # 3. TTS 合成
            yield PodcastProgress(
                phase=PodcastPhase.SYNTHESIS.value,
                message="正在合成语音...",
                progress=0.6,
            )

            synthesis_result = await self._synthesize_audio(
                dialogue=dialogue,
                output_dir=output_dir,
                voices=voices,
            )

            yield PodcastProgress(
                phase=PodcastPhase.COMPLETED.value,
                message="播客生成完成",
                progress=1.0,
                data={
                    "audio_path": synthesis_result.output_path,
                    "duration_seconds": synthesis_result.total_duration_ms // 1000,
                },
            )

        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            yield PodcastProgress(
                phase=PodcastPhase.FAILED.value,
                message=f"生成失败: {str(e)}",
                progress=1.0,
            )

    async def _synthesize_audio(
        self,
        dialogue: PodcastDialogue,
        output_dir: Optional[str] = None,
        voices: Optional[Dict[str, str]] = None,
    ) -> SynthesisResult:
        """
        合成音频

        Args:
            dialogue: 播客对话
            output_dir: 输出目录
            voices: 音色配置

        Returns:
            合成结果
        """
        # 准备音色
        voice_map = voices or {}
        for speaker in ["host", "guest"]:
            if speaker not in voice_map:
                voice_map[speaker] = self.DEFAULT_VOICES.get(speaker, VoicePreset.LONGXIAOCHUN).value

        # 转换对话为合成格式
        segments = [
            {
                "text": turn.text,
                "speaker": turn.speaker,
                "voice": voice_map.get(turn.speaker, "longxiaochun"),
            }
            for turn in dialogue.turns
            if turn.text.strip()
        ]

        # 合成
        return await self.tts_client.synthesize_dialogue(
            segments=segments,
            output_dir=output_dir,
        )


# ============================================================
# 单例
# ============================================================

podcast_synthesizer = PodcastSynthesizer()
