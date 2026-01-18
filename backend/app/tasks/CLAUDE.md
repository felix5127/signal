# backend/app/tasks/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
异步任务系统，流水线编排，定时任务调度，进度追踪。

## 成员清单
pipeline.py: 核心流水线，包含 ArticlePipeline/FullPipeline/TwitterPipeline/PodcastPipeline/VideoPipeline
base_pipeline.py: 流水线公共基类 ✅
  - PipelineStats: 统一统计类 (采集/去重/过滤/分析/翻译/转写/保存/Token)
  - BasePipeline: 基础流水线类 (去重检查/数据库会话/进度打印/运行记录)
  - StepBasedPipeline: 结构化流水线 (scrape -> dedupe -> filter -> process -> save)
pipeline_v2.py: v2 流水线入口 (预留)
newsletter.py: 周刊自动生成任务 (每周五 17:00)
digest.py: 日周精选汇总生成任务
queue.py: 任务队列管理 (APScheduler 配置)

## 流水线概览
| 流水线 | 数据源 | 采集频率 | 特点 |
|--------|--------|---------|------|
| ArticlePipeline | RSS/OPML | 按需 | 完整 8 步处理 (Deduper + UnifiedFilter) |
| FullPipeline | HN/GitHub/arXiv/HF/PH | 每12小时 | 多源混合 |
| TwitterPipeline | XGoing | 每小时 | 跳过 LLM 分析，直接存储 |
| PodcastPipeline | Podcast RSS | 按需 | 支持转写，成本高 |
| VideoPipeline | YouTube RSS | 按需 | 支持转写，成本高 |

## ArticlePipeline 流程
```
1. RSS 采集 → RawSignal[]
2. 三层去重 (Deduper) → URL精确 + 标题Jaccard + 内容指纹
3. 全文提取 (ContentExtractor) → ExtractedContent[]
4. 统一过滤 (UnifiedFilter) → score >= 3 通过 + llm_score/llm_reason/llm_prompt_version
5. 深度分析 (Analyzer) → 三步分析
6. 翻译分流 (Translator) → 英文翻译，中文保留
7. Favicon 获取 → source_icon_url
8. 数据库持久化 → Resource 表 (含 llm_* 字段)
```

## 定时任务配置
| 任务 | 触发时间 | 函数 |
|------|---------|------|
| Twitter Pipeline | 每小时 | scheduled_twitter_pipeline |
| Main Pipeline | 每12小时 | scheduled_main_pipeline |
| Daily Digest | 每天 07:00 | daily_digest_job |
| Weekly Digest | 每周一 08:00 | weekly_digest_job |
| Newsletter | 每周五 17:00 | newsletter_job |

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
