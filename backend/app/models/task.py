# Input: 无
# Output: TaskStatus ORM 模型
# Position: 任务状态持久化层，跟踪异步任务执行状态和进度
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Float, JSON
from sqlalchemy.sql import func

from app.database import Base


class TaskStatus(Base):
    """
    异步任务状态跟踪模型

    字段说明：
    - task_id: 唯一任务ID
    - task_type: 任务类型 (article_pipeline/twitter_pipeline/batch_llm_call)
    - status: 任务状态 (pending/running/completed/failed/cancelled)
    - total_items: 总任务数
    - processed_items: 已处理数
    - failed_items: 失败数
    - progress: 进度百分比 (0-100)
    - result: 任务结果 (JSON 格式)
    - error: 错误信息
    - started_at: 开始时间
    - completed_at: 完成时间
    - metadata: 扩展元数据 (JSON)
    """

    __tablename__ = "task_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)

    # 任务信息
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)
    progress = Column(Float, default=0.0)  # 0-100

    # 统计信息
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # 结果与错误
    result = Column(JSON)  # 任务执行结果
    error = Column(Text)  # 错误信息
    logs = Column(JSON)  # 执行日志（可选）

    # 时间戳
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 元数据（meta 避免 SQLAlchemy 保留字冲突）
    meta = Column("metadata", JSON)  # 扩展信息（如配置参数等）

    def __repr__(self):
        return f"<TaskStatus(task_id={self.task_id}, type={self.task_type}, status={self.status}, progress={self.progress}%)>"
