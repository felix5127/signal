"""
[INPUT]: 依赖 阿里云百炼 CosyVoice API
[OUTPUT]: 对外提供 CosyVoiceClient 类，文本转语音服务
[POS]: podcast 的 TTS 客户端
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import logging
import asyncio
import aiofiles
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import tempfile

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class VoicePreset(str, Enum):
    """预设音色"""
    # 中文男声
    LONGXIAOCHUN = "longxiaochun"  # 龙小淳 - 温和男声
    LONGLAOTIE = "longlaotie"      # 龙老铁 - 成熟男声
    LONGSHU = "longshu"            # 龙叔 - 老年男声
    LONGXIAOBAI = "longxiaobai"    # 龙小白 - 年轻男声

    # 中文女声
    LONGXIAOXIA = "longxiaoxia"    # 龙小夏 - 温柔女声
    LONGWAN = "longwan"            # 龙婉 - 甜美女声
    LONGYUE = "longyue"            # 龙悦 - 知性女声
    LONGSHUO = "longshuo"          # 龙硕 - 活泼女声

    # 英文
    KENNY = "kenny"                # Kenny - 美式男声
    ROSA = "rosa"                  # Rosa - 美式女声


@dataclass
class SpeechSegment:
    """语音片段"""
    text: str
    speaker: str
    voice: VoicePreset
    audio_path: Optional[str] = None
    duration_ms: int = 0


@dataclass
class SynthesisResult:
    """合成结果"""
    segments: List[SpeechSegment]
    total_duration_ms: int
    output_path: str
    error: Optional[str] = None


# ============================================================
# CosyVoice 客户端
# ============================================================

class CosyVoiceClient:
    """
    阿里云百炼 CosyVoice TTS 客户端

    功能:
    - 文本转语音
    - 多音色支持 (双人对话)
    - 语音片段合成

    使用示例:
    ```python
    client = CosyVoiceClient()

    # 单段文本转语音
    audio_path = await client.synthesize_text(
        text="欢迎收听本期节目",
        voice=VoicePreset.LONGXIAOCHUN,
    )

    # 多段对话合成
    segments = [
        {"text": "大家好", "speaker": "host", "voice": "longxiaochun"},
        {"text": "我们开始吧", "speaker": "guest", "voice": "longxiaoxia"},
    ]
    result = await client.synthesize_dialogue(segments)
    ```
    """

    # API 端点
    BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2audio/generation"

    # 默认音色映射
    DEFAULT_VOICES = {
        "host": VoicePreset.LONGXIAOCHUN,      # 主持人: 温和男声
        "guest": VoicePreset.LONGXIAOXIA,      # 嘉宾: 温柔女声
        "narrator": VoicePreset.LONGYUE,       # 旁白: 知性女声
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: 百炼 API Key (默认从环境变量读取)
        """
        self.api_key = api_key or config.dashscope_api_key
        self._temp_dir = Path(tempfile.gettempdir()) / "cosyvoice"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    async def synthesize_text(
        self,
        text: str,
        voice: VoicePreset = VoicePreset.LONGXIAOCHUN,
        output_path: Optional[str] = None,
    ) -> str:
        """
        文本转语音

        Args:
            text: 待转换文本
            voice: 音色
            output_path: 输出路径 (可选)

        Returns:
            音频文件路径
        """
        if not self.is_available:
            raise RuntimeError("CosyVoice API key not configured")

        try:
            # 使用 dashscope SDK
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            dashscope.api_key = self.api_key

            # 生成输出路径
            if not output_path:
                import uuid
                output_path = str(self._temp_dir / f"{uuid.uuid4()}.mp3")

            # 调用 CosyVoice
            synthesizer = SpeechSynthesizer(
                model="cosyvoice-v1",
                voice=voice.value,
            )

            # 合成
            audio_data = synthesizer.call(text)

            # 保存音频
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(audio_data)

            logger.info(f"Synthesized audio: {output_path}")
            return output_path

        except ImportError:
            # 如果没有 dashscope SDK，使用 HTTP 请求
            return await self._synthesize_via_http(text, voice, output_path)

        except Exception as e:
            logger.error(f"Failed to synthesize text: {e}")
            raise

    async def _synthesize_via_http(
        self,
        text: str,
        voice: VoicePreset,
        output_path: Optional[str] = None,
    ) -> str:
        """
        通过 HTTP API 合成语音

        Args:
            text: 待转换文本
            voice: 音色
            output_path: 输出路径

        Returns:
            音频文件路径
        """
        import httpx
        import uuid

        if not output_path:
            output_path = str(self._temp_dir / f"{uuid.uuid4()}.mp3")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "cosyvoice-v1",
                    "input": {
                        "text": text,
                    },
                    "parameters": {
                        "voice": voice.value,
                        "format": "mp3",
                    },
                },
            )
            response.raise_for_status()

            # 解析响应
            data = response.json()
            audio_url = data.get("output", {}).get("audio_url")

            if not audio_url:
                raise ValueError(f"No audio URL in response: {data}")

            # 下载音频
            audio_response = await client.get(audio_url)
            audio_response.raise_for_status()

            async with aiofiles.open(output_path, "wb") as f:
                await f.write(audio_response.content)

        return output_path

    async def synthesize_dialogue(
        self,
        segments: List[Dict[str, Any]],
        output_dir: Optional[str] = None,
    ) -> SynthesisResult:
        """
        合成对话

        Args:
            segments: 对话片段列表
                [{"text": "...", "speaker": "host/guest", "voice": "longxiaochun"}]
            output_dir: 输出目录

        Returns:
            合成结果
        """
        if not output_dir:
            import uuid
            output_dir = str(self._temp_dir / uuid.uuid4().hex)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []
        total_duration = 0

        for i, seg in enumerate(segments):
            text = seg.get("text", "")
            speaker = seg.get("speaker", "host")
            voice_name = seg.get("voice") or self.DEFAULT_VOICES.get(speaker, VoicePreset.LONGXIAOCHUN).value

            try:
                voice = VoicePreset(voice_name)
            except ValueError:
                voice = VoicePreset.LONGXIAOCHUN

            # 合成单段
            output_path = str(Path(output_dir) / f"{i:04d}_{speaker}.mp3")
            try:
                await self.synthesize_text(text, voice, output_path)
                duration = await self._get_audio_duration(output_path)
            except Exception as e:
                logger.error(f"Failed to synthesize segment {i}: {e}")
                duration = 0

            results.append(SpeechSegment(
                text=text,
                speaker=speaker,
                voice=voice,
                audio_path=output_path,
                duration_ms=duration,
            ))
            total_duration += duration

        # 合并音频
        final_output = str(Path(output_dir) / "podcast.mp3")
        await self._merge_audio_files(
            [r.audio_path for r in results if r.audio_path],
            final_output,
        )

        return SynthesisResult(
            segments=results,
            total_duration_ms=total_duration,
            output_path=final_output,
        )

    async def _get_audio_duration(self, audio_path: str) -> int:
        """
        获取音频时长

        Args:
            audio_path: 音频文件路径

        Returns:
            时长 (毫秒)
        """
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True,
                text=True,
            )
            duration_sec = float(result.stdout.strip())
            return int(duration_sec * 1000)
        except Exception:
            return 0

    async def _merge_audio_files(
        self,
        audio_files: List[str],
        output_path: str,
    ) -> None:
        """
        合并音频文件

        Args:
            audio_files: 音频文件列表
            output_path: 输出路径
        """
        if not audio_files:
            return

        try:
            import subprocess

            # 创建文件列表
            list_file = Path(output_path).parent / "files.txt"
            with open(list_file, "w") as f:
                for audio in audio_files:
                    f.write(f"file '{audio}'\n")

            # 使用 ffmpeg 合并
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(list_file), "-c", "copy", output_path],
                capture_output=True,
                check=True,
            )

            # 清理临时文件
            list_file.unlink()

        except Exception as e:
            logger.error(f"Failed to merge audio files: {e}")
            # 如果合并失败，复制第一个文件
            if audio_files:
                import shutil
                shutil.copy(audio_files[0], output_path)


# ============================================================
# 单例
# ============================================================

cosyvoice_client = CosyVoiceClient()
