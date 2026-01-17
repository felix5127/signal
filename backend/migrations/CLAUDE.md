# migrations/
> L2 | 父级: backend/CLAUDE.md

## 职责
数据库迁移脚本，手动执行的 SQL 变更记录。

## 成员清单
001_data_pipeline_refactor.sql: 数据管线重构迁移，添加 sources/prompts/reviews 表，扩展 resources 表

## 执行方式
```bash
# 在 Docker 容器中执行
docker exec -i signal-db psql -U postgres -d signal < migrations/001_data_pipeline_refactor.sql

# 或直接连接数据库
psql -h localhost -U postgres -d signal -f migrations/001_data_pipeline_refactor.sql
```

## 版本历史
| 版本 | 日期 | 描述 |
|------|------|------|
| 001 | 2026-01-17 | 数据管线重构：LLM 过滤、人工审核、数据源管理、Prompt 版本 |

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
