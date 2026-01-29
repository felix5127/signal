# migrations/
> L2 | 父级: backend/CLAUDE.md

## 职责
数据库迁移脚本，手动执行的 SQL 变更记录。

## 成员清单
001_data_pipeline_refactor.sql: 数据管线重构迁移，添加 sources/prompts/reviews 表，扩展 resources 表
002_research_assistant.sql: 研究助手迁移，pgvector 扩展 + 6 个研究相关表 + HNSW 向量索引
003_add_thumbnail_url.sql: 添加 thumbnail_url 字段用于存储播客/视频缩略图

## 执行方式
```bash
# 在 Docker 容器中执行
docker exec -i signal-db psql -U signal_user -d signal_db < migrations/001_data_pipeline_refactor.sql
docker exec -i signal-db psql -U signal_user -d signal_db < migrations/002_research_assistant.sql
docker exec -i signal-db psql -U signal_user -d signal_db < migrations/003_add_thumbnail_url.sql

# 或直接连接数据库
psql -h localhost -U signal_user -d signal_db -f migrations/001_data_pipeline_refactor.sql
psql -h localhost -U signal_user -d signal_db -f migrations/002_research_assistant.sql
psql -h localhost -U signal_user -d signal_db -f migrations/003_add_thumbnail_url.sql
```

## 版本历史
| 版本 | 日期 | 描述 |
|------|------|------|
| 001 | 2026-01-17 | 数据管线重构：LLM 过滤、人工审核、数据源管理、Prompt 版本 |
| 002 | 2026-01-17 | 研究助手：pgvector 扩展、research_projects/sources/embeddings/outputs/chat_sessions/agent_tasks 表 |
| 003 | 2026-01-29 | 添加 thumbnail_url 字段：播客/视频缩略图支持 |

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
