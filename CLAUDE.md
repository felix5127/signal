# Signal - AI 技术情报分析系统
> Python 3.11 + Next.js 14 + PostgreSQL + Docker Compose

## 定位
面向超级个体的技术情报聚合与深度分析平台，自动筛选高质量技术信号，通过 AI 生成结构化摘要和研究报告。

## 文档导航

> CLAUDE.md 体系描述"怎么做"，需求文档体系描述"做什么"和"为什么"

| 文档 | 描述 | 类型 |
|------|------|------|
| [PRODUCT.md](PRODUCT.md) | 产品愿景与路线图 | 需求文档 |
| [docs/FEATURES.md](docs/FEATURES.md) | 功能规格说明 | 需求文档 |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | 数据源目录 | 需求文档 |
| [docs/API.md](docs/API.md) | API 接口参考 | 需求文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计决策 | 需求文档 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 部署运维指南 | 需求文档 |

## <directory>

### backend/ - Python 后端 (FastAPI + SQLAlchemy)
- **app/api/** - REST API 路由 (resources, digest, stats, feeds, admin)
- **app/models/** - 数据库模型 (Resource, Signal, Newsletter, Task, Source)
- **app/processors/** - 内容处理器 (analyzer, generator, translator, podcast_analyzer)
- **app/scrapers/** - 数据抓取器 (rss, xgoing, podcast, video)
- **app/tasks/** - 异步任务队列 (pipeline, digest, newsletter)
- **app/services/** - 业务服务 (resource, source, cache, deep_research, feishu, data_tracker)
- **app/utils/** - 工具函数 (llm, cache, jina, logger)
- **app/schemas/** - Pydantic 数据传输对象
- **app/agents/** - AI Agent (mindmap, multimodal, podcast)

### frontend/ - Next.js 14 前端
- **app/** - App Router 页面 (/, /articles, /podcasts, /tweets, /videos, /featured, /feeds, /stats)
- **components/ui/** - shadcn/ui 组件库 (30+ 组件)
- **components/landing/** - Landing Page Sections (10 个 Section 组件)
- **components/detail/** - 详情页子组件 (FeaturedReason, AuthorInfo, AISidebar, ContentArea)
- **components/podcast/** - 播客详情页组件 (AudioPlayer, ChapterOverview, TranscriptView, QARecap)
- **components/research/** - 研究工作台 (project-list, workspace, panels)
- **lib/design-system/** - 设计系统令牌 (colors, spacing, typography)
- **lib/motion.ts** - Apple 级 Spring 动画预设库

### docs/ - 项目文档
- **archive/** - 归档文档 (BestBlog/, ANIMATION_GUIDE, DEEP_RESEARCH_API 等)



## <config>

### docker-compose.yml - 容器编排配置
- 定义 backend, frontend, db 三个服务
- 后端热重载卷挂载: `./backend/app:/app/app`
- 环境变量文件: `.env`

### backend/requirements.txt - Python 依赖
- FastAPI: Web 框架
- SQLAlchemy: ORM
- APScheduler: 定时任务
- httpx: 异步 HTTP 客户端
- feedparser: RSS 解析

### frontend/package.json - Node 依赖
- Next.js 14.2.0: React 框架
- shadcn/ui: UI 组件库
- Framer Motion: 动画库
- React Icons: 图标库

## 技术栈

### 后端
- **Web 框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0+
- **任务队列**: APScheduler + BackgroundTasks
- **AI 集成**: Moonshot Kimi API

### 前端
- **框架**: Next.js 14 (App Router)
- **样式**: TailwindCSS v3.4.0
- **组件库**: shadcn/ui (30+ 组件)
- **设计系统**: 微拟物光影质感 (Neumorphic Design)
- **动画系统**: Apple 级 Spring 物理引擎
  - Framer Motion + Spring 配置
  - 5 种 Spring 预设 (snappy/gentle/bouncy/smooth/inertia)
  - 页面路由过渡 (pageTransition)
  - 交互动画 (hoverLift, tapScale)
  - 可访问性支持 (MotionConfig reducedMotion)
- **状态管理**: React Hooks

### DevOps
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx (生产环境)
- **部署**: Railway / Cloudflare Pages




## 数据流架构

```
[定时任务 APScheduler]
       ↓
[数据抓取 Scrapers]
       ↓
[初步过滤 Initial Filter]
       ↓
[AI 分析 Analyzer] → [评分 + 摘要 + 分类]
       ↓
[数据库存储 PostgreSQL]
       ↓
[API 暴露 FastAPI]
       ↓
[前端展示 Next.js]
```



## 环境变量

### 必需变量
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/signal

# AI API
MOONSHOT_API_KEY=sk-xxx
TAVILY_API_KEY=tvly-xxx

# Security
JWT_SECRET_KEY=your-secret-key
ENVIRONMENT=development
```

### 可选变量
```bash
# API Keys (生产环境)
API_KEYS=key1,key2,key3

# CORS
FRONTEND_URL=http://localhost:3000
```

## 开发规范

### Git 工作流
- 主分支: `main`
- 功能分支: `feature/*`
- 修复分支: `fix/*`
- 提交规范: `feat:`, `fix:`, `docs:`, `refactor:`

### 代码风格
- **Python**: Black + isort + flake8
- **TypeScript**: ESLint + Prettier
- **注释**: 中文 + ASCII 风格分块

### GEB 分形文档协议
- **L1**: 项目根目录 `CLAUDE.md` (本文件)
- **L2**: 模块目录 `CLAUDE.md` (如 components/ui/CLAUDE.md)
- **L3**: 文件头部 `/** [INPUT]... [OUTPUT]... [POS]... */`

强制回环: 代码变更 → L3 更新 → L2 更新 → L1 更新

## 部署

### 开发环境
```bash
docker-compose up -d
```

### 生产环境
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 云平台
- **Railway**: 后端 + 数据库
- **Cloudflare Pages**: 前端静态部署

## 法则
极简 · 稳定 · 导航 · 版本精确



 Agent Team Recipes

> 以下 Recipe 供 Agent Team Lead 读取，用于理解如何组建和协调团队。
> 使用方式：告诉 Claude "按照 {Recipe 名} 创建 agent team 来 {任务描述}"

## Recipe: Full Pipeline（完整流水线）

### 触发场景
新 feature 开发、重大重构、技术方案落地

### 团队结构

| 角色 | 模型 | 权限 | 职责 |
|------|------|------|------|
| Lead | 默认 | delegate mode（纯协调，不写代码） | 拆任务、审批方案、控制修复轮、汇总结果 |
| Researcher | Opus | 只读 | 调研代码/文档/依赖，产出 findings.md |
| Architect | Opus | 只读 + 写设计文档 | 设计方案，产出 design.md，需 Lead 审批（plan approval） |
| Developer | Sonnet | 读写代码 | 按设计实现，写测试，遇歧义 message Architect |
| Reviewer | Opus | 只读 + 写报告 | 审查实现，按 CRITICAL/HIGH/MEDIUM 分级 |

### 工作流

```
1. Lead 拆解任务，创建 task list（含依赖关系）
2. Lead spawn Researcher (Opus) + Architect (Opus)
   → Researcher 调研，产出 docs/research/findings.md
   → Architect 可提前熟悉代码，但不产出设计直到 Research 完成
3. Research 完成 → Architect 读取 findings.md 设计方案
   → 如有遗漏，message Researcher 补充
   → 产出 docs/architecture/design.md，提交 Lead 审批
4. Lead 审批通过 → spawn Developer (Sonnet)
   → Developer 按设计实现，遇歧义 message Architect
   → 代码 + 测试完成
5. Lead spawn Reviewer (Opus)
   → Reviewer 对照 design.md 审查实现
   → 产出 docs/review/report.md（CRITICAL/HIGH/MEDIUM）
6. Lead 审阅报告
   → 有 CRITICAL → Lead 指派 Developer 修复 → Reviewer 再审
   → 无 CRITICAL → 流程结束，Lead 汇总
```

### 产出规范
- Researcher → `docs/research/findings.md`（明确区分"已确认事实"和"未确认假设"）
- Architect → `docs/architecture/design.md`（模块边界、接口定义、数据流）
- Reviewer → `docs/review/report.md`（问题分级 + 修复建议）

### 通信规则
- Architect 发现调研不足 → message Researcher
- Developer 遇设计歧义 → message Architect
- Reviewer 发现架构级问题 → message Architect（不是 Developer）
- 所有人完成任务 → 自动通知 Lead

### 修复环路（Lead 控制）
1. Reviewer 产出报告
2. Lead 判断是否有 CRITICAL 级别问题
3. 有 → Lead 指派 Developer 修复 → Reviewer 再审
4. 无 → 流程结束

### 约束
- 每人只修改自己职责范围内的文件，禁止交叉编辑
- Developer 不得自行决定设计变更
- Reviewer 不得直接修改代码
- Researcher 产出必须区分事实与假设



## [PROTOCOL]
变更时更新此头部，然后检查子模块 CLAUDE.md
