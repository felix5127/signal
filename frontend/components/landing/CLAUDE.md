# components/landing/
> L2 | 父级: ../CLAUDE.md

## 成员清单

### Landing Page Sections（10个组件）

**Hero.tsx**: 首屏 Hero 区域组件
- 技术细节: framer-motion 动画，支持 badge/title/subheadline/CTA 配置
- Props: badge, headline, subheadline, primaryCTA, secondaryCTA, socialProof, visual
- 微交互: 渐变背景 + 浮动动画
- 预设配置: signalHunterHeroConfig

**LogoBar.tsx**: 信任背书 Logo 展示条
- 技术细节: 支持 static/marquee 两种模式，可选 grayscale
- Props: title, logos, variant, grayscale
- 预设配置: signalHunterLogos

**ProblemSection.tsx**: 痛点展示区域
- 技术细节: Card 组件 + grid 布局，展示 3 个核心痛点
- Props: headline, subheadline, painPoints
- 预设配置: signalHunterPainPoints

**FeaturesSection.tsx**: 特性展示区域
- 技术细节: 支持 grid/bento/alternating 三种布局模式
- Props: headline, subheadline, features, layout
- 变体: 3-column grid / 不规则 bento / 左右交替
- 预设配置: signalHunterFeatures

**HowItWorks.tsx**: 工作流程展示区域
- 技术细节: 垂直步骤流程，连接线动画
- Props: headline, subheadline, steps
- 预设配置: signalHunterSteps

**Testimonials.tsx**: 用户评价展示区域
- 技术细节: 支持 carousel/grid/marquee 三种模式
- Props: headline, subheadline, testimonials, layout
- 功能: Avatar 组件 + Star 评分 + Carousel 导航
- 预设配置: signalHunterTestimonials

**Pricing.tsx**: 定价方案展示区域
- 技术细节: Card 组件 + Highlight 高亮显示 + Monthly/Annual 切换
- Props: headline, subheadline, plans, toggle
- 功能: 特性列表 (Check/X 图标) + Most Popular Badge
- 预设配置: signalHunterPricing

**FAQ.tsx**: 常见问题展示区域
- 技术细节: shadcn Accordion 组件
- Props: headline, subheadline, faqs
- 预设配置: signalHunterFAQs

**FinalCTA.tsx**: 最终行动召唤区域
- 技术细节: 渐变背景 + 双按钮配置
- Props: headline, subheadline, primaryCTA, secondaryCTA
- 视觉: gradient mesh + 装饰性 blur elements
- 预设配置: signalHunterFinalCTA

**Footer.tsx**: 页脚组件
- 技术细节: 4-column grid + 社交媒体图标 + 法律链接
- Props: columns, legal, social, copyright
- 预设配置: signalHunterFooterColumns, signalHunterFooterLegal, signalHunterFooterSocial

### 主页面

**app/landing/page.tsx**: Landing Page 主页面
- 职责: 组合所有 Section 组件，形成完整落地页
- 路由: /landing
- 导航: 已添加到 navbar

## 设计规范

### 依赖的 shadcn/ui 组件
- Button (微拟物设计)
- Card (微拟物设计)
- Badge (微拟物设计)
- Avatar
- Accordion
- Input (微拟物设计)

### 依赖的动画库
- @/lib/motion: Framer Motion variants 预设
- fadeInUp, fadeInLeft, fadeInRight, scaleIn
- staggerContainer, viewportConfig

### 使用的图标库
- lucide-react: ArrowRight, Zap, Brain, Check, X, Star, etc.

### 间距系统
- Section padding: py-20 md:py-28
- Container: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
- Grid gap: gap-6 (cards), gap-8 (sections)

### 排版层级
- Display: text-5xl md:text-6xl lg:text-7xl (Hero H1)
- Heading: text-3xl md:text-4xl lg:text-5xl (Section H2)
- Title: text-xl md:text-2xl (Card Title)
- Body: text-base (Paragraph)
- Caption: text-sm (辅助文字)

## 动画规范

### 入场动画
- 淡入上移: fadeInUp (默认)
- 交错展示: staggerContainer (容器)
- 视口触发: viewportConfig (once: true, margin: '-100px')

### 交互反馈
- Card hover: hover:shadow-lg
- Button hover: scale-[1.02]
- Button active: scale-[0.97]

## 依赖关系

### 外部依赖
- react: ^18.3.0
- framer-motion: 动画库
- lucide-react: 图标库
- next: Link 组件

### 内部依赖
- @/components/ui: shadcn/ui 组件库
- @/lib/motion: 动画预设
- @/lib/utils: cn() 工具函数

## 内容配置

所有组件都提供预设配置 (signalHunter*)，包含：
- Signal 的实际文案
- 真实的产品特性描述
- 示例定价方案
- 常见问题解答

## 变更日志

### 2025-01-09 - Landing Page 初始创建
- ✅ 创建 10 个 Section 组件
- ✅ 创建 lib/motion 动画库
- ✅ 整合为主页面 (/landing)
- ✅ 更新 navbar 添加导航入口

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
