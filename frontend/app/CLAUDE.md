# app/
> L2 | 父级: ../CLAUDE.md

## 页面路由组织

### 布局文件

**layout.tsx**: 根布局
- 技术细节: 服务端组件，包含全局元数据、主题脚本、MotionConfig
- 导出: default function RootLayout({ children })
- 核心功能: 全局布局容器，包裹 Navbar、页面内容、Footer
- 新增: MotionConfig 全局动画配置，支持 prefers-reduced-motion

**globals.css**: 全局样式
- 技术细节: Tailwind CSS 基础层 + 深色/浅色主题 CSS 变量

**template.tsx**: 路由模板（页面过渡）
- 技术细节: 客户端组件，对每个页面单独渲染
- 导出: default function Template({ children })
- 核心功能: 包裹 PageTransition 组件实现路由切换动画
- 动画效果: 淡入淡出 + 纵向微位移 (~250ms)

### 核心页面 (6个)

**page.tsx**: 首页（产品介绍精简版）
- 技术细节: Hero + 核心特性(6个) + 内容入口卡片 + CTA
- 导出: default function HomePage()
- 内容来源: @/components/landing 的 Hero/FeaturesSection + ContentHubCards
- 代码行数: ~70行

**articles/page.tsx**: 文章列表页
- 技术细节: ResourceListPage基础组件 + ArticleListCard
- 路由: /articles
- 筛选器: CompactFilterToolbar（时间/域名/语言/评分/来源/排序）
- 数据源: GET /api/resources?type=article

**podcasts/page.tsx**: 播客列表页
- 技术细节: ResourceListPage基础组件 + ResourceCard
- 路由: /podcasts
- 布局: 网格(1-2-3列响应式)
- 数据源: GET /api/resources?type=podcast

**tweets/page.tsx**: 推文列表页
- 技术细节: ResourceListPage基础组件 + TweetCard
- 路由: /tweets
- 布局: 单栏列表
- 数据源: GET /api/resources?type=tweet

**videos/page.tsx**: 视频列表页
- 技术细节: ResourceListPage基础组件 + ResourceCard
- 路由: /videos
- 布局: 网格(1-2-3列响应式)
- 数据源: GET /api/resources?type=video

**featured/page.tsx**: 精选内容页（日报 + 周报）
- 技术细节: 客户端组件，双区块展示日报和周报
- 路由: /featured
- 数据源: GET /api/digest/today, GET /api/digest/week
- 功能: 同格式展示当日和上周精选内容

### Admin 后台管理 (详见 admin/CLAUDE.md)

**admin/**: 密码保护的运维监控面板
- 路由前缀: /admin/*
- 保护机制: Cookie 认证 (middleware.ts)
- 密码: 环境变量 ADMIN_PASSWORD
- 页面: login, sources, scheduler, system, logs

### 详情页面 (1个)

**resources/[id]/page.tsx**: 资源详情页
- 技术细节: 客户端组件，动态路由参数
- 路由: /resources/:id
- 功能: 单个资源的详细展示 + 深度研究

### 其他页面 (3个)

**feeds/page.tsx**: RSS订阅页
- 技术细节: RSS链接生成和复制
- 路由: /feeds
- 功能: 多维度订阅分类

**stats/page.tsx**: 统计数据页
- 技术细节: 核心指标仪表板 + 图表
- 路由: /stats
- 数据源: GET /api/stats

**landing/page.tsx**: 产品介绍页（完整版）
- 技术细节: Hero + LogoBar + Problem + Features + HowItWorks + Testimonials + Pricing + FAQ + FinalCTA + Footer
- 路由: /landing
- 状态: 保留但不在主导航显示

### 设计系统展示页 (2个)

**neumorphic-showcase/page.tsx**: 微拟物设计展示
- 路由: /neumorphic-showcase
- 状态: 保留但不在主导航显示

**design-system/page.tsx**: 设计系统文档
- 路由: /design-system
- 状态: 保留但不在主导航显示

### 错误处理页面 (1个)

**not-found.tsx**: 自定义 404 错误页面
- 技术细节: Next.js not-found 边界组件
- 功能: 友好的 404 错误展示，带返回首页链接
- 样式: 大号 404 文字、渐变背景

## 架构设计

### 公共逻辑复用

**config/resource-types.ts**: 资源类型配置（约60行）
- 职责: 定义4种资源类型的元数据
- 导出: RESOURCE_TYPES, getResourceType, getAllResourceTypes
- 复用方: 导航栏、列表页、ContentHubCards
- 单一真相源: 避免硬编码重复

**components/resource-list-page.tsx**: 基础列表组件（约120行）
- 职责: 筛选器 + 无限滚动 + 错误处理 + 空状态
- 导出: ResourceListPage({ resourceType, CardComponent })
- 复用方: articles/podcasts/tweets/videos 4个页面
- 代码复用率: 85%

### 页面架构模式

```
首页 (/)
├── Hero Section (from @/components/landing)
├── FeaturesSection (from @/components/landing)
├── ContentHubCards (from @/components)
└── CTA

独立列表页 (/articles, /podcasts, /tweets, /videos)
├── 页面头部（标题 + 描述）
└── ResourceListPage
    ├── CompactFilterToolbar
    ├── InfiniteScroll
    └── CardComponent (ArticleListCard/TweetCard/ResourceCard)
```

## 依赖关系

### 内部依赖
- **from @/components/landing**: Hero, FeaturesSection, 配置数据
- **from @/components**: ResourceListPage, ContentHubCards, Footer, Card组件
- **from @/config**: RESOURCE_TYPES
- **from @/lib**: cn(), motion presets

### 外部依赖
- Next.js 14 (App Router)
- React 18
- Framer Motion
- Lucide React

## 变更日志

### 2026-01-12 - Admin 后台管理系统
- ✅ 创建 middleware.ts 路由保护（/admin/* 密码保护）
- ✅ 创建 admin/login 登录页面
- ✅ 创建 admin/layout.tsx 侧边栏布局
- ✅ 迁移 sources 页面到 admin/sources（增强版）
- ✅ 创建 admin/scheduler 调度器状态页面
- ✅ 创建 admin/system 系统健康页面
- ✅ 创建 admin/logs 采集日志页面
- ✅ 从导航栏移除"信号源"入口
- ✅ 添加手动触发采集功能
- ✅ 后端新增 /api/sources/trigger, /api/stats/scheduler, /api/stats/system 端点

### 2025-01-10 - 删除 Signals 模块
- ✅ 删除 app/signals/ 目录（信号详情页）
- ✅ 删除 app/api/signals/ 目录（API 代理）
- ✅ 删除 components/deep-research-button.tsx（深度研究按钮）
- ✅ 删除 next.config.js 中的 signals rewrite 规则
- ✅ 统一使用 resources 作为唯一内容模型

### 2025-01-10 - 系统优化（页面性能 + 深度研究 + 精选页面）
- ✅ 页面性能优化: 删除重复的 page-transition.tsx
- ✅ Spring动画优化: pageTransition (stiffness: 300, damping: 25)
- ✅ AnimatePresence模式: wait → sync
- ✅ 精选页面创建: /featured 展示日报 + 周报
- ✅ 导航栏更新: "周刊" → "精选"
- ✅ 路由变更: /newsletters → /featured

### 2025-01-10 - 系统优化（代码清理 + UX 增强）
- ✅ 删除未使用代码: lib/use-resource-list.ts, hooks/use-resource-list.ts, page-archive.tsx
- ✅ 创建 not-found.tsx 自定义404页面
- ✅ layout.tsx 集成 Footer + Toaster (sonner)

### 2025-01-09 - 页面架构重组
- ✅ 首页从457行资源聚合页精简为70行产品介绍页（-85%）
- ✅ 创建4个独立内容页面: /articles, /podcasts, /tweets, /videos
- ✅ 提取公共逻辑: useResourceList hook (150行)
- ✅ 创建配置中心: resource-types.ts (60行)
- ✅ 创建基础列表组件: ResourceListPage (120行)
- ✅ 导航栏精简: 从9项减少到6项
- ✅ 备份原首页: page-archive.tsx
- ✅ 代码复用率: 从0%提升到85%
- ✅ SEO优化: 4个独立页面可被搜索引擎独立索引

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
