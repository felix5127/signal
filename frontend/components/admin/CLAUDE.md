# admin/
> L2 | 父级: components/CLAUDE.md

## 职责
Admin 后台管理页面的内容组件，与 app/admin/ 页面路由一一对应。

## 成员清单

**dashboard-page-content.tsx**: 数据统计仪表板入口
- 技术细节: 客户端组件，导入 dashboard/ 目录的完整仪表板
- 导出: default DashboardPageContent
- 功能: 包装 AdminDashboard 组件

**dashboard/**: 仪表板组件目录
- index.tsx: 主入口组件，编排所有子组件布局
- hooks/useDashboardData.ts: 数据获取 Hook，30 秒自动刷新
- SystemHealthHero.tsx: 系统健康指示器（三色状态灯 + 呼吸动画）
- PipelineStatusCard.tsx: Pipeline 状态卡片（运行状态 + 倒计时 + 队列）
- CollectionFunnel.tsx: 采集漏斗可视化（今日数据流转）
- MetricCard.tsx: 通用指标卡片（可复用）
- ProcessingQueueCard.tsx: 处理队列卡片（待翻译 + 待转写）
- StatusDistributionCard.tsx: 状态分布卡片
- DailyTrendChart.tsx: 近 7 日趋势图表
- DataQualityCard.tsx: 数据完整率卡片
- SourceHealthCard.tsx: RSS 源健康卡片
- TranscriptionCard.tsx: 转写成功率卡片
- API: GET /api/admin/stats/overview, /pipeline-status, /today-funnel, /daily, /score-distribution, /data-quality, /source-health, /transcription

**sources-page-content.tsx**: 信号源控制台内容
- 技术细节: 客户端组件，信号源状态管理
- 导出: default AdminSourcesPage
- 功能: 4种信号源状态卡片、采集记录表、手动触发、启用/禁用
- 活跃数据源: twitter, blog, podcast, video
- 已移除: hackernews, github, huggingface, arxiv, producthunt（无有效数据）
- 已移除: FunnelChart（已移至 Dashboard，避免重复）
- 子组件: SourceCard, RunsTable, FilteringRulesPanel

**review-page-content.tsx**: 内容审核页面内容
- 技术细节: 客户端组件，人工审核 LLM 筛选结果
- 导出: default ReviewPageContent
- 功能: 审核列表、通过/拒绝操作、筛选标签、审核统计、分页
- 子组件: ReviewItemCard, FilterTabs, StatsCard, Pagination
- API: GET /api/admin/review/list, /stats; POST /api/admin/review/{id}/action

**scheduler-page-content.tsx**: 调度器状态内容
- 技术细节: 客户端组件，APScheduler 状态展示
- 导出: default SchedulerPageContent
- 功能: 定时任务列表、下次运行时间、手动触发

**system-page-content.tsx**: 系统健康内容
- 技术细节: 客户端组件，系统监控
- 导出: default SystemPageContent
- 功能: 数据库状态、Redis 状态、存储统计

**logs-page-content.tsx**: 采集日志内容
- 技术细节: 客户端组件，采集历史详情
- 导出: default LogsPageContent
- 功能: 采集记录列表、漏斗详情、错误信息

**prompts-page-content.tsx**: Prompt 版本管理页面内容
- 技术细节: 客户端组件，Prompt 版本 CRUD
- 导出: default PromptsPageContent
- 功能: Prompt 列表（按类型分组）、版本激活、创建新版本、效果统计（使用次数/平均评分/通过率）
- 子组件: PromptCard（展开/收起 Prompt 内容）, CreatePromptDialog
- API: GET /api/admin/prompts; POST /api/admin/prompts; POST /api/admin/prompts/{id}/activate

**login-page-content.tsx**: 登录页面内容
- 技术细节: 客户端组件，密码验证
- 导出: default LoginPageContent
- 功能: 输入密码，验证后设置 Cookie

## 设计规范

### CSS 变量
- 背景: var(--ds-bg), var(--ds-surface)
- 前景: var(--ds-fg), var(--ds-muted)
- 边框: var(--ds-border)

### 图标库
- lucide-react: 所有图标统一使用

### 布局模式
- 页面容器: py-8 px-4 sm:px-6 lg:px-8, max-w-6xl mx-auto
- 卡片: bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)]
- 网格: grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4

### 交互模式
- 按钮: rounded-lg + hover 颜色变化 + disabled:opacity-50
- 加载: border-4 + animate-spin
- 错误: 红色背景 + AlertTriangle 图标

## 变更日志

### 2026-02-01 - Admin 页面大规模精简
**页面精简：7 → 4**
- 删除 scheduler 页面（调度器未初始化，显示空白）
- 删除 system 页面（与 Dashboard 重复，已合并）
- 删除 logs 页面（与信号源重复，已合并）
- 导航菜单从 7 项减少到 4 项

**信号源页面优化**
- 移除 FunnelChart 组件（Dashboard 已有）
- 移除 funnel 状态和 API 调用
- 保留 SourceCard + RunsTable 核心功能

**数据源清理**
- 数据源从 9 个减少到 4 个
- 移除: Hacker News, GitHub, Hugging Face, arXiv, Product Hunt
- 保留: Twitter, Blog RSS, Podcast, Video

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
