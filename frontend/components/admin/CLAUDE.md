# admin/
> L2 | 父级: components/CLAUDE.md

## 职责
Admin 后台管理页面的内容组件，与 app/admin/ 页面路由一一对应。

## 成员清单

**dashboard-page-content.tsx**: 数据统计仪表板内容
- 技术细节: 客户端组件，多 API 并行请求
- 导出: default DashboardPageContent
- 功能: 资源总览、状态分布、近7日趋势、LLM评分分布
- 子组件: MetricCard, StatusCard, DailyChart, ScoreDistributionChart
- API: GET /api/admin/stats/overview, /daily, /score-distribution

**sources-page-content.tsx**: 信号源控制台内容
- 技术细节: 客户端组件，信号源状态管理
- 导出: default AdminSourcesPage
- 功能: 9种信号源状态卡片、采集漏斗图、手动触发、启用/禁用
- 子组件: SourceCard, FunnelChart, RunsTable, FilteringRulesPanel

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

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
