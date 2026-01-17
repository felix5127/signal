-- ============================================================
-- Migration: Data Pipeline Refactor
-- Version: 001
-- Date: 2026-01-17
-- Description: 添加 LLM 过滤、人工审核、数据源管理、Prompt 版本管理
-- ============================================================

-- ============================================================
-- 1. 创建 sources 表（数据源管理）
-- ============================================================
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    is_whitelist BOOLEAN DEFAULT FALSE,
    total_collected INTEGER DEFAULT 0,
    total_approved INTEGER DEFAULT 0,
    total_rejected INTEGER DEFAULT 0,
    total_published INTEGER DEFAULT 0,
    total_review_overturned INTEGER DEFAULT 0,
    avg_llm_score FLOAT DEFAULT 0.0,
    last_collected_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- sources 表索引
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(type);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
CREATE INDEX IF NOT EXISTS idx_sources_whitelist ON sources(is_whitelist);
CREATE INDEX IF NOT EXISTS idx_sources_type_enabled ON sources(type, enabled);

-- ============================================================
-- 2. 创建 prompts 表（Prompt 版本管理）
-- ============================================================
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    total_used INTEGER DEFAULT 0,
    avg_score FLOAT,
    approval_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    activated_at TIMESTAMP,
    UNIQUE(type, version)
);

-- prompts 表索引
CREATE INDEX IF NOT EXISTS idx_prompts_type ON prompts(type);
CREATE INDEX IF NOT EXISTS idx_prompts_status ON prompts(status);
CREATE INDEX IF NOT EXISTS idx_prompts_type_status ON prompts(type, status);

-- ============================================================
-- 3. 创建 reviews 表（人工审核记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    comment TEXT,
    reviewer VARCHAR(100) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- reviews 表索引
CREATE INDEX IF NOT EXISTS idx_reviews_resource_id ON reviews(resource_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at);

-- ============================================================
-- 4. 扩展 resources 表（添加 LLM 过滤和审核字段）
-- ============================================================

-- LLM 过滤结果字段
ALTER TABLE resources ADD COLUMN IF NOT EXISTS llm_score INTEGER;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS llm_reason TEXT;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS llm_prompt_version INTEGER;

-- 人工审核字段
ALTER TABLE resources ADD COLUMN IF NOT EXISTS review_status VARCHAR(20);
ALTER TABLE resources ADD COLUMN IF NOT EXISTS review_comment TEXT;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);

-- 来源关联字段
ALTER TABLE resources ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sources(id);

-- resources 新索引
CREATE INDEX IF NOT EXISTS idx_resources_llm_score ON resources(llm_score);
CREATE INDEX IF NOT EXISTS idx_resources_source_id ON resources(source_id);
CREATE INDEX IF NOT EXISTS idx_resources_review_status ON resources(review_status);

-- ============================================================
-- 5. 数据迁移：现有数据标记为 published
-- ============================================================

-- 所有现有 Resource 标记为 published（如果 status 还是 pending/analyzing）
UPDATE resources
SET status = 'published'
WHERE status IN ('pending', 'analyzing')
  OR status IS NULL;

-- ============================================================
-- 6. 插入默认 Prompt（内容过滤 v1）
-- ============================================================
INSERT INTO prompts (name, version, type, system_prompt, user_prompt_template, status, created_at, activated_at)
VALUES (
    '内容过滤 Prompt v1',
    1,
    'filter',
    '你是一个 AI 技术内容筛选专家，为 AI 技术情报平台筛选内容。

## 评分标准（0-5 分）

**5 分 - 极高价值**
- 头部公司重磅产品发布（OpenAI/Anthropic/Google 新产品）
- 改变开发者工作方式的工具（如 Cursor, Claude Code 级别）
- 深度技术分析 + 完整代码实现
- 权威人士的深度洞察

**4 分 - 高价值**
- 有独特见解的技术分析
- 实用的 AI 开发教程（有代码）
- AI 领域重要动态和趋势分析
- 知名博主的深度文章

**3 分 - 有价值**
- AI 相关的技术讨论，有一定深度
- 普通的 AI 工具/产品介绍
- AI 领域的新闻报道（有实质内容）

**2 分 - 价值较低**
- 内容较浅的 AI 相关文章
- 转载/二手信息
- 过于基础的入门内容

**1 分 - 价值很低**
- 与 AI 关联很弱
- 纯营销/广告内容
- 标题党，内容空洞

**0 分 - 无价值**
- 完全不相关
- 垃圾内容
- 非中英文

## 判断重点

1. **深度优先**：深度分析 > 新闻通稿
2. **头部优先**：OpenAI/Anthropic/Google 等头部公司动态优先
3. **实用优先**：有代码/工具/Demo 的内容优先
4. **原创优先**：原创分析 > 转载搬运

## 输出格式

严格返回 JSON：
{
  "score": 4,
  "reason": "深度分析 Claude Code 架构，有代码实现"
}

reason 限制在 50 字以内，说明评分理由。',
    '请评估以下内容：

标题：{title}
来源：{source_name}
URL：{url}

内容摘要：
{content}

---
请给出 0-5 分评分和理由。',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (type, version) DO NOTHING;

-- ============================================================
-- 完成
-- ============================================================
-- 执行完成后验证：
-- SELECT COUNT(*) FROM sources;
-- SELECT COUNT(*) FROM prompts;
-- SELECT COUNT(*) FROM reviews;
-- SELECT COUNT(*) FROM resources WHERE llm_score IS NOT NULL;
