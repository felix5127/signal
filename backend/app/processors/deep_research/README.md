# Deep Research 处理器

## 目录说明
Deep Research 深度研究功能的核心实现，采用可扩展架构设计。

## 文件列表

### `__init__.py`
- **Input**: -
- **Output**: 模块导出 (BaseResearchEngine, ResearchResult, LightweightResearchEngine)
- **Position**: 模块入口，统一导出接口

### `base.py`
- **Input**: 配置、LLM client、Search provider
- **Output**: 抽象接口定义
- **Position**: Deep Research 基础抽象类，保证 V1/V2 接口兼容性
- **功能**:
  - `ResearchResult`: 研究结果统一数据结构
  - `BaseResearchEngine`: 研究引擎抽象基类
  - `SearchResult`: 搜索结果数据结构
  - `BaseSearchProvider`: 搜索提供商抽象基类

### `v1_lightweight.py`
- **Input**: Signal 对象，LLM client，Search provider
- **Output**: ResearchResult (1500字深度报告)
- **Position**: V1 轻量级研究引擎，3步流程实现
- **功能**:
  - Step 1: 生成3个研究问题
  - Step 2: 搜索相关内容 (Tavily API)
  - Step 3: 生成综合报告
  - 成本估算: ~$0.03/篇

### `search_providers.py`
- **Input**: 搜索查询
- **Output**: SearchResult 列表
- **Position**: 搜索提供商实现，支持 Tavily/Jina 切换
- **功能**:
  - `TavilySearchProvider`: Tavily API 实现 ($0.005/次)
  - `JinaSearchProvider`: Jina Reader 实现 (预留)

---

**更新提醒**: 一旦此文件夹有所变化，请更新本 README。
