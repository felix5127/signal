-- ============================================================
-- Migration: Research Assistant Infrastructure
-- Version: 002
-- Date: 2026-01-17
-- Description: pgvector 扩展 + 研究助手数据模型
-- ============================================================

-- ============================================================
-- 1. 启用 pgvector 扩展
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 2. 创建 research_projects 表（研究项目）
-- ============================================================
-- 注意: owner_id 暂时可选，Phase 7 用户认证完成后再添加 FK
CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID,  -- 暂无 FK，Phase 7 添加用户表后补充

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',  -- active, archived

    -- 统计
    source_count INTEGER DEFAULT 0,
    output_count INTEGER DEFAULT 0,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_researched_at TIMESTAMPTZ
);

-- research_projects 索引
CREATE INDEX IF NOT EXISTS idx_projects_owner ON research_projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON research_projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON research_projects(created_at DESC);

-- ============================================================
-- 3. 创建 research_sources 表（研究源材料）
-- ============================================================
CREATE TABLE IF NOT EXISTS research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    resource_id INTEGER REFERENCES resources(id),  -- 关联 Signal Hunter 的 Resource

    -- 源信息
    source_type VARCHAR(50) NOT NULL,  -- url, pdf, audio, video, text
    title VARCHAR(500),
    original_url TEXT,
    file_path TEXT,  -- R2 存储路径

    -- 内容
    full_text TEXT,
    summary TEXT,
    extra_metadata JSONB DEFAULT '{}',

    -- 处理状态
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    processing_error TEXT,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- research_sources 索引
CREATE INDEX IF NOT EXISTS idx_sources_project ON research_sources(project_id);
CREATE INDEX IF NOT EXISTS idx_sources_resource ON research_sources(resource_id);
CREATE INDEX IF NOT EXISTS idx_sources_status ON research_sources(processing_status);
CREATE INDEX IF NOT EXISTS idx_sources_type ON research_sources(source_type);

-- ============================================================
-- 4. 创建 source_embeddings 表（向量嵌入）
-- ============================================================
CREATE TABLE IF NOT EXISTS source_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES research_sources(id) ON DELETE CASCADE,

    -- 分块信息
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tokens INTEGER,

    -- 向量嵌入 (百炼 通用文本向量-v3，默认 512 维)
    embedding vector(512) NOT NULL,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 唯一约束：每个 source 的每个 chunk 只有一个嵌入
    UNIQUE(source_id, chunk_index)
);

-- source_embeddings 索引
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON source_embeddings(source_id);

-- HNSW 向量索引（高性能近似最近邻搜索）
-- m=16: 每个节点的连接数
-- ef_construction=64: 构建时的搜索宽度
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON source_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- 5. 创建 research_outputs 表（研究输出）
-- ============================================================
CREATE TABLE IF NOT EXISTS research_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,

    -- 输出信息
    output_type VARCHAR(50) NOT NULL,  -- summary, mindmap, report, podcast, slides
    title VARCHAR(500),
    content TEXT,
    content_format VARCHAR(50) DEFAULT 'markdown',  -- markdown, html, json

    -- 文件（如果有）
    file_path TEXT,  -- R2 存储路径
    file_size INTEGER,
    duration INTEGER,  -- 秒（音频/视频）

    -- 元数据
    extra_metadata JSONB DEFAULT '{}',
    source_refs UUID[],  -- 引用的 research_sources IDs

    -- 统计
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- research_outputs 索引
CREATE INDEX IF NOT EXISTS idx_outputs_project ON research_outputs(project_id);
CREATE INDEX IF NOT EXISTS idx_outputs_type ON research_outputs(output_type);
CREATE INDEX IF NOT EXISTS idx_outputs_created ON research_outputs(created_at DESC);

-- ============================================================
-- 6. 创建 chat_sessions 表（对话会话）
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,

    -- 会话信息
    title VARCHAR(255),
    context_source_ids UUID[] DEFAULT '{}',  -- 对话上下文中的 sources

    -- 消息存储 (JSON 数组)
    -- 格式: [{"role": "user|assistant", "content": "...", "timestamp": "...", "metadata": {...}}]
    messages JSONB DEFAULT '[]',

    -- 统计
    message_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- chat_sessions 索引
CREATE INDEX IF NOT EXISTS idx_chat_project ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_updated ON chat_sessions(updated_at DESC);

-- ============================================================
-- 7. 创建 agent_tasks 表（Agent 任务追踪）
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,

    -- 任务信息
    task_type VARCHAR(50) NOT NULL,  -- research, chat, podcast, mindmap
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled

    -- 输入输出
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',

    -- 进度
    progress FLOAT DEFAULT 0,  -- 0.0 - 1.0
    current_step VARCHAR(255),
    steps_completed INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,

    -- 错误处理
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- 统计
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    duration_seconds INTEGER,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- agent_tasks 索引
CREATE INDEX IF NOT EXISTS idx_tasks_project ON agent_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON agent_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON agent_tasks(created_at DESC);

-- ============================================================
-- 8. 创建触发器：自动更新 updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_research_projects_updated_at
    BEFORE UPDATE ON research_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_outputs_updated_at
    BEFORE UPDATE ON research_outputs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 9. 创建辅助函数：向量相似度搜索
-- ============================================================
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(512),
    project_id_filter UUID DEFAULT NULL,
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    source_id UUID,
    chunk_index INTEGER,
    chunk_text TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        se.source_id,
        se.chunk_index,
        se.chunk_text,
        1 - (se.embedding <=> query_embedding) AS similarity
    FROM source_embeddings se
    JOIN research_sources rs ON se.source_id = rs.id
    WHERE (project_id_filter IS NULL OR rs.project_id = project_id_filter)
      AND 1 - (se.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY se.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 完成
-- ============================================================
-- 执行方式:
-- docker exec -i signal-db psql -U signal_user -d signal_db < migrations/002_research_assistant.sql
