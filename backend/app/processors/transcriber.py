# Input: 音频/视频URL, 通义听悟 API credentials
# Output: 转写文本（TranscriptionResult）
# Position: 音视频转写器，使用通义听悟API将音频/视频转为文字
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    from aliyunsdkcore.auth.credentials import AccessKeyCredential
except ImportError:
    AcsClient = None
    CommonRequest = None
    AccessKeyCredential = None

import httpx


@dataclass
class TranscriptionResult:
    """转写结果"""
    text: str  # 转写文本
    duration: int  # 音频时长（秒）
    language: str  # 语言（zh/en）
    task_id: str  # 任务ID


class Transcriber:
    """
    音视频转写器（通义听悟集成）

    API 文档: https://help.aliyun.com/zh/tingwu/offline-transcribe-of-audio-and-video-files

    环境变量：
    - TINGWU_ACCESS_KEY_ID: 阿里云 AccessKey ID
    - TINGWU_ACCESS_KEY_SECRET: 阿里云 AccessKey Secret
    - TINGWU_APP_KEY: 通义听悟项目 AppKey
    """

    # API 配置
    DOMAIN = "tingwu.cn-beijing.aliyuncs.com"
    VERSION = "2023-09-30"
    SUBMIT_URI = "/openapi/tingwu/v2/tasks"
    GET_URI_PREFIX = "/openapi/tingwu/v2/tasks/"

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        app_key: Optional[str] = None,
    ):
        self.access_key_id = access_key_id or os.getenv("TINGWU_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or os.getenv("TINGWU_ACCESS_KEY_SECRET")
        self.app_key = app_key or os.getenv("TINGWU_APP_KEY")

        if not self.access_key_id or not self.access_key_secret:
            print("[Transcriber] 警告: 未配置 AccessKey")
        if not self.app_key:
            print("[Transcriber] 警告: 未配置 AppKey")

    async def transcribe(
        self,
        media_url: str,
        media_type: str = "audio",
        max_wait: int = 1800,  # 30分钟
        poll_interval: int = 10,  # 10秒
    ) -> Optional[TranscriptionResult]:
        """
        转写音频/视频文件
        """
        if not self.access_key_id or not self.access_key_secret or not self.app_key:
            print("[Transcriber] API 配置不完整，跳过转写")
            return None

        if AcsClient is None:
            print("[Transcriber] aliyun-python-sdk-core 未安装，跳过转写")
            return None

        try:
            # 1. 提交转写任务
            task_id = await self._submit_task(media_url)
            if not task_id:
                return None

            # 2. 轮询任务状态
            result = await self._poll_task(task_id, max_wait, poll_interval)
            return result

        except Exception as e:
            print(f"[Transcriber] 转写失败 {media_url}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _submit_task(self, media_url: str) -> Optional[str]:
        """
        提交转写任务

        文档: https://help.aliyun.com/zh/tingwu/offline-transcribe-of-audio-and-video-files
        """
        try:
            credentials = AccessKeyCredential(
                self.access_key_id,
                self.access_key_secret
            )
            client = AcsClient(region_id='cn-beijing', credential=credentials)

            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain(self.DOMAIN)
            request.set_version(self.VERSION)
            request.set_protocol_type('https')
            request.set_method('PUT')
            request.set_uri_pattern(self.SUBMIT_URI)
            request.add_header('Content-Type', 'application/json')
            request.add_query_param('type', 'offline')

            # 构建请求体
            body = {
                'AppKey': self.app_key,
                'Input': {
                    'SourceLanguage': 'cn',  # 中文
                    'FileUrl': media_url,
                    'TaskKey': f'task_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                },
                'Parameters': {
                    # 语音识别
                    'Transcription': {
                        'DiarizationEnabled': True,  # 启用说话人分离
                        'Diarization': {
                            'SpeakerCount': 0,  # 0 表示自动检测
                        }
                    }
                }
            }

            request.set_content(json.dumps(body).encode('utf-8'))

            print(f"[Transcriber] 提交转写任务: {media_url[:60]}...")

            response = client.do_action_with_exception(request)
            response_data = json.loads(response)

            if response_data.get('Code') != '0':
                print(f"[Transcriber] API 错误: {response_data.get('Message')}")
                return None

            task_id = response_data.get('Data', {}).get('TaskId')
            if task_id:
                print(f"[Transcriber] 任务已提交: {task_id}")
                return task_id
            else:
                print(f"[Transcriber] 响应中没有 TaskId: {response_data}")
                return None

        except Exception as e:
            print(f"[Transcriber] 提交任务失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _poll_task(
        self,
        task_id: str,
        max_wait: int = 1800,
        poll_interval: int = 10,
    ) -> Optional[TranscriptionResult]:
        """
        轮询转写任务状态
        """
        elapsed = 0

        while elapsed < max_wait:
            try:
                credentials = AccessKeyCredential(
                    self.access_key_id,
                    self.access_key_secret
                )
                client = AcsClient(region_id='cn-beijing', credential=credentials)

                request = CommonRequest()
                request.set_accept_format('json')
                request.set_domain(self.DOMAIN)
                request.set_version(self.VERSION)
                request.set_protocol_type('https')
                request.set_method('GET')
                request.set_uri_pattern(f"{self.GET_URI_PREFIX}{task_id}")
                request.add_header('Content-Type', 'application/json')

                print(f"[Transcriber] 查询任务状态: {task_id} ({elapsed}s/{max_wait}s)")

                response = client.do_action_with_exception(request)
                response_data = json.loads(response)

                if response_data.get('Code') != '0':
                    print(f"[Transcriber] API 错误: {response_data.get('Message')}")
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                    continue

                data = response_data.get('Data', {})
                status = data.get('TaskStatus')

                if status == 'COMPLETED':
                    # 获取转写结果
                    result_url = data.get('Result', {}).get('Transcription')
                    if result_url:
                        # 下载转写结果
                        text = await self._download_result(result_url)
                        duration = data.get('Output', {}).get('AudioDuration', 0)  # 毫秒

                        print(f"[Transcriber] 转写完成: {len(text)} 字符")

                        return TranscriptionResult(
                            text=text,
                            duration=int(duration / 1000) if duration else 0,
                            language="zh",
                            task_id=task_id,
                        )
                    else:
                        print("[Transcriber] 转写完成但无结果URL")
                        return None

                elif status == 'FAILED':
                    error_code = data.get('ErrorCode', '')
                    error_message = data.get('ErrorMessage', '未知错误')
                    print(f"[Transcriber] 任务失败: {error_code} - {error_message}")
                    return None

                else:
                    # ONGOING 或其他状态
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval

            except Exception as e:
                print(f"[Transcriber] 轮询失败: {e}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        print(f"[Transcriber] 任务超时: {task_id}")
        return None

    async def _download_result(self, result_url: str) -> str:
        """
        下载转写结果JSON文件
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(result_url)
                response.raise_for_status()

                data = response.json()

                # 解析转写结果
                transcripts = data.get('Transcripts', [])
                full_text = ""
                for item in transcripts:
                    text = item.get('Text', '')
                    speaker_id = item.get('SpeakerId', '')
                    begin_time = item.get('BeginTime', 0)
                    end_time = item.get('EndTime', 0)

                    # 格式化时间
                    minutes_s = begin_time // 60000
                    seconds_s = (begin_time % 60000) // 1000
                    minutes_e = end_time // 60000
                    seconds_e = (end_time % 60000) // 1000
                    time_str = f"{minutes_s:02d}:{seconds_s:02d}-{minutes_e:02d}:{seconds_e:02d}"

                    if speaker_id:
                        full_text += f"[说话人{speaker_id}] {text} ({time_str})\n"
                    else:
                        full_text += f"{text} ({time_str})\n"

                return full_text.strip()

        except Exception as e:
            print(f"[Transcriber] 下载结果失败: {e}")
            return ""


# 测试代码
async def test_transcriber():
    transcriber = Transcriber()
    print(f"\n[Transcriber] Access Key ID: {transcriber.access_key_id[:10]}..." if transcriber.access_key_id else "未配置")
    print(f"[Transcriber] AppKey: {transcriber.app_key}" if transcriber.app_key else "未配置")


if __name__ == "__main__":
    asyncio.run(test_transcriber())
