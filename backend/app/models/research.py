"""
[INPUT]: 依赖 database.py (Base), sqlalchemy, pgvector.sqlalchemy (Vector)
[OUTPUT]: 对外提供研究助手 ORM 模型: ResearchProject, ResearchSource, SourceEmbedding,
         ResearchOutput, ChatSession, AgentTask
[POS]: models/ 的研究助手数据模型，被 api/research, services/research 消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    ARRAY,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# pgvector 支持
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback: 开发环境可能没有 pgvector
    Vector = None
    PGVECTOR_AVAILABLE = False


# ============================================================
# ResearchProject - 研究项目
# ============================================================
class ResearchProject(Base):
    """
    研究项目表 - 用户创建的研究课题

    状态流转:
    - active: 活跃项目
    - archived: 已归档
    """

    __tablename__ = "research_projects"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 所有者 (Phase 7 添加 FK) ==========
    owner_id = Column(UUID(as_uuid=True), nullable=True)  # 暂无 FK

    # ========== 基本信息 ==========
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")  # active, archived

    # ========== 统计 ==========
    source_count = Column(Integer, default=0)
    output_count = Column(Integer, default=0)

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_researched_at = Column(DateTime(timezone=True))

    # ========== 关系 ==========
    sources = relationship("ResearchSource", back_populates="project", cascade="all, delete-orphan")
    outputs = relationship("ResearchOutput", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("AgentTask", back_populates="project", cascade="all, delete-orphan")

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_projects_owner", "owner_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_created", "created_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<ResearchProject(id={self.id}, name={self.name})>"


# ============================================================
# ResearchSource - 研究源材料
# ============================================================
class ResearchSource(Base):
    """
    研究源材料表 - 项目中的输入材料

    source_type:
    - url: 网页链接
    - pdf: PDF 文档
    - audio: 音频文件
    - video: 视频文件
    - text: 纯文本

    processing_status:
    - pending: 待处理
    - processing: 处理中
    - completed: 已完成
    - failed: 处理失败
    """

    __tablename__ = "research_sources"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 外键 ==========
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)  # 关联 Signal

    # ========== 源信息 ==========
    source_type = Column(String(50), nullable=False)  # url, pdf, audio, video, text
    title = Column(String(500))
    original_url = Column(Text)
    file_path = Column(Text)  # R2 存储路径

    # ========== 内容 ==========
    full_text = Column(Text)
    summary = Column(Text)
    extra_metadata = Column(JSONB, default=dict)  # 避免与 SQLAlchemy 保留字冲突

    # ========== 处理状态 ==========
    processing_status = Column(String(50), default="pending")
    processing_error = Column(Text)

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # ========== 关系 ==========
    project = relationship("ResearchProject", back_populates="sources")
    embeddings = relationship("SourceEmbedding", back_populates="source", cascade="all, delete-orphan")

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_rsrc_project", "project_id"),
        Index("idx_rsrc_resource", "resource_id"),
        Index("idx_rsrc_status", "processing_status"),
        Index("idx_rsrc_type", "source_type"),
    )

    def __repr__(self):
        return f"<ResearchSource(id={self.id}, type={self.source_type}, title={self.title})>"


# ============================================================
# SourceEmbedding - 向量嵌入
# ============================================================
class SourceEmbedding(Base):
    """
    向量嵌入表 - 存储文本分块的向量表示

    使用百炼 通用文本向量-v3，默认 512 维
    HNSW 索引用于高效相似度搜索
    """

    __tablename__ = "source_embeddings"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 外键 ==========
    source_id = Column(UUID(as_uuid=True), ForeignKey("research_sources.id", ondelete="CASCADE"), nullable=False)

    # ========== 分块信息 ==========
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_tokens = Column(Integer)

    # ========== 向量嵌入 ==========
    # 使用 pgvector 的 Vector 类型，512 维 (百炼默认)
    # 注意: 在 SQLite 环境下此字段不可用
    if PGVECTOR_AVAILABLE:
        embedding = Column(Vector(512), nullable=False)
    else:
        embedding = Column(Text)  # Fallback for development

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ========== 关系 ==========
    source = relationship("ResearchSource", back_populates="embeddings")

    # ========== 索引与约束 ==========
    __table_args__ = (
        Index("idx_embeddings_source", "source_id"),
        # HNSW 向量索引在 SQL 迁移中创建
        # 唯一约束
        Index("idx_embeddings_source_chunk", "source_id", "chunk_index", unique=True),
    )

    def __repr__(self):
        return f"<SourceEmbedding(id={self.id}, source_id={self.source_id}, chunk={self.chunk_index})>"


# ============================================================
# ResearchOutput - 研究输出
# ============================================================
class ResearchOutput(Base):
    """
    研究输出表 - 项目生成的各类产出

    output_type:
    - summary: 研究摘要
    - mindmap: 概念图
    - report: 详细报告
    - podcast: 播客音频
    - slides: PPT

    content_format:
    - markdown: Markdown 格式
    - html: HTML 格式
    - json: JSON 结构
    """

    __tablename__ = "research_outputs"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 外键 ==========
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)

    # ========== 输出信息 ==========
    output_type = Column(String(50), nullable=False)  # summary, mindmap, report, podcast, slides
    title = Column(String(500))
    content = Column(Text)
    content_format = Column(String(50), default="markdown")

    # ========== 文件 ==========
    file_path = Column(Text)  # R2 存储路径
    file_size = Column(Integer)
    duration = Column(Integer)  # 秒 (音频/视频)

    # ========== 元数据 ==========
    extra_metadata = Column(JSONB, default=dict)  # 避免与 SQLAlchemy 保留字冲突
    source_refs = Column(ARRAY(UUID(as_uuid=True)), default=list)  # 引用的 sources

    # ========== 统计 ==========
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ========== 关系 ==========
    project = relationship("ResearchProject", back_populates="outputs")

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_outputs_project", "project_id"),
        Index("idx_outputs_type", "output_type"),
        Index("idx_outputs_created", "created_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<ResearchOutput(id={self.id}, type={self.output_type}, title={self.title})>"


# ============================================================
# ChatSession - 对话会话
# ============================================================
class ChatSession(Base):
    """
    对话会话表 - 与研究材料的对话历史

    messages 格式:
    [
        {
            "role": "user" | "assistant",
            "content": "消息内容",
            "timestamp": "ISO8601",
            "metadata": {...}
        },
        ...
    ]
    """

    __tablename__ = "chat_sessions"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 外键 ==========
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)

    # ========== 会话信息 ==========
    title = Column(String(255))
    context_source_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # ========== 消息 ==========
    messages = Column(JSONB, default=list)

    # ========== 统计 ==========
    message_count = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ========== 关系 ==========
    project = relationship("ResearchProject", back_populates="chat_sessions")

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_chat_project", "project_id"),
        Index("idx_chat_updated", "updated_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"


# ============================================================
# AgentTask - Agent 任务追踪
# ============================================================
class AgentTask(Base):
    """
    Agent 任务表 - 追踪异步任务执行状态

    task_type:
    - research: 研究任务
    - chat: 对话任务
    - podcast: 播客生成
    - mindmap: 概念图生成

    status:
    - pending: 等待执行
    - running: 执行中
    - completed: 已完成
    - failed: 执行失败
    - cancelled: 已取消
    """

    __tablename__ = "agent_tasks"

    # ========== 主键 ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ========== 外键 ==========
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)

    # ========== 任务信息 ==========
    task_type = Column(String(50), nullable=False)  # research, chat, podcast, mindmap
    status = Column(String(50), default="pending")

    # ========== 输入输出 ==========
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)

    # ========== 进度 ==========
    progress = Column(Float, default=0)  # 0.0 - 1.0
    current_step = Column(String(255))
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)

    # ========== 错误处理 ==========
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # ========== 统计 ==========
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    duration_seconds = Column(Integer)

    # ========== 时间 ==========
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # ========== 关系 ==========
    project = relationship("ResearchProject", back_populates="tasks")

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_type", "task_type"),
        Index("idx_tasks_created", "created_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<AgentTask(id={self.id}, type={self.task_type}, status={self.status})>"
