# detail/
> L2 | 父级: ../CLAUDE.md

## 职责

详情页子组件目录，将 resource-detail.tsx 拆分为可复用的子组件，支持：
- 左右布局（桌面端）
- 上下布局回退（移动端）
- 文章/视频类型共用

## 成员清单

**index.ts**: 统一导出入口
- 职责: 简化导入路径
- 导出: FeaturedReason, AuthorInfo, AISidebar, ContentArea

**featured-reason.tsx**: 精选理由组件
- 技术细节: 橙色渐变背景，Sparkles 图标
- 导出: FeaturedReason({ reason, className })
- 消费方: resource-detail.tsx
- 样式: amber/orange 渐变，圆角卡片

**author-info.tsx**: 作者信息卡组件
- 技术细节: 展示作者头像、来源、发布日期、阅读时长、字数
- 导出: AuthorInfo({ author, sourceName, sourceIconUrl, publishedAt, readTime, wordCount })
- 消费方: AISidebar（侧边栏内嵌）
- 样式: gray 背景，图标 + 文字行

**ai-sidebar.tsx**: AI 分析侧边栏组件
- 技术细节: 展示评分、摘要、主要观点、金句
- 导出: AISidebar({ score, isFeatured, summary, mainPoints, keyQuotes })
- 消费方: resource-detail.tsx（右侧栏）
- 样式: 多个白色卡片，紧凑布局

**content-area.tsx**: 主内容区组件
- 技术细节: 一句话总结、详细摘要、主要观点、金句、完整内容
- 导出: ContentArea({ oneSentenceSummary, summary, contentMarkdown, mainPoints, keyQuotes, showFullAnalysis })
- 消费方: resource-detail.tsx（左侧主区）
- 参数: showFullAnalysis=true 时展示移动端完整 AI 分析

## 架构设计

### 左右布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│ ← 返回                                                          │
├───────────────────────────────────┬─────────────────────────────┤
│ 左侧主内容 (flex-1, max-w-3xl)    │ 右侧侧边栏 (w-80, sticky)   │
│                                   │                             │
│ <FeaturedReason />                │ <AuthorInfo />              │
│ <ContentArea                      │ <AISidebar />               │
│   oneSentenceSummary              │   score                     │
│   contentMarkdown                 │   summary                   │
│   showFullAnalysis={false}        │   mainPoints                │
│ />                                │   keyQuotes                 │
│                                   │                             │
└───────────────────────────────────┴─────────────────────────────┘
```

### 响应式回退

| 屏幕尺寸 | 布局 | 说明 |
|----------|------|------|
| lg+ (1024px) | 左右结构 | flex gap-8, aside sticky |
| < lg | 上下结构 | flex-col, showFullAnalysis=true |

## 样式规范

### 卡片圆角
- 所有卡片: rounded-xl (12px)
- 按钮: rounded-lg (8px)

### 背景色
- FeaturedReason: amber/orange 渐变
- AuthorInfo: gray-50 / gray-800
- AISidebar 卡片: white / gray-800
- AI 评分: indigo/purple 渐变

### 间距
- 组件间: space-y-5
- 卡片内: p-4
- 侧边栏宽度: w-80 (320px)

## 依赖关系

### 内部依赖
- @/lib/utils: cn() 工具函数
- @/components/score-badge: ScoreBadge 组件
- @/components/markdown-renderer: MarkdownRenderer 组件
- @/components/main-points: MainPoints 组件
- @/components/key-quotes: KeyQuotes 组件

### 外部依赖
- lucide-react: 图标库

## 变更日志

### 2026-01-18 - 创建 detail 子组件目录
- 创建 featured-reason.tsx 精选理由组件
- 创建 author-info.tsx 作者信息卡组件
- 创建 ai-sidebar.tsx AI 分析侧边栏组件
- 创建 content-area.tsx 主内容区组件
- 创建 index.ts 统一导出入口

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
