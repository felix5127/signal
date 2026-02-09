"""
[INPUT]: 依赖 agents/research/sdk_service, models/research, services/storage, database
[OUTPUT]: 对外提供研究助手 API 端点
[POS]: api/ 的研究助手路由，被 main.py 注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.research import (
    ResearchProject,
    ResearchSource,
    ResearchOutput,
    ChatMessage,
    SourceEmbedding,
)
from app.agents.research.sdk_service import research_sdk_service
from app.agents.embeddings.bailian_embedding import embedding_service, TextSplitter
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["研究助手"])


# ============================================================
# Pydantic 模型
# ============================================================
class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    source_count: int
    output_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    """添加源请求"""
    source_type: str = Field(..., pattern="^(url|pdf|audio|video|text)$")
    title: Optional[str] = None
    original_url: Optional[str] = None
    content: Optional[str] = None  # 纯文本内容


class SourceResponse(BaseModel):
    """源响应"""
    id: UUID
    project_id: UUID
    source_type: str
    title: Optional[str]
    original_url: Optional[str]
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatStreamRequest(BaseModel):
    """对话流式请求"""
    message: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: UUID
    role: str
    content: str
    starred: bool
    references: List[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    """生成请求"""
    topic: Optional[str] = None


# ============================================================
# 项目 API
# ============================================================
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, pattern="^(active|archived)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取项目列表"""
    query = db.query(ResearchProject)

    if status:
        query = query.filter(ResearchProject.status == status)

    query = query.order_by(ResearchProject.created_at.desc())
    projects = query.offset(skip).limit(limit).all()

    return projects


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
):
    """创建研究项目"""
    project = ResearchProject(
        name=data.name,
        description=data.description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"Created project: {project.id} - {project.name}")

    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """获取项目详情"""
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """删除项目"""
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 删除关联的存储文件
    await storage_service.delete_folder(f"research/{project_id}/")

    db.delete(project)
    db.commit()

    logger.info(f"Deleted project: {project_id}")

    return {"success": True, "message": "Project deleted"}


# ============================================================
# 源材料 API
# ============================================================
@router.get("/projects/{project_id}/sources", response_model=List[SourceResponse])
async def list_sources(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """获取项目源材料列表"""
    sources = (
        db.query(ResearchSource)
        .filter(ResearchSource.project_id == project_id)
        .order_by(ResearchSource.created_at.desc())
        .all()
    )

    return sources


@router.post("/projects/{project_id}/sources", response_model=SourceResponse)
async def add_source(
    project_id: UUID,
    data: SourceCreate,
    db: Session = Depends(get_db),
):
    """添加源材料"""
    # 验证项目存在
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    source = ResearchSource(
        project_id=project_id,
        source_type=data.source_type,
        title=data.title,
        original_url=data.original_url,
        full_text=data.content,
        processing_status="pending",
    )

    db.add(source)

    # 更新项目统计
    project.source_count += 1

    db.commit()
    db.refresh(source)

    # 异步处理 (如果是文本，直接生成嵌入)
    if data.content and data.source_type == "text":
        import asyncio

        async def generate_text_embeddings(source_id: UUID, text: str):
            """异步生成文本嵌入 — 使用独立 DB session"""
            bg_db = SessionLocal()
            try:
                if not embedding_service.is_available:
                    logger.warning("Embedding service not available")
                    return

                splitter = TextSplitter()
                chunks = splitter.split_text(text, chunk_size=1000, overlap=100)
                if not chunks:
                    return

                embeddings = await embedding_service.embed_texts(chunks)

                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    source_embedding = SourceEmbedding(
                        source_id=source_id,
                        chunk_index=i,
                        chunk_text=chunk,
                        embedding=embedding,
                    )
                    bg_db.add(source_embedding)

                src = bg_db.query(ResearchSource).filter(ResearchSource.id == source_id).first()
                if src:
                    src.processing_status = "completed"

                bg_db.commit()
                logger.info(f"Generated {len(embeddings)} embeddings for source {source_id}")

            except Exception as e:
                bg_db.rollback()
                logger.error(f"Failed to generate embeddings for source {source_id}: {e}")
            finally:
                bg_db.close()

        asyncio.create_task(generate_text_embeddings(source.id, data.content))

    logger.info(f"Added source to project {project_id}: {source.id}")

    return source


@router.post("/projects/{project_id}/sources/upload")
async def upload_source(
    project_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传文件作为源材料"""
    # 验证项目
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 验证文件类型
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    type_map = {
        "pdf": "pdf",
        "mp3": "audio", "wav": "audio", "m4a": "audio",
        "mp4": "video", "webm": "video",
        "txt": "text", "md": "text",
    }

    source_type = type_map.get(ext)
    if not source_type:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # 创建源记录
    source = ResearchSource(
        project_id=project_id,
        source_type=source_type,
        title=filename,
        processing_status="pending",
    )
    db.add(source)
    db.flush()  # 获取 ID

    # 上传到 R2
    path = storage_service.generate_path(
        project_id=str(project_id),
        category="sources",
        filename=filename,
        entity_id=str(source.id),
    )

    content = await file.read()
    result = await storage_service.upload_from_bytes(content, path)

    if not result.get("success"):
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload file")

    # 更新源记录
    source.file_path = path

    # 更新项目统计
    project.source_count += 1

    db.commit()
    db.refresh(source)

    logger.info(f"Uploaded source to project {project_id}: {source.id}")

    return {
        "id": str(source.id),
        "title": source.title,
        "source_type": source.source_type,
        "file_path": source.file_path,
        "processing_status": source.processing_status,
    }


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: UUID,
    db: Session = Depends(get_db),
):
    """删除源材料"""
    source = db.query(ResearchSource).filter(ResearchSource.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # 删除存储文件
    if source.file_path:
        await storage_service.delete_file(source.file_path)

    # 更新项目统计
    project = db.query(ResearchProject).filter(ResearchProject.id == source.project_id).first()
    if project:
        project.source_count = max(0, project.source_count - 1)

    db.delete(source)
    db.commit()

    return {"success": True}


# ============================================================
# 对话 API (SSE 流式)
# ============================================================
@router.post("/projects/{project_id}/chat")
async def chat_stream(
    project_id: UUID,
    request: ChatStreamRequest,
    db: Session = Depends(get_db),
):
    """
    项目内对话 (SSE 流式)

    返回 Server-Sent Events 流:
    - event: text - 增量文本
    - event: done - 完成 (包含 references)
    - event: error - 错误信息
    """
    # 验证项目存在
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 检查 SDK 可用性
    if not research_sdk_service.is_available:
        raise HTTPException(status_code=503, detail="研究服务不可用")

    # 保存用户消息
    user_msg = ChatMessage(project_id=project_id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    async def event_generator():
        full_content = ""
        all_references = []
        saved = False

        try:
            async for event in research_sdk_service.chat_stream(
                project_id=str(project_id),
                message=request.message,
            ):
                if event.event == "text":
                    delta = json.loads(event.data).get("delta", "")
                    full_content += delta
                elif event.event == "done":
                    done_data = json.loads(event.data)
                    all_references = done_data.get("references", [])

                yield event.serialize()
        finally:
            # 无论正常结束还是客户端断开，都保存已生成的内容
            if full_content and not saved:
                saved = True
                save_db = SessionLocal()
                try:
                    ai_msg = ChatMessage(
                        project_id=project_id,
                        role="assistant",
                        content=full_content,
                        references=all_references,
                    )
                    save_db.add(ai_msg)
                    save_db.commit()
                finally:
                    save_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/projects/{project_id}/chat/messages", response_model=List[ChatMessageResponse])
async def list_chat_messages(
    project_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取对话历史消息"""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    # 反转顺序 (从旧到新)
    messages.reverse()

    return messages


@router.post("/projects/{project_id}/messages/{message_id}/star")
async def star_message(
    project_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
):
    """切换消息星标状态"""
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project_id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # 切换星标
    message.starred = not message.starred

    db.commit()
    db.refresh(message)

    return {
        "id": str(message.id),
        "starred": message.starred,
    }


# ============================================================
# 生成 API (SSE 流式)
# ============================================================
@router.post("/projects/{project_id}/generate/report")
async def generate_report_stream(
    project_id: UUID,
    request: GenerateRequest,
    db: Session = Depends(get_db),
):
    """
    生成研究报告 (SSE 流式)

    返回 Server-Sent Events 流:
    - event: progress - 进度更新
    - event: text - 增量文本
    - event: done - 完成
    - event: error - 错误信息
    """
    # 验证项目存在
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 检查 SDK 可用性
    if not research_sdk_service.is_available:
        raise HTTPException(status_code=503, detail="研究服务不可用")

    async def event_generator():
        full_content = ""
        saved = False

        try:
            async for event in research_sdk_service.report_stream(
                project_id=str(project_id),
                topic=request.topic,
            ):
                if event.event == "text":
                    delta = json.loads(event.data).get("delta", "")
                    full_content += delta

                yield event.serialize()
        finally:
            # 无论正常结束还是客户端断开，都保存已生成的报告
            if full_content and not saved:
                saved = True
                save_db = SessionLocal()
                try:
                    output = ResearchOutput(
                        project_id=project_id,
                        output_type="report",
                        title=request.topic or f"研究报告 - {datetime.utcnow().strftime('%Y-%m-%d')}",
                        content=full_content,
                        content_format="markdown",
                    )
                    save_db.add(output)

                    proj = save_db.query(ResearchProject).filter(
                        ResearchProject.id == project_id
                    ).first()
                    if proj:
                        proj.output_count += 1
                        proj.last_researched_at = datetime.utcnow()

                    save_db.commit()
                finally:
                    save_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/projects/{project_id}/generate/mindmap")
async def generate_mindmap_stream(
    project_id: UUID,
    request: GenerateRequest,
    db: Session = Depends(get_db),
):
    """
    生成思维导图 (SSE 流式)

    返回 Server-Sent Events 流:
    - event: progress - 进度更新
    - event: text - 增量文本
    - event: done - 完成
    - event: error - 错误信息
    """
    # 验证项目存在
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 检查 SDK 可用性
    if not research_sdk_service.is_available:
        raise HTTPException(status_code=503, detail="研究服务不可用")

    async def event_generator():
        full_content = ""
        saved = False

        try:
            async for event in research_sdk_service.mindmap_stream(
                project_id=str(project_id),
                topic=request.topic,
            ):
                if event.event == "text":
                    delta = json.loads(event.data).get("delta", "")
                    full_content += delta

                yield event.serialize()
        finally:
            # 无论正常结束还是客户端断开，都保存已生成的思维导图
            if full_content and not saved:
                saved = True
                save_db = SessionLocal()
                try:
                    output = ResearchOutput(
                        project_id=project_id,
                        output_type="mindmap",
                        title=request.topic or f"思维导图 - {datetime.utcnow().strftime('%Y-%m-%d')}",
                        content=full_content,
                        content_format="mermaid",
                    )
                    save_db.add(output)

                    proj = save_db.query(ResearchProject).filter(
                        ResearchProject.id == project_id
                    ).first()
                    if proj:
                        proj.output_count += 1

                    save_db.commit()
                finally:
                    save_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# 输出 API
# ============================================================
@router.get("/projects/{project_id}/outputs")
async def list_outputs(
    project_id: UUID,
    output_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取项目输出列表"""
    query = db.query(ResearchOutput).filter(ResearchOutput.project_id == project_id)

    if output_type:
        query = query.filter(ResearchOutput.output_type == output_type)

    outputs = query.order_by(ResearchOutput.created_at.desc()).all()

    return [
        {
            "id": str(o.id),
            "output_type": o.output_type,
            "title": o.title,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in outputs
    ]


@router.get("/outputs/{output_id}")
async def get_output(
    output_id: UUID,
    db: Session = Depends(get_db),
):
    """获取输出详情"""
    output = db.query(ResearchOutput).filter(ResearchOutput.id == output_id).first()

    if not output:
        raise HTTPException(status_code=404, detail="Output not found")

    return {
        "id": str(output.id),
        "project_id": str(output.project_id),
        "output_type": output.output_type,
        "title": output.title,
        "content": output.content,
        "content_format": output.content_format,
        "created_at": output.created_at.isoformat() if output.created_at else None,
    }


@router.delete("/outputs/{output_id}")
async def delete_output(
    output_id: UUID,
    db: Session = Depends(get_db),
):
    """删除输出"""
    output = db.query(ResearchOutput).filter(ResearchOutput.id == output_id).first()

    if not output:
        raise HTTPException(status_code=404, detail="Output not found")

    # 更新项目统计
    project = db.query(ResearchProject).filter(ResearchProject.id == output.project_id).first()
    if project:
        project.output_count = max(0, project.output_count - 1)

    db.delete(output)
    db.commit()

    return {"success": True}
