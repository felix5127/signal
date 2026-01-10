# lib/
> L2 | 父级: ../CLAUDE.md

## 成员清单

**utils.ts**: 工具函数库
- 技术细节: 提供 cn() classnames 合并工具函数
- 导出: cn(cls: ClassValue): string
- 依赖: clsx + tailwind-merge

**motion.ts**: Apple 级 Spring 动画预设库
- 技术细节: Framer Motion variants + Spring 物理引擎配置
- 核心哲学: Spring 弹簧 + 阻尼落定 + 物理惯性
- 导出:
  - Spring 配置: snappy, gentle, bouncy, smooth, inertia
  - 缓动曲线: appleEase, appleEaseOut, appleDecelerate
  - 动画预设: fadeInUp, fadeInDown, fadeInLeft, fadeInRight, scaleIn
  - 容器动画: staggerContainer, staggerContainerFast
  - 交互动画: hoverLift, tapScale
  - 模态框: modalOverlay, modalContent
  - 页面过渡: pageTransition
  - 装饰动画: floatAnimation, pulseGlow, bounce, blink

## 设计规范

### Spring 物理引擎配置

| 场景 | Spring 配置 | 体感时长 | 用途 |
|------|-------------|----------|------|
| **标准交互** | stiffness: 400, damping: 30 | ~200ms | 按钮、卡片 hover |
| **柔和过渡** | stiffness: 300, damping: 35 | ~350ms | 面板展开、模态框 |
| **弹性强调** | stiffness: 500, damping: 25, mass: 0.8 | ~300ms | 成功反馈、关键元素 |
| **优雅落定** | stiffness: 200, damping: 40, mass: 1.2 | ~500ms | 页面过渡、大元素移动 |
| **惯性滑动** | stiffness: 150, damping: 20, mass: 0.5 | - | 列表、轮播 |

### Apple 缓动曲线（非 Spring 场景）

- **appleEase**: `[0.25, 0.1, 0.25, 1.0]` - iOS 标准曲线
- **appleEaseOut**: `[0.22, 1, 0.36, 1]` - iOS 弹出曲线
- **appleDecelerate**: `[0, 0, 0.2, 1]` - iOS 减速曲线

### 动画时长参考

- 微交互: ~200ms (stiffness: 400, damping: 30)
- 元素进场: ~350ms (stiffness: 300, damping: 35)
- 页面切换: ~500ms (stiffness: 200, damping: 40)
- 弹性强调: ~300ms (stiffness: 500, damping: 25)

### 核心动画预设

#### 淡入上移
```typescript
fadeInUp: { opacity: 0, y: 24 } → { opacity: 1, y: 0 }
transition: { type: "spring", stiffness: 300, damping: 30 }
```

#### 弹性缩放
```typescript
scaleIn: { opacity: 0, scale: 0.9 } → { opacity: 1, scale: 1 }
transition: { type: "spring", stiffness: 400, damping: 25 }
```

#### 序列进场
```typescript
staggerContainer: { opacity: 0 } → { opacity: 1 }
transition: { staggerChildren: 0.06, delayChildren: 0.1 }
```

#### 悬浮提升
```typescript
hoverLift: { scale: 1, y: 0 } → { scale: 1.02, y: -4 }
transition: { type: "spring", stiffness: 400, damping: 25 }
```

#### 点击反馈
```typescript
tapScale: { scale: 1 } → { scale: 0.96 }
transition: { type: "spring", stiffness: 500, damping: 30 }
```

## 可访问性

### MotionConfig 配置
```tsx
<MotionConfig reducedMotion="user">
  <App />
</MotionConfig>
```

### prefers-reduced-motion 支持
- 自动检测用户系统设置
- 禁用所有动画效果
- 优先考虑用户偏好

## 依赖关系

### 外部依赖
- framer-motion: ^11.0.0
- clsx: 条件类名工具
- tailwind-merge: Tailwind 类名合并

### 内部依赖
- 无内部依赖

## 使用场景

### 全局页面过渡
- **组件**: `components/PageTransition.tsx`
- **动画**: `pageTransition` variant
- **位置**: `app/layout.tsx` 包裹 children

### 导航栏动画
- **组件**: `components/navbar.tsx`
- **动画**: Spring 物理引擎 (stiffness: 300-500)
- **效果**: 下滑进场、hover 提升、tap 缩放

### Landing Page Sections
- **组件**: `components/landing/*.tsx`
- **动画**: fadeInUp + staggerContainer
- **效果**: 序列进场、视口触发

## 变更日志

### 2025-01-09 - Apple 级 Spring 动效升级
- ✅ 升级所有动画为 Spring 物理引擎
- ✅ 添加 5 种 Spring 配置预设
- ✅ 添加 hoverLift 和 tapScale 交互动画
- ✅ 添加 modalContent 优雅落定动画
- ✅ 添加 pageTransition 页面路由过渡
- ✅ 配置 MotionConfig 支持 prefers-reduced-motion
- ✅ 升级 navbar 所有动画为 Spring

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
