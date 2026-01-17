# backend/app/api/admin/
> L2 | 父级: backend/app/api/CLAUDE.md

## 职责
Admin 管理 API，提供后台管理功能的 HTTP 接口。

## 成员清单
__init__.py: 子包入口
sources.py: 数据源管理 CRUD (GET/POST/PUT/DELETE /api/admin/sources)
stats.py: Admin 统计 API (/overview, /daily, /sources, /score-distribution)
review.py: Admin 审核 API (/list, /action, /{resource_id}/action, /stats)
prompts.py: Admin Prompt 管理 API (列表/活跃版本/创建/激活)

## 端点概览
| 路由 | 方法 | 功能 |
|------|------|------|
| /api/admin/sources | GET | 获取数据源列表（支持类型/启用/白名单筛选） |
| /api/admin/sources | POST | 创建新数据源 |
| /api/admin/sources/{id} | PUT | 更新数据源 |
| /api/admin/sources/{id} | DELETE | 删除数据源 |
| /api/admin/sources/{id}/stats | GET | 获取数据源详情统计 |
| /api/admin/stats/* | GET | 统计概览/每日统计/数据源统计/评分分布 |
| /api/admin/review/* | GET/POST | 审核列表/审核操作/审核统计 |
| /api/admin/prompts/* | GET/POST | Prompt 列表/活跃版本/创建/激活 |

## 依赖服务
- SourceManageService: 数据源 CRUD 操作
- StatsService: 统计数据查询
- ReviewService: 审核操作
- PromptService: Prompt 管理

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
