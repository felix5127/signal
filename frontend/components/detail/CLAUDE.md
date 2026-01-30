# detail/
> L2 | 父级: ../CLAUDE.md

## 职责

详情页子组件目录，将 resource-detail.tsx 拆分为可复用的子组件，支持：
- Mercury.com 浅色系设计风格
- Header 全宽 + Content Row 两栏布局
- AI 侧边栏三卡片设计
- 响应式回退（移动端上下布局）

## 设计规范 (Mercury.com 浅色系)

### 颜色系统
- 背景色: #FBFCFD
- 主色调: #1E3A5F
- 主文字: #272735
- 次要文字: #6B6B6B
- 弱化文字: #9A9A9A
- 边框: rgba(0,0,0,0.06)

### 圆角系统
- 卡片: 16px (rounded-2xl)
- 按钮: 12px (rounded-xl)

### 布局结构
- 最大宽度: max-w-6xl (1152px)
- 左侧正文: ~70% (flex-1)
- 右侧侧边栏: 380px
- 间距: gap-8 (32px)

## 成员清单

**index.ts**: 统一导出入口
- 职责: 简化导入路径
- 导出: FeaturedReason, AuthorInfo, AISidebar, ContentArea, AISummaryCard, AIAssistantCard, RelatedContentCard

### AI 侧边栏组件（新增）

**ai-summary-card.tsx**: AI 摘要卡片
- 技术细节: 展示 AI 生成的内容摘要
- 导出: AISummaryCard({ summary, oneSentenceSummary, className })
- 消费方: resource-detail.tsx（右侧侧边栏）
- 样式: 白色背景 + 浅边框 + 16px 圆角

**ai-assistant-card.tsx**: AI 研究助手卡片
- 技术细节: 展示问题列表 + 输入框，支持 AI 问答
- 导出: AIAssistantCard({ mainPoints, className, onAskQuestion })
- 消费方: resource-detail.tsx（右侧侧边栏）
- 样式: 白色背景 + 问题按钮 + 输入框

**related-content-card.tsx**: 相关内容卡片
- 技术细节: 展示相关文章列表
- 导出: RelatedContentCard({ items, className })
- 消费方: resource-detail.tsx（右侧侧边栏）
- 样式: 白色背景 + 文章链接列表

### 遗留组件（保留兼容）

**featured-reason.tsx**: 精选理由组件
- 技术细节: 橙色渐变背景，Sparkles 图标
- 导出: FeaturedReason({ reason, className })
- 状态: 保留，可选使用

**author-info.tsx**: 作者信息卡组件
- 技术细节: 展示作者头像、来源、发布日期、阅读时长、字数
- 导出: AuthorInfo({ author, sourceName, sourceIconUrl, publishedAt, readTime, wordCount })
- 状态: 保留，可选使用

**ai-sidebar.tsx**: AI 分析侧边栏组件（旧版）
- 技术细节: 展示评分、摘要、主要观点、金句
- 导出: AISidebar({ score, isFeatured, summary, mainPoints, keyQuotes })
- 状态: 保留，已被新版三卡片替代

**content-area.tsx**: 主内容区组件（旧版）
- 技术细节: 一句话总结、详细摘要、主要观点、金句、完整内容
- 导出: ContentArea({ oneSentenceSummary, summary, contentMarkdown, mainPoints, keyQuotes, showFullAnalysis })
- 状态: 保留，部分逻辑已内联到 resource-detail.tsx

## 架构设计

### 新版页面结构

```
┌─────────────────────────────────────────────────────────────────┐
│ Breadcrumb: 首页 > 文章详情 > 当前文章                           │
├─────────────────────────────────────────────────────────────────┤
│ Header (全宽)                                                    │
│ ├── 标签行 (Badge 72px × 28px)                                  │
│ ├── 大标题 (36px)                                               │
│ └── Meta信息 (日期 + 来源 + 阅读量)                              │
├───────────────────────────────────┬─────────────────────────────┤
│ 左侧 Article Body (flex-1, ~70%) │ 右侧 AI Sidebar (380px)      │
│                                   │                             │
│ <一句话总结卡片>                   │ <AISummaryCard />           │
│ <正文段落>                         │ <AIAssistantCard />         │
│   - 行高 1.8                       │ <RelatedContentCard />      │
│   - 子标题 18px/600                │                             │
│ <阅读原文按钮>                     │                             │
│                                   │                             │
└───────────────────────────────────┴─────────────────────────────┘
```

### 响应式回退

| 屏幕尺寸 | 布局 | 说明 |
|----------|------|------|
| lg+ (1024px) | 左右结构 | flex-row, aside sticky |
| < lg | 上下结构 | flex-col, sidebar 在正文下方 |

## 样式规范

### 卡片样式
- 背景: bg-white
- 边框: border border-[rgba(0,0,0,0.06)]
- 圆角: rounded-2xl (16px)
- 内边距: p-5 (20px)
- 间距: space-y-5 (20px)

### 排版样式
- 标题: text-[15px] font-semibold text-[#272735]
- 正文: text-[14px] text-[#6B6B6B] leading-[1.7]
- 辅助: text-[13px] text-[#9A9A9A]

### 交互样式
- hover: bg-[#F6F5F2] text-[#272735]
- transition: duration-200

## 依赖关系

### 内部依赖
- @/lib/utils: cn() 工具函数
- @/components/ui/badge: Badge 组件
- @/components/ui/button: Button 组件
- @/components/markdown-renderer: MarkdownRenderer 组件

### 外部依赖
- lucide-react: 图标库
- next/link: 路由链接

## 变更日志

### 2026-01-26 - Mercury 风格重构
- 新增 ai-summary-card.tsx AI 摘要卡片组件
- 新增 ai-assistant-card.tsx AI 研究助手卡片组件
- 新增 related-content-card.tsx 相关内容卡片组件
- 重构 resource-detail.tsx 为 Mercury.com 浅色系风格
- 实现 Header 全宽 + Content Row 两栏布局
- 面包屑改为内联实现（首页 > 文章详情 > 当前文章）
- 标签尺寸统一为 72px × 28px
- 正文排版: 行高 1.8, 子标题 18px/600

### 2026-01-18 - 创建 detail 子组件目录
- 创建 featured-reason.tsx 精选理由组件
- 创建 author-info.tsx 作者信息卡组件
- 创建 ai-sidebar.tsx AI 分析侧边栏组件
- 创建 content-area.tsx 主内容区组件
- 创建 index.ts 统一导出入口

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
