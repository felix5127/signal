# podcast/
> L2 | 父级: ../CLAUDE.md

## 职责

播客详情页子组件目录，实现 4 Tab 结构的播客特殊体验：
- Show Notes (原始描述)
- Content Overview (章节概览 + 时间戳跳转)
- Transcript (转录文本)
- Q&A Recap (问答回顾)

## 成员清单

**index.ts**: 统一导出入口
- 职责: 简化导入路径
- 导出: AudioPlayerProvider, useAudioPlayer, AudioPlayer, ChapterOverview, TranscriptView, QARecap, ContentTabs, PodcastDetail, formatTime, formatDuration

**audio-player-context.tsx**: 音频播放器 Context
- 技术细节: React Context API，替代全局 window 对象
- 导出: AudioPlayerProvider, useAudioPlayer
- 消费方: PodcastDetail (Provider), ChapterOverview (Consumer)
- 功能: 跨组件共享播放状态、seekTo 方法

**utils.ts**: 公共工具函数
- 技术细节: 时间格式化等共享函数
- 导出: formatTime, formatDuration
- 消费方: audio-player.tsx, chapter-overview.tsx, podcast-detail.tsx

**podcast-detail.tsx**: 播客详情页主组件
- 技术细节: 4 Tab 结构，整合所有子组件
- 导出: PodcastDetail({ resource })
- 消费方: 被 resource-detail.tsx 根据 type='podcast' 条件渲染
- 布局: 单栏结构，顶部信息卡 + 播放器 + Tab 内容

**audio-player.tsx**: 音频播放器组件
- 技术细节: HTML5 Audio API，支持进度条、倍速、音量、下载
- 导出: AudioPlayer({ audioUrl, duration, onTimeUpdate }), seekToTime(seconds)
- 功能:
  - 播放/暂停控制
  - 进度条拖拽跳转
  - 后退 10s / 前进 30s
  - 倍速切换 (0.5x - 2x)
  - 音量控制 + 静音
  - 下载按钮
  - 全局 seekToTime 方法供章节跳转

**content-tabs.tsx**: Tab 切换组件
- 技术细节: 4 个 Tab 导航，支持禁用无内容的 Tab
- 导出: ContentTabs({ activeTab, onTabChange, children, hasShowNotes, hasChapters, hasTranscript, hasQA })
- Tab 定义:
  - show-notes: Show Notes (原始描述)
  - chapters: Content Overview (章节概览)
  - transcript: Transcript (转录文本)
  - qa: Q&A Recap (问答回顾)

**chapter-overview.tsx**: 章节概览组件
- 技术细节: 展示章节列表，时间戳可点击跳转
- 导出: ChapterOverview({ chapters, currentTime })
- 数据结构: Chapter = { time: number, title: string, summary?: string }
- 功能:
  - 高亮当前播放章节
  - 点击时间戳跳转播放

**transcript-view.tsx**: 转录文本展示组件
- 技术细节: 全文展示 + 搜索高亮 + 复制按钮
- 导出: TranscriptView({ transcript })
- 功能:
  - 搜索关键词高亮
  - 一键复制全文
  - 字数统计

**qa-recap.tsx**: Q&A 回顾组件
- 技术细节: 可展开的问答对列表
- 导出: QARecap({ qaPairs })
- 数据结构: QAPair = { question: string, answer: string, timestamp?: number }
- 功能:
  - 默认展开第一个
  - 点击展开/收起

## 数据依赖

### 后端字段 (Resource 模型)

| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| audio_url | TEXT | 音频 URL | ✅ 已有 |
| duration | INTEGER | 时长（秒） | ✅ 已有 |
| transcript | TEXT | 转录文本 | ✅ 已有 |
| chapters | JSON | 章节列表 | ✅ 已添加 |
| qa_pairs | JSON | Q&A 对 | ✅ 已添加 |
| featured_reason | TEXT | 精选理由 | ✅ 已添加 |
| featured_reason_zh | TEXT | 中文精选理由 | ✅ 已添加 |

### 期望的 JSONB 格式

```typescript
// chapters
[
  { "time": 79, "title": "为什么AI Coding让人开始'价值焦虑'", "summary": "..." },
  { "time": 511, "title": "为什么AI Coding像'言出法随'", "summary": "..." }
]

// qa_pairs
[
  { "question": "AI Coding 会取代程序员吗？", "answer": "不会完全取代..." },
  { "question": "如何提升与 AI 协作的效率？", "answer": "关键在于..." }
]
```

## 样式规范

### 配色
- 一句话总结: blue/indigo 渐变背景
- 信息卡片: gray-50 / gray-800
- Tab 导航: gray-100 / gray-800 圆角容器
- 当前章节: indigo 高亮

### 间距
- 组件间: mb-6 / mb-8
- 卡片内: p-4 / p-5
- Tab 内容: min-h-[300px]

### 播放器
- 进度条: h-2 圆角，indigo/purple 渐变
- 控制按钮: 圆形主按钮 + 圆角辅助按钮
- 倍速按钮: px-3 py-1.5 圆角标签

## 依赖关系

### 内部依赖
- @/lib/utils: cn() 工具函数
- @/components/detail/featured-reason: FeaturedReason 组件
- @/components/score-badge: ScoreBadge 组件
- @/components/tag-list: TagList 组件
- @/components/deep-research-button: DeepResearchButton 组件
- @/components/effects/flickering-grid: FlickeringGrid 背景

### 外部依赖
- lucide-react: 图标库

## 变更日志

### 2026-01-18 - 创建 podcast 子组件目录
- 创建 audio-player.tsx 音频播放器组件
- 创建 content-tabs.tsx Tab 切换组件
- 创建 chapter-overview.tsx 章节概览组件
- 创建 transcript-view.tsx 转录文本组件
- 创建 qa-recap.tsx Q&A 回顾组件
- 创建 podcast-detail.tsx 播客详情页主组件
- 创建 index.ts 统一导出入口

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
