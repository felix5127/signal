# backend/app/tasks/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
异步任务系统，流水线编排，定时任务调度，进度追踪。

## 成员清单
pipeline.py: 核心流水线，包含 ArticlePipeline/TwitterPipeline/PodcastPipeline/VideoPipeline
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
| ArticlePipeline | RSS/OPML | 每12小时 | 完整 8 步处理 (Deduper + UnifiedFilter) |
| TwitterPipeline | XGoing | 每小时 | 跳过 LLM 分析，直接存储 |
| PodcastPipeline | Podcast RSS | 每6小时 | 转写 + PodcastAnalyzer 章节/Q&A 分析 + 日期过滤 |
| VideoPipeline | YouTube RSS | 按需 | 转写 + PodcastAnalyzer 章节/Q&A 分析 |

## ArticlePipeline 流程
```
1. RSS 采集 → RawSignal[]
2. 三层去重 (Deduper) → URL精确 + 标题Jaccard + 内容指纹 [追踪: 重复项]
3. 全文提取 (ContentExtractor) → ExtractedContent[]
4. 统一过滤 (UnifiedFilter) → score >= 3 通过 [追踪: 过滤/通过]
5. 深度分析 (Analyzer) → 三步分析
6. 翻译分流 (Translator) → 英文翻译，中文保留
7. Favicon 获取 → source_icon_url
8. 数据库持久化 → Resource 表 (含 llm_* 字段) [追踪: 收录项]
9. 记录采集结果 → SourceService
10. 飞书追踪 (DataTracker) → 批量写入飞书多维表格
```

## 数据追踪 (ArticlePipeline)
通过 DataTracker 在流水线各节点记录数据状态:
- **去重阶段**: 记录被过滤的重复项 (stage=dedup)
- **过滤阶段**: 记录 LLM 评分及拒绝原因 (stage=llm)
- **存储阶段**: 记录最终收录的内容 (stage=save)

追踪数据写入飞书多维表格字段:
| 字段 | 类型 | 说明 |
|------|------|------|
| 标题 | 文本 | 内容标题 (限 100 字符) |
| URL | 链接 | 原始链接 |
| 来源 | 单选 | RSS/Twitter/Podcast/Video |
| 时间 | 日期 | 采集时间 |
| 状态 | 单选 | 收录/过滤 |
| 原因 | 文本 | LLM 评分理由或过滤原因 |
| 阶段 | 单选 | 去重/LLM过滤/存储 |
| 评分 | 数字 | LLM 评分 (0-5) |
| 流水线 | 单选 | 文章/推特/播客/视频 |

## 性能对比
| 流水线版本 | 处理 100 篇耗时 | 吞吐量 | 并发控制 | 错误重试 |
|----------|---------------|--------|---------|---------|
| 原始版 (pipeline.py) | ~30-40 分钟 | 0.04 篇/秒 | 无 | 无 |
| 优化版 (pipeline_v2.py) | ~8-12 分钟 | 0.14 篇/秒 | 有 | 有 |

优化要点: 全文提取并发 (10x) / LLM 调用并发 (5x) / 批量 DB 操作 (50x) / 失败自动重试 (3 次)

## 定时任务配置
| 任务 | 触发时间 | 函数 |
|------|---------|------|
| Article Pipeline | 每12小时 | scheduled_main_pipeline |
| Twitter Pipeline | 每小时 | scheduled_twitter_pipeline |
| Podcast Pipeline | 每6小时 | scheduled_podcast_pipeline |
| Daily Digest | 每天 07:00 | daily_digest_job |
| Weekly Digest | 每周一 08:00 | weekly_digest_job |
| Newsletter | 每周五 17:00 | newsletter_job |

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
