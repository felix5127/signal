"""
[INPUT]: 依赖 agents/podcast, services/storage
[OUTPUT]: 对外提供播客生成 API 端点
[POS]: api/ 的播客路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.podcast.synthesizer import podcast_synthesizer, PodcastPhase
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/podcast", tags=["播客生成"])


# ============================================================
# Pydantic 模型
# ============================================================

class PodcastRequest(BaseModel):
    """播客生成请求"""
    content: str = Field(..., min_length=100, max_length=50000, description="研究内容")
    title: Optional[str] = Field(None, max_length=200, description="播客标题")
    target_duration: int = Field(default=600, ge=120, le=3600, description="目标时长(秒)")
    host_voice: Optional[str] = Field(default="longxiaochun", description="主持人音色")
    guest_voice: Optional[str] = Field(default="longxiaoxia", description="嘉宾音色")


class PodcastResponse(BaseModel):
    """播客响应"""
    success: bool
    audio_url: Optional[str] = None
    duration_seconds: int = 0
    title: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# API 端点
# ============================================================

@router.post("/generate", response_model=PodcastResponse)
async def generate_podcast(
    data: PodcastRequest,
):
    """
    生成播客 (同步)

    直接从文本内容生成播客。
    """
    if not podcast_synthesizer.is_available:
        raise HTTPException(
            status_code=503,
            detail="播客生成服务不可用，请检查 DASHSCOPE_API_KEY 配置"
        )

    try:
        result = await podcast_synthesizer.generate_podcast(
            research_content=data.content,
            target_duration=data.target_duration,
            title=data.title,
            voices={
                "host": data.host_voice,
                "guest": data.guest_voice,
            },
        )

        if result.success:
            # 上传到 R2
            audio_url = None
            if result.audio_path:
                upload_result = await storage_service.upload_from_path(
                    result.audio_path,
                    f"podcasts/{result.outline.title[:50] if result.outline else 'podcast'}.mp3",
                )
                if upload_result.get("success"):
                    audio_url = upload_result.get("url")

            return PodcastResponse(
                success=True,
                audio_url=audio_url,
                duration_seconds=result.duration_seconds,
                title=result.outline.title if result.outline else data.title,
            )
        else:
            return PodcastResponse(
                success=False,
                error=result.error,
            )

    except Exception as e:
        logger.error(f"Podcast generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
async def generate_podcast_stream(
    data: PodcastRequest,
):
    """
    生成播客 (SSE 流式)

    返回 Server-Sent Events 流:
    - event: progress - 进度更新
    - event: result - 最终结果
    - event: error - 错误信息
    """
    if not podcast_synthesizer.is_available:
        raise HTTPException(
            status_code=503,
            detail="播客生成服务不可用，请检查 DASHSCOPE_API_KEY 配置"
        )

    async def generate_stream():
        try:
            async for progress in podcast_synthesizer.generate_podcast_stream(
                research_content=data.content,
                target_duration=data.target_duration,
                title=data.title,
                voices={
                    "host": data.host_voice,
                    "guest": data.guest_voice,
                },
            ):
                event_data = {
                    "phase": progress.phase,
                    "message": progress.message,
                    "progress": progress.progress,
                }

                if progress.data:
                    event_data.update(progress.data)

                yield f"event: progress\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 完成时发送结果
                if progress.phase == PodcastPhase.COMPLETED.value and progress.data:
                    audio_path = progress.data.get("audio_path")
                    if audio_path:
                        # 上传到 R2
                        upload_result = await storage_service.upload_from_path(
                            audio_path,
                            f"podcasts/{data.title or 'podcast'}.mp3",
                        )
                        result_data = {
                            "success": True,
                            "audio_url": upload_result.get("url"),
                            "duration_seconds": progress.data.get("duration_seconds", 0),
                        }
                        yield f"event: result\ndata: {json.dumps(result_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Podcast stream error: {e}")
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/voices")
async def list_voices():
    """
    获取可用音色列表
    """
    return {
        "voices": [
            {"id": "longxiaochun", "name": "龙小淳", "gender": "male", "language": "zh", "description": "温和男声"},
            {"id": "longlaotie", "name": "龙老铁", "gender": "male", "language": "zh", "description": "成熟男声"},
            {"id": "longshu", "name": "龙叔", "gender": "male", "language": "zh", "description": "老年男声"},
            {"id": "longxiaobai", "name": "龙小白", "gender": "male", "language": "zh", "description": "年轻男声"},
            {"id": "longxiaoxia", "name": "龙小夏", "gender": "female", "language": "zh", "description": "温柔女声"},
            {"id": "longwan", "name": "龙婉", "gender": "female", "language": "zh", "description": "甜美女声"},
            {"id": "longyue", "name": "龙悦", "gender": "female", "language": "zh", "description": "知性女声"},
            {"id": "longshuo", "name": "龙硕", "gender": "female", "language": "zh", "description": "活泼女声"},
            {"id": "kenny", "name": "Kenny", "gender": "male", "language": "en", "description": "美式男声"},
            {"id": "rosa", "name": "Rosa", "gender": "female", "language": "en", "description": "美式女声"},
        ],
        "default": {
            "host": "longxiaochun",
            "guest": "longxiaoxia",
        },
    }
