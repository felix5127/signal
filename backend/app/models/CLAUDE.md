# backend/app/models/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
SQLAlchemy ORM 数据模型定义，包含字段验证、索引优化、关系映射。

## 成员清单
resource.py: v2 核心数据模型，支持 4 类内容 (article/podcast/tweet/video)，30+ 字段
signal.py: v1 Legacy 数据模型，25+ 字段，逐步迁移至 Resource
newsletter.py: 周刊记录，year+week 唯一索引
digest.py: 日周精选汇总 (DailyDigest, WeeklyDigest)
task.py: 异步任务状态追踪 (TaskStatus)
source_run.py: 采集运行记录，记录每次信号源采集的漏斗数据
source_config.py: 信号源动态配置，运行时覆盖 config.yaml

## 模型关系
```
Resource (v2 核心)
  ├── 基础信息: title, url, url_hash, source, source_icon_url
  ├── 分类信息: resource_type (article/podcast/tweet/video), category, tags
  ├── LLM 分析: one_sentence_summary, summary, main_points, key_quotes, score
  ├── 多语言: title_translated, summary_zh, main_points_zh
  ├── 深度研究: deep_research, deep_research_tokens, deep_research_cost, deep_research_strategy
  └── 元数据: published_at, scraped_at, is_featured, language

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
```

## 索引优化
- Resource: url_hash (唯一), published_at (降序), score (降序), resource_type
- Newsletter: (year, week_number) 复合唯一
- TaskStatus: task_id (唯一)
- SourceRun: (source_type, started_at) 复合索引

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
