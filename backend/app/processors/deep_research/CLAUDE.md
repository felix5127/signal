# backend/app/processors/deep_research/
> L2 | 父级: backend/app/processors/CLAUDE.md

## 职责
Deep Research 深度研究引擎，可扩展架构，支持多策略研究和多搜索提供商。

## 成员清单
__init__.py: 模块入口，统一导出 BaseResearchEngine, ResearchResult, LightweightResearchEngine
base.py: 抽象基类 (BaseResearchEngine, BaseSearchProvider) + 数据结构 (ResearchResult, SearchResult)
v1_lightweight.py: V1 轻量级引擎，3 步流程 (生成问题 → 搜索 → 生成报告)，成本 ~$0.03/篇
search_providers.py: 搜索提供商实现 — TavilySearchProvider ($0.005/次) + JinaSearchProvider (预留)

## 研究流程
```
Step 1: 生成 3 个研究问题
Step 2: Tavily API 搜索相关内容
Step 3: 整合搜索结果 + 原文，生成 1500 字报告
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
