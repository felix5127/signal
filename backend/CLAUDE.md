# backend/
> L2 | Signal Hunter Python 后端

## 职责
FastAPI 驱动的 RESTful API 服务，负责数据采集、AI 分析、存储和接口暴露。

## 成员清单
app/: 应用主目录，包含所有业务逻辑
requirements.txt: Python 依赖定义 (FastAPI, SQLAlchemy, APScheduler 等)
Dockerfile: 生产环境容器构建配置
Dockerfile.dev: 开发环境容器配置 (热重载)
BestBlog/: BestBlogs OPML 订阅源配置

## 技术栈
FastAPI 0.115+ | SQLAlchemy 2.0 | PostgreSQL 15 | APScheduler | Redis 7

## 核心能力
- **数据采集**: 16 个爬虫适配 (RSS/HN/GitHub/arXiv/HuggingFace/Twitter 等)
- **AI 分析**: 规则预筛 + LLM 初评 + 三步深度分析
- **深度研究**: Tavily 搜索增强 + LLM 报告生成
- **定时任务**: APScheduler 驱动的自动化流水线
- **API 暴露**: RESTful 接口 + Redis 缓存

## 数据流
```
[定时任务] → [数据采集] → [初评过滤] → [深度分析] → [翻译] → [DB存储] → [API暴露]
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
