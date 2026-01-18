"""
[INPUT]: 依赖 agents/research, models/research, services/storage, database
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

from app.database import get_db
from app.models.research import (
    ResearchProject,
    ResearchSource,
    ResearchOutput,
    ChatSession,
    AgentTask,
)
from app.agents.research.agent import ResearchAgent, ChatAgent
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


class ResearchRequest(BaseModel):
    """研究请求"""
    query: str = Field(..., min_length=1, max_length=2000)
    include_web_search: bool = True
    max_iterations: int = Field(default=5, ge=1, le=10)


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: UUID
    message: str
    response: str


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
        # TODO: 触发异步任务生成嵌入
        pass

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
# 研究 API
# ============================================================
@router.post("/projects/{project_id}/research")
async def start_research(
    project_id: UUID,
    data: ResearchRequest,
    db: Session = Depends(get_db),
):
    """
    发起研究任务 (SSE 流式响应)

    返回 Server-Sent Events 流:
    - event: progress - 进度更新
    - event: result - 最终结果
    - event: error - 错误信息
    """
    # 验证项目
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取项目材料作为上下文
    sources = db.query(ResearchSource).filter(
        ResearchSource.project_id == project_id,
        ResearchSource.processing_status == "completed",
    ).limit(10).all()

    context_parts = []
    for source in sources:
        if source.summary:
            context_parts.append(f"## {source.title}\n{source.summary}")

    context = "\n\n".join(context_parts) if context_parts else None

    # 创建任务记录
    task = AgentTask(
        project_id=project_id,
        task_type="research",
        status="running",
        input_data={"query": data.query},
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    async def generate_stream():
        agent = ResearchAgent()
        try:
            async for progress in agent.research_stream(
                project_id=project_id,
                query=data.query,
                context=context,
                max_iterations=data.max_iterations,
            ):
                # 发送进度
                event_data = {
                    "phase": progress.phase,
                    "message": progress.message,
                    "progress": progress.progress,
                }
                yield f"event: progress\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 如果完成，发送结果
                if progress.data and "output" in progress.data:
                    result_data = {
                        "success": True,
                        "output": progress.data["output"],
                    }
                    yield f"event: result\ndata: {json.dumps(result_data, ensure_ascii=False)}\n\n"

                    # 保存输出
                    output = ResearchOutput(
                        project_id=project_id,
                        output_type="report",
                        title=f"研究报告: {data.query[:50]}",
                        content=progress.data["output"],
                    )
                    db.add(output)

                    # 更新任务
                    task.status = "completed"
                    task.output_data = {"output_id": str(output.id)}

                    # 更新项目
                    project.output_count += 1
                    project.last_researched_at = datetime.utcnow()

                    db.commit()

        except Exception as e:
            logger.error(f"Research stream error: {e}")
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

            task.status = "failed"
            task.error_message = str(e)
            db.commit()

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# 对话 API
# ============================================================
@router.post("/projects/{project_id}/chat", response_model=ChatResponse)
async def chat(
    project_id: UUID,
    data: ChatRequest,
    db: Session = Depends(get_db),
):
    """项目内对话"""
    from app.agents.llm.kimi_client import Message

    # 验证项目
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取或创建会话
    if data.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == data.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(
            project_id=project_id,
            title=data.message[:50],
        )
        db.add(session)
        db.flush()

    # 构建历史消息
    history = []
    if session.messages:
        for msg in session.messages:
            history.append(Message(role=msg["role"], content=msg["content"]))

    # 调用 Agent
    agent = ChatAgent()
    result = await agent.chat(
        project_id=project_id,
        message=data.message,
        history=history if history else None,
    )

    # 更新会话
    messages = session.messages or []
    messages.append({"role": "user", "content": data.message, "timestamp": datetime.utcnow().isoformat()})
    messages.append({"role": "assistant", "content": result.content, "timestamp": datetime.utcnow().isoformat()})
    session.messages = messages
    session.message_count = len(messages)
    session.tokens_used += result.usage.get("total_tokens", 0)

    db.commit()
    db.refresh(session)

    return ChatResponse(
        session_id=session.id,
        message=data.message,
        response=result.content,
    )


@router.get("/projects/{project_id}/chat/sessions")
async def list_chat_sessions(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """获取对话会话列表"""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.project_id == project_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "message_count": s.message_count,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


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
