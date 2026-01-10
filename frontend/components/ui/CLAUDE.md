# components/ui/
> L2 | 父级: ../CLAUDE.md

## 成员清单

### 基础交互组件（已升级微拟物设计）

**button.tsx**: 微拟物按钮组件，提供渐变背景 + 三层立体阴影系统
- 技术细节: 内联样式实现 gradient + box-shadow，useState 管理 hover 状态
- 变体: default | primary | destructive | accent | secondary | outline | ghost | link
- 尺寸: sm | default | md | lg | xl | icon
- 微交互: hover:scale-[1.02], active:scale-[0.97]
- 关键参数: variant, size, asChild

**card.tsx**: 微拟物卡片组件，提供多种阴影变体
- 技术细节: CSS 变量驱动的阴影系统，支持 hover scale 效果
- 变体: default | raised (凸起) | inset (内凹) | outline (边框)
- 子组件: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- 微交互: hover:scale-[1.01], active:scale-[0.98]
- 关键参数: variant

**input.tsx**: 微拟物输入框组件，内凹阴影效果
- 技术细节: CSS 变量 --shadow-inset，聚焦时增强为 --shadow-inset-lg
- 样式: border-0, bg-background, rounded-2xl
- 微交互: 聚焦时 scale-[1.01]，hover 时阴影增强
- 关键参数: type (text | email | password | etc.)

**badge.tsx**: 微拟物标签组件，渐变背景 + 立体阴影
- 技术细节: 内联样式实现 gradient + box-shadow，useState 管理 hover
- 变体: default | secondary | destructive | outline
- 样式: rounded-2xl, px-3 py-1
- 微交互: hover:scale-[1.03], active:scale-[0.98]
- 关键参数: variant

### shadcn/ui 基础组件（30个，保持默认设计）

**label.tsx**: 表单标签组件
**form.tsx**: 表单容器组件
**select.tsx**: 下拉选择器
**checkbox.tsx**: 复选框
**radio-group.tsx**: 单选按钮组
**switch.tsx**: 开关切换
**textarea.tsx**: 多行文本输入

**dialog.tsx**: 对话框模态窗口
**sheet.tsx**: 侧边抽屉组件
**alert.tsx**: 警告提示组件
**sonner.tsx**: Toast 通知组件
**skeleton.tsx**: 骨架屏加载占位
**progress.tsx**: 进度条组件

**tabs.tsx**: 标签页切换
**accordion.tsx**: 手风琴折叠面板
**dropdown-menu.tsx**: 下拉菜单
**navigation-menu.tsx**: 导航菜单
**command.tsx**: 命令面板 (⌘K)
**collapsible.tsx**: 可折叠容器

**avatar.tsx**: 头像组件
**table.tsx**: 表格组件
**popover.tsx**: 气泡弹出框
**tooltip.tsx**: 工具提示
**hover-card.tsx**: 悬停卡片

**scroll-area.tsx**: 自定义滚动区域
**separator.tsx**: 分隔线
**textarea.tsx**: 多行文本框

## 设计规范

### 颜色来源
- 仅使用 globals.css 中的 CSS 变量
- 禁止硬编码颜色值
- 支持主题切换（light/dark mode）

### 圆角系统
- --radius-sm: 16px
- --radius: 20px (默认)
- --radius-md: 24px
- --radius-lg: 32px

### 阴影系统
- --shadow-raised-sm | --shadow-raised | --shadow-raised-lg | --shadow-raised-hover
- --shadow-inset-sm | --shadow-inset | --shadow-inset-lg
- --shadow-neutral | --shadow-neutral-hover

### 微交互动画
- --transition-fast: 0.15s ease
- --transition-base: 0.2s ease
- --transition-slow: 0.3s ease
- scale-hover: 1.02
- scale-active: 0.97

## 依赖关系

### 外部依赖
- react: ^18.3.0
- class-variance-authority: CVA 变体管理
- @radix-ui/*: Radix UI 原语组件

### 内部依赖
- @/lib/utils: cn() 工具函数

## 变更日志

### 2025-01-09 - 微拟物设计升级
- ✅ Button: 添加渐变背景 + 三层阴影 + 缩放微交互
- ✅ Card: 添加 variant prop (raised/inset/outline)
- ✅ Input: 应用内凹阴影，聚焦增强
- ✅ Badge: 添加渐变背景 + 立体阴影

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
