# components/
> L2 | 父级: ../CLAUDE.md

## 成员清单

**navbar.tsx**: 全局导航栏组件
- 技术细节: 使用 Next.js Link/usePathname + Lucide React 图标 + Framer Motion Spring 物理引擎
- 导出: default function Navbar()
- 核心功能: 页面路由导航、Logo展示、桌面/移动端响应式菜单、Apple级Spring交互动画
- 导航项: 6项（文章/播客/推文/视频/精选/研究）- 信号源移至 /admin
- 动画配置: 下滑进场(stiffness:300,damping:30) + hover提升 + tap缩放 + 图标旋转

**page-transition.tsx**: 全局页面路由过渡组件
- 技术细节: Framer Motion AnimatePresence + usePathname + Spring 物理引擎
- 导出: PageTransition({ children })
- 核心功能: 页面切换时的淡入淡出+纵向位移过渡效果
- 动画配置: Spring物理引擎(stiffness:400,damping:30) + mode="sync"
- 消费方: app/template.tsx

**Footer.tsx**: 全局页脚组件 (Mercury 风格)
- 技术细节: 2列网格布局，统一品牌元素
- 导出: Footer()
- 消费方: app/layout.tsx
- Logo: Radar 图标 (Lucide) + Signal
- 品牌描述: "AI 驱动的技术情报分析平台，帮助你发现改变世界的技术信号。"
- 链接结构:
  - 内容: 文章、视频、播客、推文
  - 关于: 关于我们、联系方式
- 样式: 浅色背景、响应式双列布局

**Breadcrumb.tsx**: 面包屑导航组件
- 技术细节: 动态面包屑，支持链接和纯文本项
- 导出: Breadcrumb({ items })
- 消费方: 详情页面 (resources/[id])
- 样式: 小字体(text-sm)、灰色文本、蓝色hover

**BackToTop.tsx**: 返回顶部按钮组件
- 技术细节: 客户端组件 + 滚动监听 + framer-motion 显隐动画
- 导出: BackToTop()
- 消费方: 长列表页面
- 样式: 固定定位右下角、圆形蓝色按钮、Spring动画

**podcast-generator.tsx**: 播客生成组件
- 技术细节: SSE 流式进度 + 音频播放器 + 音色选择
- 导出: PodcastGenerator({ content, title, targetDuration, onComplete })
- 消费方: 研究工作台、资源详情页
- 功能: 文本转播客、进度展示、音频播放、下载

**resource-detail.tsx**: 资源详情页组件 (Mercury 风格重构)
- 技术细节: Mercury.com 浅色系设计，Header 全宽 + Content Row 两栏布局
- 导出: ResourceDetail({ resource, relatedResources })
- 消费方: app/resources/[id]/page.tsx（非播客类型）
- 功能: 面包屑导航、标签行、AI 侧边栏三卡片、响应式布局
- 颜色: #FBFCFD (背景), #1E3A5F (主色), #272735/#6B6B6B/#9A9A9A (文字)

**tweet-card.tsx**: 推文卡片组件 (Mercury 风格)
- 技术细节: 卡片内展开全文，无需跳转详情页
- 导出: TweetCard({ tweet })
- 消费方: app/tweets/page.tsx
- 设计规范:
  - "显示全文"按钮: chevron-down 图标 + 文字
  - 按钮颜色: #1E3A5F, 字号 13px
  - 卡片间距: 16px
- 交互: 点击展开/收起推文全文

**article-list-card.tsx**: 文章列表卡片组件 (Mercury 风格)
- 技术细节: 简洁卡片布局，支持标题、摘要、标签
- 导出: ArticleListCard({ article })
- 消费方: app/articles/page.tsx

**resource-filter-bar.tsx**: 筛选栏组件
- 技术细节: 时间/分类/排序/精选开关

**pagination.tsx**: 分页组件

**score-badge.tsx**: 评分徽章组件（支持精选标记）

**markdown-renderer.tsx**: Markdown 渲染器

**daily-news-tab.tsx**: 每日新闻 Tab（按日期分组、无限滚动）

**weekly-report-tab.tsx**: 每周观察 Tab

**main-points.tsx**: 主要观点组件（可展开/收起）

**key-quotes.tsx**: 金句组件（引用样式）

**tag-list.tsx**: 标签列表组件（可点击）

## 子目录

**landing/** - Landing Page 组件目录
**effects/** - 特效组件目录
**detail/** - 详情页子组件目录（见 detail/CLAUDE.md）
**podcast/** - 播客详情页组件目录（见 podcast/CLAUDE.md）

## 设计规范

### Apple 级 Spring 动画应用

| 组件 | 动画类型 | Spring 配置 | 体感时长 |
|------|---------|-------------|----------|
| **navbar** | 下滑进场 | stiffness: 300, damping: 30 | ~250ms |
| **navbar** | Logo hover | stiffness: 400, damping: 25 | ~200ms |
| **navbar** | 菜单项 hover | stiffness: 400, damping: 30 | ~200ms |
| **navbar** | 菜单按钮 tap | stiffness: 500, damping: 30 | ~180ms |
| **navbar** | 移动菜单展开 | stiffness: 300, damping: 35 | ~350ms |
| **page-transition** | 页面切换 | stiffness: 400, damping: 30 | ~250ms |

### 交互动画模式

- **hoverLift**: 悬浮时轻微上移(y: -2) + 缩放(1.02)
- **tapScale**: 点击时快速缩小(0.96-0.92) + 弹性恢复
- **图标旋转**: 菜单/关闭图标切换时旋转动画(-90° ↔ 90°)

## 依赖关系

### 外部依赖
- framer-motion: ^11.0.0
- next: Link, usePathname
- lucide-react: 图标组件库

### 内部依赖
- @/lib/motion: Spring 动画预设配置
- @/lib/utils: cn() classnames 工具函数

## 使用场景

### 全局导航
- **组件**: `navbar.tsx`
- **位置**: 被 `app/layout.tsx` 消费
- **功能**: 所有页面顶部固定显示的导航栏

### 页面过渡
- **组件**: `page-transition.tsx`
- **位置**: 被 `app/template.tsx` 消费
- **功能**: 包裹页面内容实现路由切换动画
- **特性**: mode="sync" 确保快速切换，initial={false} 避免首次加载动画

## 可访问性

- 支持 prefers-reduced-motion（通过全局 MotionConfig）
- 键盘导航支持（focus:ring 样式）
- 移动端响应式设计（md:breakpoint）
- 语义化 HTML（nav, button, link）

## 变更日志

### 2026-01-27 - Footer 品牌统一 & 推文卡片优化
- Footer.tsx 品牌统一：Radar 图标 + 统一品牌描述
- Footer.tsx 链接结构简化：4列 → 2列（内容/关于）
- tweet-card.tsx 新增"显示全文"按钮设计规范
- 推文卡片间距调整为 16px

### 2026-01-26 - Mercury 风格资源详情页重构
- 重构 resource-detail.tsx 为 Mercury.com 浅色系风格
- 新增 detail/ai-summary-card.tsx AI 摘要卡片组件
- 新增 detail/ai-assistant-card.tsx AI 研究助手卡片组件
- 新增 detail/related-content-card.tsx 相关内容卡片组件
- 实现 Header 全宽 + Content Row 两栏布局 (70% + 380px)
- 面包屑导航: 首页 > 文章详情 > 当前文章
- 标签尺寸统一: 72px x 28px
- 正文排版: 行高 1.8, 子标题 18px/600

### 2026-01-18 - 详情页体验改进
- 创建 detail/ 子目录（FeaturedReason, AuthorInfo, AISidebar, ContentArea）
- 创建 podcast/ 子目录（AudioPlayer, ChapterOverview, TranscriptView, QARecap, ContentTabs, PodcastDetail）
- 重构 resource-detail.tsx 为左右布局（桌面）+ 上下布局（移动端）
- 播客详情页特殊设计：4 Tab 结构（Show Notes/Chapters/Transcript/Q&A）

### 2026-01-12 - Admin 后台管理系统
- ✅ navbar.tsx 移除"信号源"导航入口（移至 /admin/sources）
- ✅ 导航项从 7 项减至 6 项

### 2025-01-10 - 页面过渡优化
- ✅ 创建 page-transition.tsx 组件
- ✅ 创建 app/template.tsx 路由级过渡模板
- ✅ 优化动画配置: stiffness: 400, damping: 30 (~250ms)
- ✅ 使用 mode="sync" 实现快速页面切换
- ✅ 添加全局 MotionConfig 支持 prefers-reduced-motion

### 2025-01-10 - 系统优化（代码清理 + UX 增强）
- ✅ 删除未使用代码: lib/use-resource-list.ts, hooks/use-resource-list.ts, page-archive.tsx
- ✅ 创建 app/not-found.tsx 自定义404页面
- ✅ 创建 Footer.tsx 全局页脚组件
- ✅ 创建 Breadcrumb.tsx 面包屑导航组件
- ✅ 创建 BackToTop.tsx 返回顶部按钮组件
- ✅ 集成 Toast 通知系统 (sonner)
- ✅ L3 头部注释标准化

### 2025-01-09 - Apple 级 Spring 动效升级
- ✅ navbar.tsx 所有动画升级为 Spring 物理引擎
- ✅ 添加 hover 提升 + tap 缩放交互反馈
- ✅ 移动端菜单展开动画优化
- ✅ L3 头部注释标准化

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
