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

**Footer.tsx**: 全局页脚组件
- 技术细节: 4列网格布局，包含产品/资源/法律链接、社交媒体图标、版权信息
- 导出: Footer()
- 消费方: app/layout.tsx
- 样式: 深色背景(bg-gray-900)、响应式网格

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

**README.md**: 组件目录说明文档
- 内容: 组件使用指南和设计说明

## 子目录

**landing/** - Landing Page 组件目录
**effects/** - 特效组件目录

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
