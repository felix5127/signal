# backend/app/api/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
REST API 路由层，处理 HTTP 请求，参数验证，调用 Service 层，返回 JSON 响应。

## 成员清单
resources.py: 资源 CRUD (v2 核心)，GET/POST /resources, /search, /deep-research
signals.py: 信号 API (v1 Legacy)，GET/POST /signals, /signals/{id}/deep-research
digest.py: 日周精选汇总，GET /digest/today, /digest/week, /digest/weeks
newsletters.py: 周刊 CRUD，GET/POST /newsletters/{id}
feeds.py: RSS 订阅源，GET /feeds/{type} (返回 XML)
stats.py: 统计与健康检查，GET /stats, /health
sources.py: 热门来源 + 信号源管理，/sources/hot, /status, /funnel, /toggle, /runs, /feeds
tasks.py: 任务状态查询 + Pipeline 触发，GET /tasks, POST /tasks/pipeline/trigger
video.py: 视频相关端点
auth.py: 用户认证 API，注册/登录/刷新/登出/OAuth (GitHub/Google)
admin/: Admin 管理端点子模块
admin/sources.py: Admin 数据源管理 API，GET/POST/PUT/DELETE /sources, /sources/{id}/stats
admin/stats.py: Admin 统计 API，/overview, /daily, /sources, /score-distribution
admin/review.py: Admin 审核 API，/list, /action, /{resource_id}/action, /stats
admin/prompts.py: Admin Prompt 管理 API
research.py: 研究助手 API (项目/源材料/研究任务/对话/输出) - SSE 流式支持
podcast.py: 播客生成 API (文本转播客/项目转播客/音色列表) - SSE 流式支持

## 端点概览
| 路由前缀 | 模块 | 核心功能 |
|---------|------|---------|
| /api/resources | resources.py | 资源列表/详情/搜索/深度研究 |
| /api/signals | signals.py | 信号列表/详情 (Legacy) |
| /api/digest | digest.py | 今日精选/本周精选/历史周刊 |
| /api/newsletters | newsletters.py | 周刊管理 |
| /api/feeds | feeds.py | RSS 订阅源输出 |
| /api/stats | stats.py | 系统统计 |
| /api/sources | sources.py | 热门来源 + 信号源状态/配置/采集记录 |
| /api/tasks | tasks.py | 任务状态 + Pipeline 触发 |
| /api/admin/sources | admin/sources.py | Admin 数据源 CRUD / 详情统计 |
| /api/admin/stats | admin/stats.py | Admin 统计概览/每日/数据源/评分分布 |
| /api/admin/review | admin/review.py | Admin 审核列表/批量审核/单个审核/审核统计 |
| /api/admin/prompts | admin/prompts.py | Prompt 列表/活跃版本/创建/激活 |
| /api/research | research.py | 研究助手 - 项目/源/研究/对话/输出 |
| /api/podcast | podcast.py | 播客生成 - 文本转播客/项目转播客/音色列表 |
| /api/auth | auth.py | 用户认证 - 注册/登录/刷新/登出/OAuth |

## 缓存策略
- 资源列表: 5min TTL
- 资源详情: 10min TTL
- 统计数据: 1min TTL

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
