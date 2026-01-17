# admin/
> L2 | 父级: app/CLAUDE.md

## 职责
Admin 后台管理系统，密码保护的运维监控面板。

## 成员清单

**login/page.tsx**: 登录页面
- 技术细节: 客户端组件，密码验证
- 路由: /admin/login
- 功能: 输入密码，验证后设置 Cookie

**layout.tsx**: Admin 布局
- 技术细节: 客户端组件，侧边栏导航
- 功能: 统一布局，侧边栏导航，响应式设计
- 导航项: 数据统计/信号源/内容审核/Prompt管理/调度器/系统状态/采集日志

**dashboard/page.tsx**: 数据统计仪表板
- 技术细节: 客户端组件，动态导入
- 路由: /admin/dashboard
- 功能: 资源总览、状态分布、近7日趋势、LLM评分分布
- 组件: MetricCard, StatusCard, DailyChart, ScoreDistributionChart

**sources/page.tsx**: 信号源控制台
- 技术细节: 客户端组件，信号源状态管理
- 路由: /admin/sources
- 功能: 9种信号源状态、采集漏斗、手动触发、启用/禁用
- 组件: SourceCard, FunnelChart, RunsTable

**review/page.tsx**: 内容审核
- 技术细节: 客户端组件，人工审核 LLM 筛选结果
- 路由: /admin/review
- 功能: 审核列表、通过/拒绝操作、筛选标签、审核统计
- 组件: ReviewItemCard, FilterTabs, StatsCard, Pagination

**prompts/page.tsx**: Prompt 版本管理
- 技术细节: 客户端组件，Prompt 版本 CRUD
- 路由: /admin/prompts
- 功能: Prompt 列表、版本激活、创建新版本、效果统计（使用次数/平均评分/通过率）
- 组件: PromptCard, CreatePromptDialog

**scheduler/page.tsx**: 调度器状态
- 技术细节: 客户端组件，APScheduler 状态展示
- 路由: /admin/scheduler
- 功能: 定时任务列表、下次运行时间、手动触发

**system/page.tsx**: 系统健康
- 技术细节: 客户端组件，系统监控
- 路由: /admin/system
- 功能: 数据库状态、Redis 状态、存储统计

**logs/page.tsx**: 采集日志
- 技术细节: 客户端组件，采集历史详情
- 路由: /admin/logs
- 功能: 采集记录列表、漏斗详情、错误信息

## 路由保护

**middleware.ts** (frontend/):
- 保护所有 /admin/* 路由（排除 /admin/login）
- Cookie 认证: `admin_auth=authenticated`
- 未认证重定向到 /admin/login

**api/admin/login/route.ts**:
- POST: 验证密码，设置 Cookie（7天有效）
- 密码来源: 环境变量 ADMIN_PASSWORD

**api/admin/logout/route.ts**:
- POST: 清除认证 Cookie

## 后端 API 依赖

| 前端路由 | 后端 API |
|---------|---------|
| /admin/dashboard | GET /api/admin/stats/overview, /daily, /score-distribution |
| /admin/sources | GET /api/sources/status, /funnel, /runs |
| /admin/sources | POST /api/sources/toggle/{type}, /trigger/{type} |
| /admin/review | GET /api/admin/review/list, /stats |
| /admin/review | POST /api/admin/review/{id}/action |
| /admin/prompts | GET /api/admin/prompts |
| /admin/prompts | POST /api/admin/prompts |
| /admin/prompts | POST /api/admin/prompts/{id}/activate |
| /admin/scheduler | GET /api/stats/scheduler |
| /admin/system | GET /api/stats/system |
| /admin/logs | GET /api/sources/runs |

## 设计特点

- 响应式侧边栏（移动端抽屉式）
- 实时状态指示（绿/黄/红状态点）
- 手动触发采集（后台异步执行）
- 错误详情展开（可折叠）
- 自动刷新（30秒/60秒间隔）

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
