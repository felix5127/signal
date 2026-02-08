# design-system/
> L2 | 父级: ../CLAUDE.md

## 职责

基于 Figma 设计稿构建的完整设计系统，包含设计 Tokens、可复用组件和通用 Hooks。

## 目录结构

```
design-system/
├── tokens/              # 设计 Tokens
│   ├── colors.js       # 颜色系统（从 Figma 提取的 16+ 颜色）
│   ├── spacing.js      # 间距系统（8px 基准网格）
│   ├── typography.js   # 排版系统（Inter 字体，8 种尺寸）
│   ├── effects.js      # 效果系统（圆角、阴影、动效）
│   └── index.js        # Tokens 统一导出
│
├── components/         # 可复用 UI 组件
│   ├── Button.jsx      # 按钮组件（5 种变体，5 种尺寸）
│   ├── Input.jsx       # 输入框组件
│   ├── Card.jsx        # 卡片组件（含 5 个子组件）
│   ├── Badge.jsx       # 徽章组件（含 ScoreBadge）
│   ├── Tag.jsx         # 标签组件（可移除）
│   └── index.js        # 组件统一导出
│
├── hooks/             # 通用 Hooks
│   ├── useTheme.js    # 主题管理（light/dark/system）
│   ├── useMediaQuery.js # 响应式检测
│   └── index.js       # Hooks 统一导出
│
└── index.js           # 设计系统顶层导出
```

## 设计 Tokens

### 颜色系统

从 Figma 提取的颜色:

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 背景 | `#FFFFFF`, `#F8F9F7` | 浅色背景 |
| 深色背景 | `#161818`, `#002B31` | 深色模式背景 |
| 主文字 | `#CDCBFF` | 品牌淡紫（标题） |
| 次要文字 | `#544A2E`, `#68706F` | 正文、辅助文字 |
| 边框 | `rgba(186, 196, 192, 0.2)` | 默认边框 |
| 品牌色 | `#6258FF` -> `#E06AB2` -> `#FB8569` | 渐变色 |

### 间距系统

基于 8px 基准网格:

```javascript
spacing = {
  1: '4px',   // 0.5x
  2: '8px',   // 1x (基准)
  3: '12px',  // 1.5x
  4: '16px',  // 2x
  6: '24px',  // 3x
  8: '32px',  // 4x
  12: '48px', // 6x
}
```

### 排版系统

- **字体族**: Inter (优先), 系统后备字体
- **字体大小**: 10.8px ~ 103.4px (9 种尺寸)
- **字重**: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)
- **行高**: 1.35 ~ 1.72

### 圆角

```javascript
borderRadius = {
  xs: '3px',      // 小圆角
  sm: '4px',      // 中小圆角
  md: '8px',      // 中圆角
  lg: '12px',     // 大圆角
  full: '9999px', // 胶囊形
}
```

## 组件

### Button
- 5 种变体: primary, secondary, outline, ghost, link
- 5 种尺寸
- 支持 leftIcon, loading 状态

### Card
- 含 5 个子组件: Card, CardHeader, CardTitle, CardContent, CardFooter
- 支持 hoverable 属性

### Badge / ScoreBadge
- ScoreBadge 支持 score/maxScore 评分展示

### Tag / TagGroup
- 支持 removable + onRemove 回调

## Hooks

### useTheme
- 主题管理: light / dark / system
- 导出: resolvedTheme, toggleTheme

### useMediaQuery
- 响应式检测
- 导出: useIsMobile()

## Tailwind 集成

设计系统 Tokens 已集成到 `tailwind.config.ts`:

```jsx
// 自定义颜色
<div className="bg-primary text-text-primary">

// 自定义间距
<div className="p-container-lg gap-component-md">

// 自定义圆角
<div className="rounded-lg rounded-full">
```

## 变更日志

### 2025-01-02 - 初始版本
- 从 Figma 设计稿提取颜色系统 (16+ 颜色值)
- 组件: Button, Input, Card, Badge, Tag
- Hooks: useTheme, useMediaQuery

## [PROTOCOL]
变更时更新此头部，然后检查 ../CLAUDE.md
