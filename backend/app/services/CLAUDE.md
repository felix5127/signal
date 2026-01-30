# backend/app/services/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
业务逻辑层，编排复杂业务流程，管理事务，调用 Models 和 Processors。

## 成员清单
resource_service.py: 资源 CRUD、筛选、搜索服务 (v2 核心)
signal_service.py: 信号查询、统计服务 (v1 Legacy)
deep_research_service.py: 深度研究统一入口，策略选择、成本控制、缓存管理
cache_service.py: Redis 缓存管理，key 生成、TTL 控制
source_service.py: 信号源管理，状态查询、配置管理、采集记录、漏斗统计 (基于 SourceConfig)
source_manage_service.py: 数据源 CRUD 管理，白名单设置，启用/禁用，统计更新 (基于 Source 模型)
source_health.py: 信号源健康检查，状态监控
prompt_service.py: Prompt 版本管理，创建/激活/归档版本，使用统计更新
stats_service.py: 统计数据服务，整体统计、数据源统计、时间统计、LLM 评分分布
review_service.py: 内容审核服务，待审核列表、审核操作、批量审核、审核统计
storage_service.py: R2/S3 文件存储服务，上传/下载/预签名URL/文件管理 (研究助手 v3)
feishu_service.py: 飞书多维表格 API 封装，token 管理、批量记录写入
data_tracker.py: 数据追踪器，Pipeline 各节点调用，收集并批量写入飞书追踪记录

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

### SourceManageService (基于 Source 模型)
- get_all_sources(): 多条件筛选数据源列表 (类型/启用状态/白名单)
- get_source_by_id(): 根据 ID 获取数据源
- get_source_by_url(): 根据 URL 获取数据源
- create_source(): 创建新数据源
- update_source(): 更新数据源信息
- delete_source(): 删除数据源
- set_whitelist(): 设置白名单状态
- toggle_enabled(): 切换启用状态
- update_source_stats(): 从 Resource 聚合更新统计数据
- update_all_stats(): 批量更新所有数据源统计

### PromptService
- get_active_prompt(): 获取指定类型的活跃 Prompt
- get_prompts_by_type(): 获取指定类型的所有版本
- get_all_prompts(): 获取全部 Prompt
- get_prompt_by_id(): 根据 ID 获取
- create_prompt(): 创建新版本 (自动递增版本号)
- activate_prompt(): 激活版本 (自动归档同类型旧版本)
- update_stats(): 更新使用统计 (次数、平均分、通过率)

### StatsService
- get_overview_stats(): 整体统计概览 (总数、状态分布、今日统计、平均评分、数据源统计)
- get_source_stats(): 按数据源统计 (采集量、通过率、平均评分)
- get_daily_stats(): 每日统计 (指定天数内的每日数据)
- get_score_distribution(): LLM 评分分布 (0-5 分各档数量)
- get_data_quality_stats(): 内容完整率统计 (播客/视频/文章的关键字段填充率)
- get_source_health_stats(): RSS 源健康状态 (基于最近 7 天采集成功率，三级健康状态)
- get_transcription_stats(): 转写成功率统计 (有音频但无转录的记录，待转写列表)
- get_pipeline_status(): Pipeline 实时状态 (运行状态、上次运行、下次运行倒计时、处理队列)
- get_today_funnel_stats(): 今日采集漏斗统计 (抓取→规则过滤→去重→LLM过滤→保存)

### ReviewService
- get_review_list(): 获取待审核列表 (按状态/来源/日期筛选，分页)
- review_action(): 执行审核操作 (publish/reject/restore)，记录 Review 日志
- batch_review(): 批量审核多个资源
- get_review_stats(): 获取审核统计 (按状态/来源分组，人工改判数)

### StorageService (R2/S3)
- generate_path(): 生成存储路径 (research/{project_id}/{category}/{entity_id}/{filename})
- validate_file(): 验证文件类型和大小
- upload_file(): 上传文件到 R2
- upload_from_bytes(): 从字节数据上传
- generate_presigned_upload_url(): 生成预签名上传 URL (客户端直传)
- download_file(): 下载文件
- generate_presigned_download_url(): 生成预签名下载 URL
- delete_file(): 删除单个文件
- delete_folder(): 删除文件夹 (批量删除)
- get_file_info(): 获取文件元信息

### FeishuService
- get_tenant_token(): 获取飞书 tenant_access_token (带缓存，自动刷新)
- create_record(): 新增单条记录
- batch_create_records(): 批量新增记录 (最多 500 条)

### DataTracker
- track(): 添加追踪记录 (TrackingRecord)
- track_filtered(): 快捷方法，记录被过滤的内容
- track_collected(): 快捷方法，记录被收录的内容
- flush(): 批量写入飞书，失败不影响主流程

## 设计模式
- **策略模式**: DeepResearchService 支持多种研究策略
- **装饰器模式**: CacheService 提供缓存装饰器
- **单例模式**: 全局 service 实例
- **追踪模式**: DataTracker 在 Pipeline 各节点收集数据，最后批量写入

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
