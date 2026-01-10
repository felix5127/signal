# Backend - AI Signal Hunter

面向超级个体的技术情报分析系统后端服务。基于 FastAPI + SQLite + OpenAI，每小时自动抓取 Hacker News 高质量信号。

## 架构概述

采用**单 Prompt 方案**（非 Multi-Agent），通过规则预筛 + LLM 二次过滤实现高信噪比输出。定时任务由 APScheduler 驱动，数据存储于 SQLite (WAL 模式)。

## 文件清单

### 核心模块
- `app/main.py` - FastAPI 应用入口 + APScheduler 定时任务启动
- `app/config.py` - 配置加载（Pydantic Settings）
- `app/database.py` - SQLAlchemy 引擎 + Session 管理

### 数据模型
- `app/models/signal.py` - Signal 表 ORM 模型
- `app/models/run_log.py` - RunLog 表 ORM 模型
- `app/schemas/signal.py` - Signal API 请求/响应模型（Pydantic）
- `app/schemas/filter.py` - FilterResult 模型

### API 路由
- `app/api/signals.py` - GET /api/signals, GET /api/signals/{id}
- `app/api/health.py` - GET /health
- `app/api/stats.py` - GET /api/stats

### 数据采集
- `app/scrapers/base.py` - BaseScraper 抽象类 + 重试逻辑
- `app/scrapers/hackernews.py` - HN Firebase API 爬虫
- `app/scrapers/github.py` - GitHub Trending 爬虫（Phase 2）
- `app/scrapers/huggingface.py` - Hugging Face 爬虫（Phase 2）

### 数据处理
- `app/processors/dedup.py` - URL 去重 + 标题相似度去重
- `app/processors/filter.py` - 两阶段过滤（规则 + LLM）
- `app/processors/analyzer.py` - GitHub 尽调 + Jina Reader
- `app/processors/generator.py` - 摘要生成 + 评分

### 任务编排
- `app/tasks/pipeline.py` - 主流水线：抓取 → 去重 → 过滤 → 生成 → 入库

### 工具函数
- `app/utils/llm.py` - OpenAI 客户端封装
- `app/utils/jina.py` - Jina Reader API 调用
- `app/utils/logger.py` - 结构化日志配置

### 配置与数据
- `pyproject.toml` - Python 依赖管理（uv）
- `Dockerfile` - 后端容器镜像
- `data/` - SQLite 数据库文件目录

### 测试
- `tests/test_scrapers.py` - 爬虫单元测试
- `tests/test_filters.py` - 过滤器单元测试
- `tests/test_api.py` - API 集成测试

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
