# backend/app/
> L2 | 父级: backend/CLAUDE.md

## 职责
Signal 后端应用主目录，包含所有业务逻辑代码。

## 成员清单
main.py: FastAPI 应用入口，路由注册，调度器初始化，启动/关闭事件
config.py: 配置加载器，合并 YAML + 环境变量，提供全局 config 对象
database.py: SQLAlchemy 数据库连接，SessionLocal 工厂，init_db 初始化

api/: REST API 路由层 (9 个端点模块)
models/: ORM 数据模型 (5 个业务模型)
services/: 业务逻辑层 (4 个服务)
processors/: 内容处理引擎 (7 个处理器)
scrapers/: 多源数据采集 (4 类数据源: RSS/Twitter/Podcast/Video)
tasks/: 异步任务系统 (5 个任务模块)
utils/: 工具函数库 (4 个工具)
middlewares/: 中间件 (错误处理/认证)
schemas/: Pydantic 响应模型
schedulers/: 定时任务调度配置

## 核心数据流
```
RSS采集 → 全文提取 → 初评过滤(规则+LLM) → 深度分析(三步) → 翻译分流 → DB存储 → API暴露
```

## 分层架构
```
L0: API Layer (api/)        ← HTTP 请求入口
L1: Service Layer (services/) ← 业务编排
L2: Processor Layer (processors/) ← 单一责任处理
L3: Scraper Layer (scrapers/)   ← 数据采集
L4: Model Layer (models/)     ← ORM 定义
L5: Task Layer (tasks/)       ← 流水线编排
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
