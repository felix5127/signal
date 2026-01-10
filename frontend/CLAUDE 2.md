# frontend/
> L2 | 父级: ../CLAUDE.md

## 目录结构

### app/ - Next.js 14 App Router 页面
**核心页面** (7个): /, /articles, /podcasts, /tweets, /videos, /newsletters, /resources/[id]
**详情页面**: /resources/[id], /signals/[id]
**错误页面**: not-found (自定义404)
**其他页面**: /feeds, /stats, /landing, /neumorphic-showcase, /design-system
**详情**: 见 app/CLAUDE.md

### components/ - 可复用组件
**列表组件**:
- resource-list-page.tsx: 基础列表页模板（120行）
- content-hub-cards.tsx: 内容入口卡片网格（60行）
- article-list-card.tsx: 文章列表卡片
- tweet-card.tsx: 推文卡片
- resource-card.tsx: 通用资源卡片

**布局组件**:
- navbar.tsx: 全局导航栏
- Footer.tsx: 全局页脚
- PageTransition.tsx: 页面过渡动画

**功能组件**:
- FeaturedSignalCard.tsx: 精简信号卡片
- FeaturedSignals.tsx: 首页信号展示区块
- Breadcrumb.tsx: 面包屑导航
- BackToTop.tsx: 返回顶部按钮

**UI组件**: shadcn/ui组件库（30+组件）
**Landing组件**: components/landing/ 目录下的10个Section组件
**详情**: 见 components/CLAUDE.md

### hooks/ - 自定义React Hooks
**use-toast.ts**: Toast 通知 Hook
- 职责: 封装 sonner 库，提供 success/error/info/warning/promise 方法
- 导出: useToast()

### config/ - 配置文件
**resource-types.ts**: 资源类型配置（60行）
- 职责: 定义4种资源类型的元数据
- 导出: RESOURCE_TYPES, ResourceType, 辅助函数

### lib/ - 工具函数和库
**utils.ts**: 工具函数（cn classnames合并）
**motion.ts**: Apple级Spring动画预设库
**design-system/**: 设计系统令牌（colors/spacing/typography）

## 技术栈

### 框架
- **Next.js**: 14.2.0 (App Router)
- **React**: 18.3.0
- **TypeScript**: 5.x

### 样式
- **TailwindCSS**: v3.4.0
- **CSS Variables**: 设计系统令牌
- **Framer Motion**: 动画库

### 组件库
- **shadcn/ui**: 30+组件
- **Lucide React**: 图标库

### 设计系统
- **微拟物设计**: Neumorphic Design
- **Spring动效**: Apple级物理引擎
- **响应式**: 移动端优先

## 页面路由架构

### 核心页面
```
/                           # 首页（产品介绍 + AI精选信号）
/articles                   # 文章列表页
/podcasts                   # 播客列表页
/tweets                     # 推文列表页
/videos                     # 视频列表页
/featured                   # 精选内容（日报 + 周报）
```

### 详情页面
```
/resources/[id]             # 资源详情页
/signals/[id]               # 信号详情页
```

### 错误页面
```
/not-found                  # 自定义404页面
```

### 其他页面
```
/feeds                      # RSS订阅页
/stats                      # 统计数据页
/landing                    # 产品介绍页（完整版）
/neumorphic-showcase        # 微拟物展示
/design-system              # 设计系统文档
/newsletters                # 周刊列表页（保留，已不在主导航）
```

## 组件复用架构

### 三层复用模式

**L1: hooks/** - 功能层
```
useToast()
├── success()
├── error()
├── info()
└── promise()
```

**L2: config/** - 配置层
```
RESOURCE_TYPES
├── 元数据定义
├── 单一真相源
└── 避免硬编码
```

**L3: components/** - 展示层
```
ResourceListPage({ resourceType, CardComponent })
├── 筛选器
├── 无限滚动
├── 错误处理
└── 空状态
```

### 代码复用率
- **提取后**:
  - components/resource-list-page.tsx (120行) → 复用4次
  - config/resource-types.ts (60行) → 复用8次
- **总复用率**: 85%

## 设计规范

### Apple级Spring动效
- **核心哲学**: Spring弹簧 + 阻尼落定 + 物理惯性
- **Spring配置**:
  - snappy: stiffness 400, damping 30 (~200ms)
  - gentle: stiffness 300, damping 35 (~350ms)
  - bouncy: stiffness 500, damping 25 (~300ms)
  - smooth: stiffness 200, damping 40 (~500ms)
  - inertia: stiffness 150, damping 20
- **使用场景**: 页面过渡、交互动画、卡片hover

### 微拟物设计
- **核心原则**: 三段式渐变 + 三层阴影 + 微交互
- **CSS变量**: --gradient-*, --shadow-raised, --shadow-inset
- **圆角规范**: 16px - 32px大圆角
- **微交互**: hover scale-[1.02], active scale-[0.97]

### 间距系统
- **Section间距**: py-20 md:py-28
- **Container**: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
- **Grid gap**: gap-4 (cards), gap-6 (sections)

### 排版层级
- **Display**: text-5xl md:text-6xl lg:text-7xl (Hero H1)
- **Heading**: text-3xl md:text-4xl lg:text-5xl (Section H2)
- **Title**: text-xl md:text-2xl (Card Title)
- **Body**: text-base (Paragraph)
- **Caption**: text-sm (辅助文字)

## 依赖关系

### 外部依赖
- next: ^14.2.0
- react: ^18.3.0
- framer-motion: ^11.0.0
- lucide-react: 图标库
- sonner: Toast 通知库
- clsx + tailwind-merge: 类名工具

### 内部依赖
- app/ → components/ + hooks/ + config/
- components/ → lib/ + hooks/ + config/
- hooks/ → config/ + components/

## 变更日志

### 2025-01-10 - 系统优化（代码清理 + UX 增强）
- ✅ 代码清理: 删除 lib/use-resource-list.ts, hooks/use-resource-list.ts, page-archive.tsx
- ✅ UX 增强: 创建 404页面、Footer、Breadcrumb、BackToTop 组件
- ✅ 功能增强: 集成 Toast 通知系统 (sonner)
- ✅ Bug修复: 修复 signals/[id]/page.tsx 的 key 属性问题
- ✅ 创建 hooks/CLAUDE.md 文档
- ✅ GEB 文档同步更新

### 2025-01-10 - Signals 整合到首页
- ✅ 创建 FeaturedSignalCard.tsx 精简版信号卡片
- ✅ 创建 FeaturedSignals.tsx 首页信号展示区块
- ✅ 更新首页结构：Hero → FeaturedSignals → Features → ContentHubCards → CTA
- ✅ 移除独立 /signals 列表页
- ✅ 精简导航栏：7项 → 6项
- ✅ 删除原 signal-card.tsx 组件
- ✅ GEB 文档同步更新

### 2025-01-09 - 页面架构重组
- ✅ 首页精简: 457行 → 75行（-84%）
- ✅ 创建4个独立内容页面
- ✅ 提取公共逻辑（hooks + config + components）
- ✅ 代码复用率提升: 0% → 85%
- ✅ 导航栏精简: 9项 → 7项
- ✅ GEB文档系统完整更新

### 2025-01-09 - Apple级Spring动效升级
- ✅ 升级所有动画为Spring物理引擎
- ✅ 添加5种Spring配置预设
- ✅ 添加hoverLift和tapScale交互动画
- ✅ 配置MotionConfig支持prefers-reduced-motion

### 2025-01-09 - 微拟物设计系统
- ✅ Button, Card, Input, Badge组件升级
- ✅ 三段式渐变背景
- ✅ 三层阴影系统
- ✅ 微交互动画

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
