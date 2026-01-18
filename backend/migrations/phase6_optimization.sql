-- Phase 6: 性能优化数据库迁移
-- 优化查询性能的索引和配置

-- ============================================================
-- 研究相关表索引优化
-- ============================================================

-- 研究项目索引
CREATE INDEX IF NOT EXISTS idx_research_projects_user_id ON research_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_research_projects_status ON research_projects(status);
CREATE INDEX IF NOT EXISTS idx_research_projects_created_at ON research_projects(created_at DESC);

-- 研究源材料索引
CREATE INDEX IF NOT EXISTS idx_research_sources_project_id ON research_sources(project_id);
CREATE INDEX IF NOT EXISTS idx_research_sources_source_type ON research_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_research_sources_status ON research_sources(status);
CREATE INDEX IF NOT EXISTS idx_research_sources_created_at ON research_sources(created_at DESC);

-- 源材料分块索引 (向量搜索优化)
CREATE INDEX IF NOT EXISTS idx_research_source_chunks_source_id ON research_source_chunks(source_id);
-- 向量索引 (HNSW) - 如果 pgvector 已安装
-- CREATE INDEX IF NOT EXISTS idx_research_source_chunks_embedding ON research_source_chunks
--     USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 研究任务索引
CREATE INDEX IF NOT EXISTS idx_research_tasks_project_id ON research_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_research_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at ON research_tasks(created_at DESC);

-- 研究输出索引
CREATE INDEX IF NOT EXISTS idx_research_outputs_project_id ON research_outputs(project_id);
CREATE INDEX IF NOT EXISTS idx_research_outputs_task_id ON research_outputs(task_id);
CREATE INDEX IF NOT EXISTS idx_research_outputs_output_type ON research_outputs(output_type);
CREATE INDEX IF NOT EXISTS idx_research_outputs_created_at ON research_outputs(created_at DESC);

-- 对话消息索引
CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id ON chat_messages(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- ============================================================
-- 资源表索引优化
-- ============================================================

-- 资源表复合索引 (常用查询优化)
CREATE INDEX IF NOT EXISTS idx_resources_status_created ON resources(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_resources_type_status ON resources(resource_type, status);
CREATE INDEX IF NOT EXISTS idx_resources_score_status ON resources(llm_score DESC, status);

-- 全文搜索索引 (PostgreSQL Full-Text Search)
-- 创建 tsvector 列 (如果不存在)
ALTER TABLE resources ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 更新 search_vector
UPDATE resources SET search_vector =
    setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(summary, '')), 'B');

-- 创建 GIN 索引
CREATE INDEX IF NOT EXISTS idx_resources_search ON resources USING gin(search_vector);

-- 创建触发器自动更新 search_vector
CREATE OR REPLACE FUNCTION resources_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.summary, '')), 'B');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS resources_search_vector_trigger ON resources;
CREATE TRIGGER resources_search_vector_trigger
    BEFORE INSERT OR UPDATE OF title, summary ON resources
    FOR EACH ROW EXECUTE FUNCTION resources_search_vector_update();

-- ============================================================
-- 数据源表索引优化
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sources_source_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
CREATE INDEX IF NOT EXISTS idx_sources_whitelist ON sources(is_whitelist);

-- ============================================================
-- 任务表索引优化
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- ============================================================
-- 统计信息更新
-- ============================================================

-- 更新表统计信息
ANALYZE research_projects;
ANALYZE research_sources;
ANALYZE research_source_chunks;
ANALYZE research_tasks;
ANALYZE research_outputs;
ANALYZE chat_messages;
ANALYZE resources;
ANALYZE sources;
ANALYZE tasks;

-- ============================================================
-- 查询优化配置 (可选，需要超级用户权限)
-- ============================================================

-- 增加 work_mem 用于复杂查询
-- SET work_mem = '256MB';

-- 增加 effective_cache_size
-- SET effective_cache_size = '4GB';

-- 启用并行查询
-- SET max_parallel_workers_per_gather = 4;

-- ============================================================
-- 完成
-- ============================================================

SELECT 'Phase 6 optimization migration completed' AS status;
