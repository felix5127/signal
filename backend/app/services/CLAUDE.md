# backend/app/services/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
业务逻辑层，编排复杂业务流程，管理事务，调用 Models 和 Processors。

## 成员清单
resource_service.py: 资源 CRUD、筛选、搜索服务 (v2 核心)
signal_service.py: 信号查询、统计服务 (v1 Legacy)
deep_research_service.py: 深度研究统一入口，策略选择、成本控制、缓存管理
cache_service.py: Redis 缓存管理，key 生成、TTL 控制
source_service.py: 信号源管理，状态查询、配置管理、采集记录、漏斗统计

## 服务职责

### ResourceService
- get_resources(): 多维筛选 (时间/类型/分类/评分/语言/来源)
- get_resource_by_id(): 单条查询
- search(): 全文搜索 (ILIKE)

### SignalService (Legacy)
- get_signals(): 信号列表查询
- get_signal_stats(): 统计信息

### DeepResearchService
- generate_research(): 生成深度研究报告
- 策略选择: LIGHTWEIGHT (当前) / AUTO
- 成本控制: 单篇限额检查、每日限额检查
- 缓存管理: 检查已有报告、避免重复生成

### CacheService
- cache_result(): 装饰器，自动缓存函数结果
- make_list_key(): 生成列表缓存 key
- make_detail_key(): 生成详情缓存 key

### SourceService
- get_all_status(): 所有信号源状态概览
- get_source_detail(): 单个信号源详情
- toggle_source(): 启用/禁用信号源
- get_runs(): 分页查询采集历史
- record_run(): 记录一次采集运行
- get_feeds(): 获取 OPML feed 列表
- get_funnel_stats(): 聚合漏斗统计

## 设计模式
- **策略模式**: DeepResearchService 支持多种研究策略
- **装饰器模式**: CacheService 提供缓存装饰器
- **单例模式**: 全局 service 实例

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
