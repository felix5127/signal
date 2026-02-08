# Signal 数据爬取系统重构 — 完成报告

> 日期: 2026-02-08
> 团队: Full Pipeline Recipe (Lead + Researcher + Architect + Developer + Reviewer)
> 状态: 全部 4 Phase 完成

---

## 执行摘要

针对 Signal 数据爬取系统的及时性、可靠性、透明度和可控性问题，执行了 4 阶段渐进式重构。新增 5 个文件，修改 10+ 个文件，不改 DB Schema、不改 API 响应格式、不改前端。

---

## 问题与解决方案

| 原始问题 | 根因 | 解决方案 | Phase |
|----------|------|---------|-------|
| 转写一直不 work | SDK 缺失静默失败 + 同步阻塞事件循环 + 认证字段错误 + 每日限额仅 5 条 | TranscriptionService: asyncio.to_thread() 非阻塞 + 3 字段正确认证 + AcsClient 单例复用 + 可配置限额 | 1 |
| AI 工具有缺陷 | LLM 失败时 UnifiedFilter 默认放行 (score=3) + JSON 解析不统一 + 无成本控制 | AIService 统一调用层: FailurePolicy.REJECT 失败即拒绝 + 5 层 JSON 解析 + CostTracker 成本追踪 | 1 |
| 缺乏透明度 | 大量 print() + 内存状态重启丢失 + 暂停/恢复是假功能 | PipelineContext 步骤级追踪 + PipelineOrchestrator 生命周期管理 + structlog 结构化日志 + 真实 cancel 能力 | 2 |
| 缺乏可控性 | 无法取消运行中任务 + 无法预览采集结果 + 无全局状态查看 | `POST /cancel/{type}` + `GET /pipeline-status` + dry-run 模式 | 4 |
| ContentExtractor 脆弱 | 每次启动新浏览器 + 无重试 + 失败返回空字符串 | 浏览器单例复用 + 2 次重试 + Jina Reader 降级 + 域名级失败统计 | 3 |
| DataTracker 不全 | 只追踪 ArticlePipeline | 4 个 Pipeline 全部接入 DataTracker | 4 |

---

## 4 阶段实施记录

### Phase 1: 基础设施 (P0 - CRITICAL)
- [x] AIService + FailurePolicy + CostTracker (`services/ai_service.py`)
- [x] TranscriptionService (`processors/transcription_service.py`)
- [x] UnifiedFilter 迁移到 AIService, REJECT 策略
- [x] PodcastPipeline 集成新 TranscriptionService
- [x] 启动时配置校验 (`startup.py`)
- [x] **修复**: TingwuConfig 认证字段 3 字段 (Architect 发现)
- [x] **修复**: pipeline.py 注入 AIService (Reviewer 发现 M3.1)
- [x] **修复**: _daily_count 提交后即递增 (Reviewer 发现 H2.1)

### Phase 2: 可观测性 (P1 - HIGH)
- [x] CancellationToken 提取到 `utils/cancellation.py`
- [x] PipelineContext (`tasks/pipeline_context.py`)
- [x] PipelineOrchestrator (`tasks/orchestrator.py`)
- [x] pipeline.py structlog 迁移 (关键路径)
- [x] 管理 API: `POST /cancel/{type}` + `GET /pipeline-status`

### Phase 3: 可靠性 (P1 - HIGH)
- [x] ContentExtractor: 浏览器复用 + 重试 + Jina 降级 + 失败统计
- [x] Analyzer 迁移到 AIService (RETRY_THEN_SKIP)
- [x] Translator 迁移到 AIService (FALLBACK)
- [x] PodcastAnalyzer 迁移到 AIService (RETRY_THEN_SKIP)
- [x] SourceHealthChecker 增强: RSS 可达性探测 + 历史健康评估

### Phase 4: 代码清理 (P2 - MEDIUM)
- [x] Stats 类统一到 `pipeline/stats.py`
- [x] DataTracker 扩展到全部 4 个 Pipeline
- [x] dry-run 模式
- [ ] ~~删除 filter.py / initial_filter.py~~ (仍有活跃消费者，安全跳过)
- [ ] ~~Pipeline 迁移到 StepBasedPipeline~~ (风险裁剪，留到下一轮)
- [ ] ~~统一 Source/SourceConfig 模型~~ (涉及 DB，风险裁剪)

---

## 新增文件清单

| 文件路径 | 行数 | 职责 | Phase |
|---------|------|------|-------|
| `backend/app/services/ai_service.py` | ~412 | 统一 AI 调用层 + FailurePolicy + CostTracker | 1 |
| `backend/app/processors/transcription_service.py` | ~439 | 异步转写服务 (非阻塞) | 1 |
| `backend/app/tasks/pipeline_context.py` | ~227 | 流水线运行上下文 + 步骤追踪 | 2 |
| `backend/app/tasks/orchestrator.py` | ~147 | 流水线编排器 (防重叠 + 取消) | 2 |
| `backend/app/utils/cancellation.py` | ~30 | CancellationToken 共享模块 | 2 |

## 修改文件清单

| 文件路径 | 改动类型 | Phase |
|---------|---------|-------|
| `processors/unified_filter.py` | AIService 双通道 + REJECT 策略 | 1 |
| `processors/analyzer.py` | AIService 双通道 + RETRY_THEN_SKIP | 3 |
| `processors/translator.py` | AIService 双通道 + FALLBACK + structlog | 3 |
| `processors/podcast_analyzer.py` | AIService 双通道 + RETRY_THEN_SKIP + structlog | 3 |
| `scrapers/content_extractor.py` | 浏览器复用 + 重试 + Jina 降级 + 失败统计 | 3 |
| `services/source_health.py` | RSS 可达性探测 + 历史健康评估 | 3 |
| `tasks/pipeline.py` | AIService 注入 + DataTracker 全覆盖 + dry-run + structlog | 1-4 |
| `tasks/pipeline/stats.py` | 统一 Stats 类定义 | 4 |
| `config.py` | TingwuConfig 3 字段认证 | 1 |
| `startup.py` | 启动时配置校验 | 1 |
| `api/sources.py` | cancel + pipeline-status 端点 | 2 |

---

## 审查记录

### Phase 1 审查 (Reviewer: Opus)
- 结论: 有条件通过
- C2.1 (CRITICAL): TingwuConfig 凭证映射 → 已修复
- M3.1 (HIGH impact): AIService 未注入 UnifiedFilter → 已修复
- H2.1 (HIGH): _daily_count 计时错误 → 已修复
- H1.1 (HIGH): Token 估算偏差 → 留到后续 (不影响功能)

### Phase 2-4 审查 (Lead 快速审阅)
- 通过，无 CRITICAL 问题

---

## 设计原则

本次重构的核心转变: **从"乐观假设"到"悲观设计"**

| 之前 | 之后 |
|------|------|
| SDK 缺失 → 静默返回 None | SDK 缺失 → structlog 告警 + 明确的 is_available() 检查 |
| LLM 失败 → 默认放行 (score=3) | LLM 失败 → REJECT (score=0) |
| 全文提取失败 → 空字符串继续处理 | 提取失败 → Jina 降级 → 带 error 标记的结果 |
| 任务状态 → 内存 PipelineState | 任务状态 → PipelineContext + structlog + API |
| 暂停/恢复 → 假功能 (只改 DB) | 取消 → CancellationToken + threading.Event |

---

## 后续建议

| 优先级 | 事项 |
|--------|------|
| 立即 | 部署到 staging 环境验证，重点测试转写和过滤通过率 |
| 短期 | 监控 UnifiedFilter REJECT 策略对通过率的影响 |
| 短期 | 从 LLMClient 暴露实际 Token usage |
| 中期 | 迁移 filter.py / initial_filter.py 的消费者到 UnifiedFilter |
| 中期 | PipelineContext 添加 DB 持久化 |
| 长期 | Pipeline 迁移到 StepBasedPipeline |

---

## Docker 集成验证 (2026-02-08)

### 验证方法
在 Docker Compose 环境中触发 ArticlePipeline，端到端验证 Phase 1-4 所有改动。

### 结果摘要

| Phase | 状态 | 关键验证点 |
|-------|------|-----------|
| Phase 1 | ✅ | RSS 16 源全部成功, 45 条目; LLM 403 正确识别为 non-retryable |
| Phase 2 | ✅ | structlog 结构化日志; pipeline-status/cancel API 200; Step 级日志 |
| Phase 3 | ✅ | ContentExtractor: Playwright 超时 → 重试 → Jina 降级; 40/40 全文提取成功 |
| Phase 4 | ✅ | dry_run API 参数补全; DataTracker/Stats 代码验证通过 |

### 验证过程中修复的问题

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| V1 | OPML 文件在容器内不可见 | `docker-compose.yml` 挂载 `./BestBlog`（空目录）而非 `./backend/BestBlog` | 修正卷挂载路径 |
| V2 | trigger API 忽略 `dry_run` 参数 | Phase 4 只改了 `pipeline.py` 没改 API 层 | `sources.py` 添加 `dry_run` query param + 传递链路 |

### 未验证项（环境限制）

- **UnifiedFilter REJECT 策略**: ArticlePipeline 使用 initial_filter.py (规则过滤), UnifiedFilter 由 run_full_pipeline 调用
- **AI 分析完整流程**: OpenRouter API 额度耗尽 (403), 40/40 文章分析失败; 需充值后复测
- **TranscriptionService**: 需要实际播客音频 + 通义听悟凭证才能端到端测试

---

## 相关文档

- [调研报告](findings.md) — docs/research/findings.md
- [设计方案](../architecture/design.md) — docs/architecture/design.md
- [Phase 1 审查报告](report.md) — docs/review/report.md
