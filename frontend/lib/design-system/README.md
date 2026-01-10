# Signal Hunter 设计系统

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

从 Figma 提取的颜色：

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 背景 | `#FFFFFF`, `#F8F9F7` | 浅色背景 |
| 深色背景 | `#161818`, `#002B31` | 深色模式背景 |
| 主文字 | `#CDCBFF` | 品牌淡紫（标题） |
| 次要文字 | `#544A2E`, `#68706F` | 正文、辅助文字 |
| 边框 | `rgba(186, 196, 192, 0.2)` | 默认边框 |
| 品牌色 | `#6258FF` → `#E06AB2` → `#FB8569` | 渐变色 |

### 间距系统

基于 8px 基准网格：

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

## 组件使用示例

### Button

```jsx
import { Button } from '@/design-system/components/Button'

// 主要按钮
<Button variant="primary" onClick={handleClick}>
  提交
</Button>

// 次要按钮
<Button variant="secondary" leftIcon={<Icon />}>
  取消
</Button>

// 加载状态
<Button loading>
  处理中...
</Button>
```

### Card

```jsx
import { Card, CardHeader, CardTitle, CardContent } from '@/design-system'

<Card hoverable>
  <CardHeader>
    <CardTitle>标题</CardTitle>
  </CardHeader>
  <CardContent>
    内容...
  </CardContent>
</Card>
```

### Badge

```jsx
import { Badge, ScoreBadge } from '@/design-system'

<Badge color="primary">标签</Badge>
<ScoreBadge score={4.5} maxScore={5} />
```

### Tag

```jsx
import { Tag, TagGroup } from '@/design-system'

<TagGroup>
  <Tag color="primary">React</Tag>
  <Tag removable onRemove={() => {}}>TypeScript</Tag>
</TagGroup>
```

## Hooks 使用示例

### useTheme

```jsx
import { useTheme } from '@/design-system/hooks/useTheme'

function Header() {
  const { resolvedTheme, toggleTheme } = useTheme()
  return (
    <button onClick={toggleTheme}>
      切换到 {resolvedTheme === 'dark' ? '浅色' : '深色'} 模式
    </button>
  )
}
```

### useMediaQuery

```jsx
import { useIsMobile } from '@/design-system/hooks/useMediaQuery'

function Sidebar() {
  const isMobile = useIsMobile()
  return isMobile ? <MobileNav /> : <DesktopNav />
}
```

## 集成到 Tailwind

设计系统 Tokens 已集成到 `tailwind.config.ts`，可直接使用：

```jsx
// 使用自定义颜色
<div className="bg-primary text-text-primary">

// 使用自定义间距
<div className="p-container-lg gap-component-md">

// 使用自定义圆角
<div className="rounded-lg rounded-full">
```

## 更新日志

- **2025-01-02**: 初始版本，从 Figma 设计稿提取
  - 颜色系统: 16+ 颜色值
  - 组件: Button, Input, Card, Badge, Tag
  - Hooks: useTheme, useMediaQuery
