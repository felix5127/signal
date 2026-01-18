# backend/app/models/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
SQLAlchemy ORM 数据模型定义，包含字段验证、索引优化、关系映射。

## 成员清单
resource.py: v2 核心数据模型，支持 4 类内容 (article/podcast/tweet/video)，40+ 字段，含 LLM 过滤 + 人工审核
signal.py: v1 Legacy 数据模型，25+ 字段，逐步迁移至 Resource
newsletter.py: 周刊记录，year+week 唯一索引
digest.py: 日周精选汇总 (DailyDigest, WeeklyDigest)
task.py: 异步任务状态追踪 (TaskStatus)
source.py: 数据源元信息管理，URL/白名单/采集统计，区别于 source_config 的运行时配置
source_run.py: 采集运行记录，记录每次信号源采集的漏斗数据
source_config.py: 信号源动态配置，运行时覆盖 config.yaml
review.py: 人工审核记录，记录 approve/reject/restore 操作
prompt.py: Prompt 版本管理，支持 A/B 测试，(type, version) 唯一约束
research.py: v3 研究助手模型，ResearchProject/ResearchSource/SourceEmbedding/ResearchOutput/ChatSession/AgentTask

## 模型关系
```
Resource (v2 核心)
  ├── 基础信息: title, url, url_hash, source_name, source_icon_url
  ├── 分类信息: type (article/podcast/tweet/video), domain, subdomain, tags
  ├── LLM 分析: one_sentence_summary, summary, main_points, key_quotes, score
  ├── 多语言: title_translated, summary_zh, main_points_zh
  ├── 深度研究: deep_research, deep_research_tokens, deep_research_cost, deep_research_strategy
  ├── LLM 过滤: llm_score (0-5), llm_reason, llm_prompt_version
  ├── 人工审核: review_status (approved/rejected), review_comment, reviewed_at, reviewed_by
  ├── 来源关联: source_id → Source
  ├── 状态流转: pending → approved/rejected → published/archived
  └── 元数据: published_at, created_at, is_featured, language

Signal (v1 Legacy) → 逐步迁移到 Resource

Newsletter
  ├── 周标识: year, week_number (唯一索引)
  └── 内容: title, content_html, content_markdown

TaskStatus
  ├── 任务标识: task_id, task_type
  ├── 状态: status (pending/running/completed/failed), progress
  └── 结果: result, error, logs

SourceRun (采集记录)
  ├── 基础: source_type, started_at, finished_at, status
  ├── 漏斗: fetched_count → rule_filtered → dedup_filtered → llm_filtered → saved
  └── 错误: error_message, error_details

SourceConfig (动态配置)
  ├── 标识: source_type (PK)
  ├── 状态: enabled
  └── 覆盖: config_override (JSON)

Source (数据源管理)
  ├── 基础: name, type (blog/twitter/podcast/video), url (唯一)
  ├── 配置: enabled, is_whitelist
  ├── 统计: total_collected/approved/rejected/published, avg_llm_score
  └── 状态: last_collected_at, last_error

Review (人工审核)
  ├── 关联: resource_id → Resource
  ├── 操作: action (approve/reject/restore), old_status, new_status
  └── 元数据: comment, reviewer, created_at

Prompt (Prompt 版本管理)
  ├── 版本: name, version, type (filter/analyzer/translator)
  ├── 内容: system_prompt, user_prompt_template
  ├── 状态: status (draft/active/archived)
  ├── 统计: total_used, avg_score, approval_rate
  └── 时间: created_at, activated_at

ResearchProject (v3 研究项目)
  ├── 基础: name, description, status (active/archived)
  ├── 统计: source_count, output_count
  ├── 关系: → ResearchSource[], ResearchOutput[], ChatSession[], AgentTask[]
  └── 时间: created_at, updated_at, last_researched_at

ResearchSource (研究源材料)
  ├── 关联: project_id → ResearchProject, resource_id → Resource (可选)
  ├── 源信息: source_type (url/pdf/audio/video/text), title, original_url, file_path
  ├── 内容: full_text, summary, metadata (JSONB)
  ├── 状态: processing_status (pending/processing/completed/failed)
  └── 关系: → SourceEmbedding[]

SourceEmbedding (向量嵌入)
  ├── 关联: source_id → ResearchSource
  ├── 分块: chunk_index, chunk_text, chunk_tokens
  ├── 向量: embedding (vector(512), 百炼 通用文本向量-v3)
  └── 索引: HNSW (m=16, ef_construction=64)

ResearchOutput (研究输出)
  ├── 关联: project_id → ResearchProject
  ├── 输出: output_type (summary/mindmap/report/podcast/slides), title, content
  ├── 文件: file_path, file_size, duration
  └── 统计: tokens_used, cost_usd, source_refs[]

ChatSession (对话会话)
  ├── 关联: project_id → ResearchProject
  ├── 会话: title, context_source_ids[], messages (JSONB)
  └── 统计: message_count, tokens_used

AgentTask (Agent 任务)
  ├── 关联: project_id → ResearchProject
  ├── 任务: task_type (research/chat/podcast/mindmap), status
  ├── 进度: progress, current_step, steps_completed/total_steps
  └── 统计: tokens_used, cost_usd, duration_seconds
```

## 索引优化
- Resource: url_hash (唯一), published_at (降序), score (降序), type, llm_score, source_id
- Newsletter: (year, week_number) 复合唯一
- TaskStatus: task_id (唯一)
- Source: url (唯一), type (索引), enabled (索引), is_whitelist (索引), (type, enabled) 复合索引
- SourceRun: (source_type, started_at) 复合索引
- Review: resource_id (索引)
- Prompt: type (索引), status (索引), (type, version) 复合唯一
- ResearchProject: owner_id, status, created_at (降序)
- ResearchSource: project_id, resource_id, processing_status, source_type
- SourceEmbedding: source_id, (source_id, chunk_index) 唯一, embedding (HNSW vector_cosine_ops)
- ResearchOutput: project_id, output_type, created_at (降序)
- ChatSession: project_id, updated_at (降序)
- AgentTask: project_id, status, task_type, created_at (降序)

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
