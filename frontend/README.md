# Frontend - AI Signal Hunter

面向超级个体的技术情报分析系统前端应用。基于 Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui，提供优雅的信号浏览和筛选体验。

## 架构概述

采用 **Next.js 14 App Router** 架构，主要使用 Server Components 实现服务端渲染，仅在必要交互场景使用 Client Components。数据获取通过 SWR 实现自动缓存和重新验证。

## 文件清单

### 应用页面
- `app/layout.tsx` - 根布局，定义全局样式和元数据
- `app/page.tsx` - Dashboard 主页（Server Component），展示信号列表
- `app/signals/[id]/page.tsx` - 信号详情页（Server Component）
- `app/resources/[id]/page.tsx` - 资源详情页（Server Component），BestBlogs 风格
- `app/error.tsx` - 全局错误边界
- `app/loading.tsx` - 全局加载状态
- `app/not-found.tsx` - 404 页面

### UI 组件
- `components/ui/button.tsx` - 按钮组件（shadcn/ui）
- `components/ui/card.tsx` - 卡片组件
- `components/ui/badge.tsx` - 徽章组件
- `components/ui/skeleton.tsx` - 骨架屏
- `components/ui/select.tsx` - 选择器
- `components/ui/separator.tsx` - 分隔线

### 业务组件
- `components/signal-card.tsx` - 信号卡片（Client Component）
- `components/filter-bar.tsx` - 筛选栏（Client Component）
- `components/update-indicator.tsx` - 实时更新指示器（Client Component）
- `components/star-rating.tsx` - 星级评分展示
- `components/markdown-renderer.tsx` - Markdown 渲染器
- `components/daily-news-tab.tsx` - 每日新闻 Tab 页（按日期分组）
- `components/weekly-report-tab.tsx` - 每周观察 Tab 页
- `components/deep-research-button.tsx` - 深度研究按钮
- `components/main-points.tsx` - 主要观点组件（可展开/收起）
- `components/key-quotes.tsx` - 金句组件（引用样式）
- `components/tag-list.tsx` - 标签列表组件（可点击）

### 工具库
- `lib/api.ts` - API 客户端封装（fetch + 类型安全）
- `lib/types.ts` - TypeScript 类型定义
- `lib/utils.ts` - 工具函数（cn, formatRelativeTime 等）

### 配置文件
- `package.json` - 依赖管理（pnpm）
- `tsconfig.json` - TypeScript 配置
- `next.config.js` - Next.js 配置
- `tailwind.config.ts` - Tailwind CSS 配置
- `postcss.config.js` - PostCSS 配置
- `Dockerfile` - 前端容器镜像
- `.env.local.example` - 环境变量模板

### 静态资源
- `public/favicon.ico` - 网站图标
- `public/logo.svg` - Logo

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
