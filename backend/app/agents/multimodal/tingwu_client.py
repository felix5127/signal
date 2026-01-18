"""
[INPUT]: 依赖 阿里云 听悟 API (语音转写)
[OUTPUT]: 对外提供 TingwuClient 类，音频/视频转写服务
[POS]: multimodal 的语音转写客户端
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from app.config import config

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

class TaskStatus(str, Enum):
    """任务状态"""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class TranscriptSegment:
    """转写片段"""
    text: str
    start_time: float  # 毫秒
    end_time: float    # 毫秒
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """转写结果"""
    task_id: str
    status: TaskStatus
    full_text: str
    segments: List[TranscriptSegment]
    duration_ms: int
    language: str
    error: Optional[str] = None


# ============================================================
# 听悟客户端
# ============================================================

class TingwuClient:
    """
    阿里云听悟语音转写客户端

    功能:
    - 创建转写任务
    - 查询任务状态
    - 获取转写结果

    使用示例:
    ```python
    client = TingwuClient()

    # 创建转写任务
    task_id = await client.create_task(
        file_url="https://example.com/audio.mp3",
        file_type="audio",
    )

    # 等待完成并获取结果
    result = await client.wait_for_result(task_id)
    print(result.full_text)
    ```
    """

    # API 端点
    BASE_URL = "https://tingwu.aliyuncs.com"
    CREATE_TASK_PATH = "/openapi/tingwu/v2/tasks"
    GET_TASK_PATH = "/openapi/tingwu/v2/tasks/{task_id}"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: 听悟 API Key (默认从环境变量读取)
        """
        self.api_key = api_key or config.tingwu.api_key
        self.app_key = config.tingwu.app_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    @property
    def client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_task(
        self,
        file_url: str,
        file_type: str = "audio",
        language: str = "auto",
        enable_speaker_diarization: bool = True,
    ) -> str:
        """
        创建转写任务

        Args:
            file_url: 文件 URL (需公开可访问)
            file_type: 文件类型 (audio/video)
            language: 语言代码 (auto/zh/en)
            enable_speaker_diarization: 是否启用说话人分离

        Returns:
            任务 ID
        """
        if not self.is_available:
            raise RuntimeError("Tingwu API key not configured")

        payload = {
            "appKey": self.app_key,
            "input": {
                "fileUrl": file_url,
                "sourceLanguage": language,
                "taskKey": f"research_{file_type}",
            },
            "parameters": {
                "transcription": {
                    "diarizationEnabled": enable_speaker_diarization,
                },
            },
        }

        try:
            response = await self.client.post(
                self.CREATE_TASK_PATH,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            task_id = data.get("data", {}).get("taskId")

            if not task_id:
                raise ValueError(f"Invalid response: {data}")

            logger.info(f"Created Tingwu task: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"Failed to create Tingwu task: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息
        """
        try:
            response = await self.client.get(
                self.GET_TASK_PATH.format(task_id=task_id),
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            raise

    async def wait_for_result(
        self,
        task_id: str,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> TranscriptionResult:
        """
        等待任务完成并获取结果

        Args:
            task_id: 任务 ID
            poll_interval: 轮询间隔 (秒)
            max_wait: 最大等待时间 (秒)

        Returns:
            转写结果
        """
        elapsed = 0.0

        while elapsed < max_wait:
            data = await self.get_task_status(task_id)
            status_data = data.get("data", {})
            status = status_data.get("taskStatus", "")

            if status == "COMPLETED":
                return self._parse_result(task_id, status_data)

            if status == "FAILED":
                error = status_data.get("errorMessage", "Unknown error")
                return TranscriptionResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    full_text="",
                    segments=[],
                    duration_ms=0,
                    language="",
                    error=error,
                )

            logger.debug(f"Task {task_id} status: {status}, waiting...")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return TranscriptionResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            full_text="",
            segments=[],
            duration_ms=0,
            language="",
            error="Timeout waiting for transcription",
        )

    def _parse_result(self, task_id: str, data: Dict) -> TranscriptionResult:
        """
        解析转写结果

        Args:
            task_id: 任务 ID
            data: API 响应数据

        Returns:
            转写结果
        """
        result_data = data.get("result", {})
        transcription = result_data.get("transcription", {})

        # 提取片段
        segments = []
        full_text_parts = []

        for paragraph in transcription.get("paragraphs", []):
            for sentence in paragraph.get("sentences", []):
                text = sentence.get("text", "")
                start = sentence.get("beginTime", 0)
                end = sentence.get("endTime", 0)
                speaker = sentence.get("speakerId")

                segments.append(TranscriptSegment(
                    text=text,
                    start_time=start,
                    end_time=end,
                    speaker=speaker,
                ))
                full_text_parts.append(text)

        return TranscriptionResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            full_text=" ".join(full_text_parts),
            segments=segments,
            duration_ms=result_data.get("duration", 0),
            language=transcription.get("language", ""),
        )

    async def transcribe(
        self,
        file_url: str,
        file_type: str = "audio",
    ) -> TranscriptionResult:
        """
        转写文件 (创建任务并等待结果)

        Args:
            file_url: 文件 URL
            file_type: 文件类型

        Returns:
            转写结果
        """
        task_id = await self.create_task(file_url, file_type)
        return await self.wait_for_result(task_id)


# ============================================================
# 单例
# ============================================================

tingwu_client = TingwuClient()
