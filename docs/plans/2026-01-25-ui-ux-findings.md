# UI/UX Pro Max 重构 - 发现与研究

> 关联计划: 2026-01-25-ui-ux-pro-max-redesign.md

## 现状分析

### 当前设计系统问题

1. **CSS 变量系统混乱** (3套并存)
   - Web 风格设计变量 (--ds-*)
   - 原有 Figma 设计系统 (--color-*, --bg-*, --text-*)
   - HSL/OKLCH 变量系统 (--background, --foreground, --primary)
   - 微拟物设计系统 (--shadow-raised, --gradient-*)

2. **组件风格不一致**
   | 组件 | 当前风格 | 问题 |
   |-----|---------|------|
   | button.tsx | 微拟物 (gradient + 复杂阴影) | 过于复杂 |
   | card.tsx | 微拟物 (shadow variants) | 不够简洁 |
   | resource-card.tsx | Web 风格 (--ds-* 变量) | 与其他组件不一致 |
   | navbar.tsx | 硬编码 (gray-200, purple-600) | 与设计系统脱节 |
   | Hero.tsx | HSL 变量 (--primary) | 背景效果复杂 |

3. **文件清单**
   - `frontend/app/globals.css` - 358 行，变量混乱
   - `frontend/app/globals-neumorphic.css` - 158 行，微拟物系统
   - `frontend/components/ui/button.tsx` - 135 行
   - `frontend/components/ui/card.tsx` - 119 行
   - `frontend/components/navbar.tsx` - 194 行

## Mercury 风格研究

### 从 mercury.com 提取的设计特点

1. **配色**
   - 中性主题：#fbfcfd (背景)、#272735 (文本)
   - 绿色主题：#f1f7f3 (背景)、#188554 (主色)
   - 强调色：#8a753c (琥珀金)

2. **圆角**
   - 大圆角：2rem (32px) 到 2.5rem (40px)
   - 这是 Mercury 风格的标志性特点

3. **阴影**
   - 极淡，几乎无阴影
   - 依靠边框和背景色区分层级

4. **玻璃效果**
   - 70% 透明度 + blur(12-16px)
   - 使用克制，主要用于导航栏

5. **字体**
   - 自定义 Arcadia 字体
   - 字重：标题 500，正文 400
   - 我们使用 Geist 作为替代

## 技术决策

### 保留的内容
- Framer Motion 动画库
- shadcn/ui 组件结构
- Tailwind CSS 框架
- 现有的组件架构

### 需要重构的内容
- CSS 变量系统 → 统一为 Mercury 风格
- 组件样式 → 简化，去除复杂阴影和渐变
- 颜色硬编码 → 使用 CSS 变量

### 新增的内容
- 玻璃效果工具类
- 统一的圆角规范
- 骨架屏加载组件

## 参考资源

- Mercury.com - 主要参考
- Stripe.com - 简洁专业感
- Linear.app - 动画参考
