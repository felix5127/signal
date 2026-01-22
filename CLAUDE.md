# Signal Hunter - AI 技术情报分析系统
> Python 3.11 + Next.js 14 + PostgreSQL + Docker Compose

## 定位
面向超级个体的技术情报聚合与深度分析平台，从 Hacker News 等源头自动筛选高质量技术信号，通过 AI 生成结构化摘要和研究报告。

## <directory>

### backend/ - Python 后端 (FastAPI + SQLAlchemy)
- **app/api/** - REST API 路由 (resources, signals, newsletters, stats, feeds)
- **app/models/** - 数据库模型 (Resource, Signal, Newsletter, Task)
- **app/processors/** - 内容处理器 (analyzer, generator, translator, podcast_analyzer)
- **app/scrapers/** - 数据抓取器 (hackernews, github, arxiv, huggingface)
- **app/tasks/** - 异步任务队列 (pipeline, digest, newsletter)
- **app/services/** - 业务服务 (deep_research_service, cache_service)

### frontend/ - Next.js 14 前端
- **app/** - App Router 页面 (/, /newsletters, /resources, /signals, /stats, /feeds, /landing)
- **components/ui/** - shadcn/ui 组件库 (30个组件，4个已升级微拟物设计)
- **components/landing/** - Landing Page Sections (10个Section组件)
- **components/effects/** - 视觉效果组件 (dither, dot-grid, flickering-grid)
- **components/detail/** - 详情页子组件 (FeaturedReason, AuthorInfo, AISidebar, ContentArea)
- **components/podcast/** - 播客详情页组件 (AudioPlayer, ChapterOverview, TranscriptView, QARecap, ContentTabs)
- **components/research/** - 研究工作台 (project-list, workspace)
- **components/research/panels/** - 工作台面板组件 (SourcesPanel, ChatPanel, ResearchPanel)
- **lib/design-system/** - 设计系统令牌 (colors, spacing, typography)
- **lib/motion.ts** - Apple 级 Spring 动画预设库

### docs/ - 项目文档
- **architecture/** - 架构设计文档
- **deployment/** - 部署指南 (Cloudflare, Railway)

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

## 设计系统

### 微拟物设计语言 (Neumorphic Design)
- **核心原则**: 三段式渐变 + 三层阴影 + 微交互
- **CSS 变量**: `--gradient-*`, `--shadow-raised`, `--shadow-inset`
- **圆角规范**: 16px - 32px 大圆角设计
- **微交互**: hover scale-[1.02], active scale-[0.97]

### Apple 级 Spring 动效系统
- **核心哲学**: Spring 弹簧 + 阻尼落定 + 物理惯性
- **Spring 配置**:
  - 标准交互: stiffness: 400, damping: 30 (~200ms)
  - 柔和过渡: stiffness: 300, damping: 35 (~350ms)
  - 弹性强调: stiffness: 500, damping: 25 (~300ms)
  - 优雅落定: stiffness: 200, damping: 40 (~500ms)
  - 惯性滑动: stiffness: 150, damping: 20
- **缓动曲线**: appleEase, appleEaseOut, appleDecelerate
- **动画预设**: fadeInUp, scaleIn, staggerContainer, hoverLift, tapScale
- **页面过渡**: pageTransition (AnimatePresence + Spring)
- **可访问性**: MotionConfig reducedMotion="user"

### 已升级组件
1. **Button**: 渐变背景 + 立体阴影 + 8 种变体 + tapScale 交互动画
2. **Card**: 4 种阴影变体 (default/raised/inset/outline) + hoverLift 提升
3. **Input**: 内凹阴影效果，聚焦增强
4. **Badge**: 渐变背景 + 悬停增强
5. **Navbar**: 全局导航栏 + Spring 动画 (下滑进场 + hover 提升 + tap 缩放)
6. **PageTransition**: 页面路由过渡 (AnimatePresence + Spring 物理引擎)

### 颜色系统
- **主色调**: Primary (蓝色系)
- **辅助色**: Secondary (灰色系)
- **强调色**: Accent (紫色系)
- **语义色**: Destructive (红色), Success (绿色)

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

## 核心功能

### 1. 信号采集
- Hacker News 热门新闻
- GitHub Trending 仓库
- arXiv 新论文
- Hugging Face 新模型
- Product Hunt 热门产品

### 2. AI 处理
- **过滤规则**: 新代码/新模型/新论文/可复现结果/可用工具
- **摘要生成**: 一句话总结 + 详细摘要 (300字)
- **评分系统**: 0-100 分，≥70 分为精选
- **分类标签**: AI/ML/Web3/DevTools/Career 等

### 3. 深度研究 (Deep Research)
- 一键生成 1500 字研究报告
- 技术分析 + 竞品对比 + 应用场景
- 搜索增强 (Tavily API)

### 4. 周刊生成
- 每周自动汇总精选信号
- 生成 HTML/PDF 格式周刊
- 邮件订阅推送

### 5. 数据导出
- RSS 订阅源
- JSON API
- CSV 导出

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

## [PROTOCOL]
变更时更新此头部，然后检查子模块 CLAUDE.md
