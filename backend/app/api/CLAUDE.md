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
tasks.py: 异步任务状态查询，GET /tasks/{task_id}
video.py: 视频相关端点

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
| /api/tasks | tasks.py | 任务状态 |

## 缓存策略
- 资源列表: 5min TTL
- 资源详情: 10min TTL
- 统计数据: 1min TTL

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
