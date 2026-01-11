# Input: 依赖 FastAPI、database.py (get_db)、models/task.py (TaskStatus)
# Output: 任务状态查询 API 端点（列表/详情）
# Position: API 路由层，任务状态对外接口
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import TaskStatus


router = APIRouter()


# ========== 响应模型 ==========


class LogEntry(BaseModel):
    """日志条目"""
    step: str
    time: str

    @field_validator("time", mode="before")
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class TaskResponse(BaseModel):
    """任务状态响应"""
    id: int
    task_id: str
    task_type: str
    status: str  # pending/running/completed/failed/cancelled
    progress: float  # 0-100
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
    logs: Optional[List[LogEntry]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("started_at", "completed_at", "created_at", mode="before")
    @classmethod
    def convert_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int


# ========== API 端点 ==========


@router.get("/tasks", response_model=TaskListResponse)
def get_tasks(
    task_type: Optional[str] = Query(default="deep_research", description="任务类型"),
    status: Optional[str] = Query(default=None, description="状态过滤"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取任务列表

    Args:
        task_type: 任务类型 (deep_research/article_pipeline/twitter_pipeline等)
        status: 状态过滤 (pending/running/completed/failed)
        limit: 返回数量

    Returns:
        任务列表（按创建时间倒序）
    """
    query = db.query(TaskStatus).filter(TaskStatus.task_type == task_type)

    if status:
        query = query.filter(TaskStatus.status == status)

    # 按创建时间倒序
    query = query.order_by(TaskStatus.created_at.desc())

    total = query.count()
    tasks = query.limit(limit).all()

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    获取单个任务详情

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    删除任务

    Args:
        task_id: 任务ID

    Returns:
        删除结果
    """
    task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 如果任务正在运行，先标记为取消
    if task.status == "running":
        task.status = "cancelled"
        task.error = "Task cancelled by user"

    db.delete(task)
    db.commit()

    return {"success": True, "message": "任务已删除"}


@router.post("/tasks/{task_id}/toggle-pause")
def toggle_task_pause(
    task_id: str,
    db: Session = Depends(get_db),
):
    """
    暂停/恢复任务

    Args:
        task_id: 任务ID

    Returns:
        操作结果
    """
    task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "running":
        task.status = "pending"
        return {"success": True, "message": "任务已暂停", "new_status": "pending"}
    elif task.status == "pending":
        task.status = "running"
        task.started_at = datetime.now()
        return {"success": True, "message": "任务已恢复", "new_status": "running"}
    else:
        raise HTTPException(status_code=400, detail="只能暂停或恢复运行中的任务")


@router.post("/tasks/pipeline/trigger")
def trigger_pipeline(
    source: Optional[str] = Query(default=None, description="数据源: hn/twitter/github/huggingface/arxiv/producthunt/blog"),
):
    """
    手动触发数据抓取任务

    Args:
        source: 指定数据源（可选），不指定则运行全部

    Returns:
        触发结果
    """
    from app.main import scheduled_twitter_pipeline, scheduled_main_pipeline, scheduled_pipeline

    try:
        if source == "twitter":
            # 在后台线程运行
            import threading
            thread = threading.Thread(target=scheduled_twitter_pipeline)
            thread.start()
            return {"success": True, "message": "Twitter pipeline 已触发"}
        elif source:
            # 指定单个数据源
            import threading
            thread = threading.Thread(target=scheduled_pipeline, args=([source],))
            thread.start()
            return {"success": True, "message": f"{source} pipeline 已触发"}
        else:
            # 运行主要数据源
            import threading
            thread = threading.Thread(target=scheduled_main_pipeline)
            thread.start()
            return {"success": True, "message": "主数据源 pipeline 已触发（hn/github/huggingface/arxiv/producthunt/blog）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")
