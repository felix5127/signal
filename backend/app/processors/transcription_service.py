# [INPUT]: 阿里云通义听悟 API, config.py (TingwuConfig), utils/cancellation.py (CancellationToken)
# [OUTPUT]: 对外提供 TranscriptionService, TranscriptionResult, TranscriptionError, CancellationToken
# [POS]: 音视频转写服务，替代 Transcriber，提供异步非阻塞调用和单例复用
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import httpx
import structlog

from app.config import TingwuConfig
from app.utils.cancellation import CancellationToken  # 共享取消令牌

logger = structlog.get_logger("transcription_service")

# 条件导入阿里云 SDK
try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    from aliyunsdkcore.auth.credentials import AccessKeyCredential
    ALIYUN_SDK_AVAILABLE = True
except ImportError:
    AcsClient = None  # type: ignore
    CommonRequest = None  # type: ignore
    AccessKeyCredential = None  # type: ignore
    ALIYUN_SDK_AVAILABLE = False


# ============================================================
# 数据类型
# ============================================================

@dataclass(frozen=True)
class TranscriptionResult:
    """转写结果"""
    text: str           # 转写文本
    duration: int       # 音频时长 (秒)
    language: str       # 检测到的语言
    task_id: str        # 通义听悟任务 ID


class TranscriptionError(Exception):
    """转写失败"""

    def __init__(self, message: str, task_id: Optional[str] = None):
        self.task_id = task_id
        super().__init__(message)


# ============================================================
# TranscriptionService — 异步转写服务
# ============================================================

class TranscriptionService:
    """
    音视频转写服务 (替代 Transcriber)

    改进点:
    1. 同步 SDK 调用包装为 asyncio.to_thread() — 不阻塞事件循环
    2. AcsClient 单例复用 — 不再每次轮询重建
    3. 启动时配置校验 + 明确告警
    4. 可配置限额 (从 config 读取)
    5. 结构化日志 + 状态追踪
    6. 支持 CancellationToken 中途取消
    """

    # API 端点常量
    DOMAIN = "tingwu.cn-beijing.aliyuncs.com"
    VERSION = "2023-09-30"
    SUBMIT_URI = "/openapi/tingwu/v2/tasks"
    GET_URI_PREFIX = "/openapi/tingwu/v2/tasks/"

    def __init__(self, config: TingwuConfig):
        self._config = config
        self._client: Optional["AcsClient"] = None
        self._daily_count = 0
        self._daily_reset_date: Optional[date] = None

    # ============================================================
    # 配置校验
    # ============================================================

    def validate_config(self) -> list[str]:
        """
        启动时校验配置，返回缺失项列表

        Returns:
            缺失配置项的描述列表 (空列表表示配置完整)
        """
        missing: list[str] = []

        if not ALIYUN_SDK_AVAILABLE:
            missing.append("aliyun-python-sdk-core 未安装")

        if not self._config.access_key_id:
            missing.append("TINGWU_ACCESS_KEY_ID 未配置")

        if not self._config.access_key_secret:
            missing.append("TINGWU_ACCESS_KEY_SECRET 未配置")

        if not self._config.app_key:
            missing.append("TINGWU_APP_KEY 未配置")

        return missing

    def is_available(self) -> bool:
        """检查转写服务是否可用"""
        return len(self.validate_config()) == 0

    # ============================================================
    # AcsClient 单例
    # ============================================================

    def _get_client(self) -> "AcsClient":
        """获取或创建 AcsClient 单例"""
        if self._client is None:
            if not ALIYUN_SDK_AVAILABLE:
                raise TranscriptionError("aliyun-python-sdk-core 未安装")

            credentials = AccessKeyCredential(
                self._config.access_key_id,
                self._config.access_key_secret,
            )
            self._client = AcsClient(region_id="cn-beijing", credential=credentials)

        return self._client

    # ============================================================
    # 每日限额
    # ============================================================

    def _check_daily_limit(self, max_daily: int) -> bool:
        """检查是否超出每日限额"""
        today = date.today()
        if self._daily_reset_date != today:
            self._daily_count = 0
            self._daily_reset_date = today

        return self._daily_count < max_daily

    # ============================================================
    # 核心转写流程
    # ============================================================

    async def transcribe(
        self,
        media_url: str,
        media_type: str = "audio",
        cancellation_token: Optional[CancellationToken] = None,
        max_daily: int = 10,
    ) -> TranscriptionResult:
        """
        异步转写音频/视频 (非阻塞)

        改进:
        - SDK 调用通过 asyncio.to_thread() 包装
        - 支持 CancellationToken 中途取消
        - 结构化错误返回 (不再返回 None)

        Args:
            media_url: 媒体文件 URL
            media_type: 媒体类型 (audio/video)
            cancellation_token: 取消令牌 (可选)
            max_daily: 每日最大转写数

        Returns:
            TranscriptionResult

        Raises:
            TranscriptionError: 转写失败
        """
        # 校验配置
        missing = self.validate_config()
        if missing:
            raise TranscriptionError(f"配置不完整: {', '.join(missing)}")

        # 检查每日限额
        if not self._check_daily_limit(max_daily):
            raise TranscriptionError(
                f"已达每日转写限额 ({max_daily})"
            )

        logger.info(
            "transcription.started",
            media_url=media_url[:80],
            media_type=media_type,
        )

        # 1. 提交转写任务 (异步)
        task_id = await self._submit_task_async(media_url)

        # 提交成功即计入限额 (即使后续 poll 超时/失败，API 配额已消耗)
        self._daily_count += 1

        # 2. 轮询任务状态 (异步 + 可取消)
        result = await self._poll_task_async(task_id, cancellation_token)

        logger.info(
            "transcription.completed",
            task_id=task_id,
            text_length=len(result.text),
            duration=result.duration,
            daily_count=self._daily_count,
        )

        return result

    # ============================================================
    # 同步 SDK 调用 (在线程池中执行)
    # ============================================================

    async def _submit_task_async(self, media_url: str) -> str:
        """将同步提交调用放入线程池"""
        return await asyncio.to_thread(self._submit_task_sync, media_url)

    def _submit_task_sync(self, media_url: str) -> str:
        """同步提交转写任务 (在线程池中调用)"""
        client = self._get_client()

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain(self.DOMAIN)
        request.set_version(self.VERSION)
        request.set_protocol_type("https")
        request.set_method("PUT")
        request.set_uri_pattern(self.SUBMIT_URI)
        request.add_header("Content-Type", "application/json")
        request.add_query_param("type", "offline")

        body = {
            "AppKey": self._config.app_key,
            "Input": {
                "SourceLanguage": self._config.language,
                "FileUrl": media_url,
                "TaskKey": f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            },
            "Parameters": {
                "Transcription": {
                    "DiarizationEnabled": True,
                    "Diarization": {
                        "SpeakerCount": self._config.speaker_count,
                    },
                },
            },
        }

        request.set_content(json.dumps(body).encode("utf-8"))

        try:
            response = client.do_action_with_exception(request)
            response_data = json.loads(response)
        except Exception as e:
            raise TranscriptionError(f"提交任务失败: {e}")

        if response_data.get("Code") != "0":
            msg = response_data.get("Message", "未知错误")
            raise TranscriptionError(f"API 错误: {msg}")

        task_id = response_data.get("Data", {}).get("TaskId")
        if not task_id:
            raise TranscriptionError(f"响应中缺少 TaskId: {response_data}")

        logger.info("transcription.task_submitted", task_id=task_id)
        return task_id

    # ============================================================
    # 异步轮询
    # ============================================================

    async def _poll_task_async(
        self,
        task_id: str,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> TranscriptionResult:
        """
        异步轮询任务状态，支持取消

        每次查询通过 asyncio.to_thread() 包装同步 SDK 调用，
        轮询间隔使用 asyncio.sleep() 不阻塞事件循环。
        """
        poll_interval = self._config.poll_interval
        max_attempts = self._config.max_poll_attempts
        attempts = 0

        while attempts < max_attempts:
            # 检查取消信号
            if cancellation_token and cancellation_token.is_cancelled:
                logger.info("transcription.cancelled", task_id=task_id)
                raise TranscriptionError("转写已取消", task_id=task_id)

            # 查询状态 (异步)
            try:
                status, data = await asyncio.to_thread(
                    self._query_task_sync, task_id
                )
            except TranscriptionError:
                raise
            except Exception as e:
                logger.warning(
                    "transcription.poll_error",
                    task_id=task_id,
                    attempt=attempts,
                    error=str(e),
                )
                attempts += 1
                await asyncio.sleep(poll_interval)
                continue

            if status == "COMPLETED":
                result_url = data.get("Result", {}).get("Transcription")
                if not result_url:
                    raise TranscriptionError("转写完成但无结果 URL", task_id=task_id)

                text = await self._download_result(result_url)
                duration_ms = data.get("Output", {}).get("AudioDuration", 0)

                return TranscriptionResult(
                    text=text,
                    duration=int(duration_ms / 1000) if duration_ms else 0,
                    language=self._config.language,
                    task_id=task_id,
                )

            if status == "FAILED":
                error_code = data.get("ErrorCode", "")
                error_msg = data.get("ErrorMessage", "未知错误")
                raise TranscriptionError(
                    f"任务失败: {error_code} - {error_msg}",
                    task_id=task_id,
                )

            # ONGOING — 继续等待
            if attempts % 12 == 0:  # 每分钟打印一次进度
                elapsed = attempts * poll_interval
                logger.info(
                    "transcription.polling",
                    task_id=task_id,
                    elapsed_s=elapsed,
                    status=status,
                )

            attempts += 1
            await asyncio.sleep(poll_interval)

        # 超时
        raise TranscriptionError(
            f"轮询超时 ({max_attempts * poll_interval}s)",
            task_id=task_id,
        )

    def _query_task_sync(self, task_id: str) -> tuple[str, dict]:
        """同步查询任务状态 (在线程池中调用)"""
        client = self._get_client()

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain(self.DOMAIN)
        request.set_version(self.VERSION)
        request.set_protocol_type("https")
        request.set_method("GET")
        request.set_uri_pattern(f"{self.GET_URI_PREFIX}{task_id}")
        request.add_header("Content-Type", "application/json")

        try:
            response = client.do_action_with_exception(request)
            response_data = json.loads(response)
        except Exception as e:
            raise TranscriptionError(f"查询任务失败: {e}", task_id=task_id)

        if response_data.get("Code") != "0":
            msg = response_data.get("Message", "未知错误")
            raise TranscriptionError(f"API 错误: {msg}", task_id=task_id)

        data = response_data.get("Data", {})
        status = data.get("TaskStatus", "UNKNOWN")

        return status, data

    # ============================================================
    # 结果下载
    # ============================================================

    async def _download_result(self, result_url: str) -> str:
        """下载并解析转写结果 JSON"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(result_url)
                response.raise_for_status()
                data = response.json()

            # 拼接转写文本 (与旧 Transcriber 格式保持一致)
            transcripts = data.get("Transcripts", [])
            segments: list[str] = []

            for item in transcripts:
                text = item.get("Text", "")
                speaker_id = item.get("SpeakerId", "")
                begin_time = item.get("BeginTime", 0)
                end_time = item.get("EndTime", 0)

                # 格式化时间戳
                minutes_s = begin_time // 60000
                seconds_s = (begin_time % 60000) // 1000
                minutes_e = end_time // 60000
                seconds_e = (end_time % 60000) // 1000
                time_str = f"{minutes_s:02d}:{seconds_s:02d}-{minutes_e:02d}:{seconds_e:02d}"

                if speaker_id:
                    segments.append(f"[说话人{speaker_id}] {text} ({time_str})")
                else:
                    segments.append(f"{text} ({time_str})")

            return "\n".join(segments)

        except Exception as e:
            raise TranscriptionError(f"下载结果失败: {e}")
