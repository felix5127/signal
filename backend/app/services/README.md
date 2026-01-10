# Services 服务层

## 目录说明
本目录包含业务逻辑服务层，封装复杂的业务流程和跨模块调用。

## 文件列表

### `deep_research_service.py`
- **Input**: Signal 对象，研究策略配置
- **Output**: ResearchResult (深度研究报告)
- **Position**: Deep Research 统一服务入口，负责策略选择、成本控制、缓存管理
- **功能**:
  - 策略选择 (Lightweight/Full Agent)
  - 成本预估和限制
  - 每日生成限额检查
  - 缓存管理 (24小时)
  - 数据库持久化

---

**更新提醒**: 一旦此文件夹有所变化，请更新本 README。
