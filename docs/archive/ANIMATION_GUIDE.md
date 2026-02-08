# UI 动效增强指南

## 📦 已安装依赖

```bash
framer-motion@^11.0.0  # 高性能 React 动画库
react-icons@^5.0.0      # 超过 100,000+ 图标库
```

---

## 🎨 动效组件库

### **1. 页面过渡组件** (`components/page-transition.tsx`)

#### `PageTransition`
页面级淡入淡出动画

```tsx
import { PageTransition } from '@/components/page-transition'

export default function MyPage() {
  return (
    <PageTransition>
      <div>页面内容</div>
    </PageTransition>
  )
}
```

**效果**：从下方 20px 淡入滑入，持续 0.3s

---

#### `CardEnterAnimation`
卡片进入动画（带延迟）

```tsx
import { CardEnterAnimation } from '@/components/page-transition'

{items.map((item, index) => (
  <CardEnterAnimation key={item.id} delay={index * 0.05}>
    <ResourceCard data={item} />
  </CardEnterAnimation>
))}
```

**参数**：
- `delay`: 延迟时间（秒），默认 0
- `className`: 自定义类名

**效果**：从下方 30px + 缩放 0.95 → 1.0，持续 0.4s

---

#### `FadeInAnimation`
轻量级淡入动画

```tsx
import { FadeInAnimation } from '@/components/page-transition'

<FadeInAnimation delay={0.2}>
  <div>淡入元素</div>
</FadeInAnimation>
```

**效果**：纯透明度 0 → 1，持续 0.5s

---

#### `SlideInAnimation`
侧边滑入动画

```tsx
import { SlideInAnimation } from '@/components/page-transition'

<SlideInAnimation direction="left" delay={0.3}>
  <Sidebar />
</SlideInAnimation>
```

**参数**：
- `direction`: `'left' | 'right' | 'top' | 'bottom'`，默认 `'right'`

**效果**：从指定方向滑入 50px，持续 0.4s

---

### **2. 动画资源卡片** (`components/animated-resource-card.tsx`)

#### `AnimatedResourceCard`
带 hover 和进入动画的资源卡片

```tsx
import { AnimatedResourceCard } from '@/components/animated-resource-card'

{resources.map((resource, index) => (
  <AnimatedResourceCard
    key={resource.id}
    resource={resource}
    index={index}
    className="w-full"
  />
))}
```

**动效**：
- 进入：淡入 + 上移 + 缩放（0.4s）
- Hover：上浮 8px + 放大 1.02 倍
- 点击：缩小 0.98

---

#### `AnimatedListItem`
列表项动画

```tsx
import { AnimatedListItem } from '@/components/animated-resource-card'

{items.map((item, index) => (
  <AnimatedListItem key={item.id} index={index}>
    <ArticleListItem data={item} />
  </AnimatedListItem>
))}
```

**效果**：从左侧 -20px 淡入，持续 0.3s

---

### **3. 社交图标组件** (`components/social-icons.tsx`)

#### `SocialIcon`
单个社交图标

```tsx
import { SocialIcon } from '@/components/social-icons'

<SocialIcon
  platform="twitter"
  href="https://twitter.com/user"
  size={24}
  showLabel={false}
/>
```

**支持的平台**：
- `twitter`, `github`, `linkedin`, `youtube`
- `instagram`, `facebook`, `telegram`, `discord`
- `reddit`, `hackernews`

**动效**：Hover 时上浮 2px + 放大 1.1

---

#### `SocialIcons`
社交图标列表

```tsx
import { SocialIcons, COMMON_SOCIAL_ICONS } from '@/components/social-icons'

<SocialIcons
  icons={[
    COMMON_SOCIAL_ICONS.twitter('https://twitter.com/user'),
    COMMON_SOCIAL_ICONS.github('https://github.com/user'),
  ]}
  size={24}
  className="flex space-x-4"
/>
```

**效果**：依次淡入，每个延迟 0.1s

---

### **4. 增强导航栏** (`components/navbar.tsx`)

已集成 Framer Motion 动效：

- **导航栏入场**：从顶部滑入（y: -100 → 0）
- **Logo hover**：放大 1.05 + 旋转 5 度
- **菜单项 hover**：上浮 2px
- **汉堡菜单切换**：图标旋转动画
- **移动端菜单展开**：高度动画 + 依次滑入

---

## 🎯 使用场景示例

### **场景 1：卡片网格**
```tsx
import { CardEnterAnimation } from '@/components/page-transition'

<div className="grid grid-cols-3 gap-4">
  {cards.map((card, index) => (
    <CardEnterAnimation key={card.id} delay={index * 0.05}>
      <MyCard data={card} />
    </CardEnterAnimation>
  ))}
</div>
```

### **场景 2：列表加载**
```tsx
import { AnimatedListItem } from '@/components/animated-resource-card'

{items.map((item, index) => (
  <AnimatedListItem key={item.id} index={index}>
    <MyListItem data={item} />
  </AnimatedListItem>
))}
```

### **场景 3：页脚社交图标**
```tsx
import { SocialIcons, COMMON_SOCIAL_ICONS } from '@/components/social-icons'

<footer>
  <SocialIcons
    icons={[
      COMMON_SOCIAL_ICONS.twitter('https://twitter.com/signalhunter'),
      COMMON_SOCIAL_ICONS.github('https://github.com/signalhunter'),
    ]}
  />
</footer>
```

---

## ⚡ 性能优化建议

1. **延迟计算**：使用 `Math.min(index * 0.05, 0.5)` 限制最大延迟
2. **GPU 加速**：优先使用 `transform` 和 `opacity`（GPU 属性）
3. **避免重排**：不要动画 `width/height`，使用 `scale` 替代
4. **批量动画**：使用 `<AnimatePresence>` 管理退出动画

---

## 🎨 自定义动画

```tsx
import { motion } from 'framer-motion'

<motion.div
  initial={{ opacity: 0, scale: 0.8 }}
  animate={{ opacity: 1, scale: 1 }}
  exit={{ opacity: 0, scale: 0.8 }}
  transition={{
    duration: 0.3,
    ease: [0.4, 0, 0.2, 1], // 自定义贝塞尔曲线
  }}
>
  {children}
</motion.div>
```

---

## 📊 缓动函数推荐

| 缓动 | 用途 | 值 |
|------|------|-----|
| `easeInOut` | 通用动画 | `[0.4, 0, 0.2, 1]` |
| `easeOut` | 进入动画 | `[0, 0, 0.2, 1]` |
| `easeIn` | 退出动画 | `[0.4, 0, 1, 1]` |
| `spring` | 弹性效果 | `{ type: 'spring', stiffness: 300 }` |

---

**Felix，现在整个项目已具备专业级 UI 动效系统！** 🚀
