# components/research/panels/
> L2 | 父级: ../CLAUDE.md

## 职责
研究工作台的面板组件，提供源材料管理、深度研究、输出预览等侧边栏功能。

## 成员清单

**SourcesPanel.tsx**: 左侧源材料面板 (w-72)
- 职责: 源材料列表展示 + 添加 URL/文本 + 删除源材料 + 处理状态图标
- 导出: SourcesPanel({ projectId, sources, onSourcesChange }), Source 类型
- 技术细节: 弹窗表单、状态图标(CheckCircle/Clock/AlertCircle)、Framer Motion 动画
- 状态图标: completed(绿色) / processing|pending(黄色) / failed(红色)
- API: POST /api/research/projects/{id}/sources, DELETE /api/research/sources/{id}

**ChatPanel.tsx**: 中间对话面板
- 职责: 用户/AI 对话，基于项目材料的问答
- 导出: ChatPanel({ projectId, messages, onMessagesChange, sessionId, onSessionIdChange })
- 技术细节: 消息气泡、自动滚动、加载状态、错误处理
- API: POST /api/research/projects/{id}/chat

**ResearchPanel.tsx**: 右侧研究面板
- 职责: 深度研究输入 + SSE 进度展示 + 研究输出列表
- 导出: ResearchPanel({ projectId, outputs, onOutputsChange })
- 技术细节: SSE 流式进度、Framer Motion 动画、可展开输出卡片
- API: POST /api/research/projects/{id}/research (SSE), GET /api/research/projects/{id}/outputs

**index.ts**: 模块导出入口
- 职责: 统一导出 panels 目录下所有组件

## 功能说明

### SourcesPanel
```
┌──────────────────────┐
│ 源材料         (3)   │
│ [+ 添加源材料]       │
├──────────────────────┤
│ ┌──────────────────┐ │
│ │ 🔗 example.com   │ │
│ │ ✅ https://...   │ │
│ │              [x] │ │
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │ 📄 文本片段...   │ │
│ │ ⏳ text          │ │
│ │              [x] │ │
│ └──────────────────┘ │
│                      │
│   还没有源材料       │
│   点击上方按钮添加   │
└──────────────────────┘
```

### ResearchPanel
```
┌────────────────────┐
│   深度研究区       │
│ ┌────────────────┐ │
│ │ 研究问题输入   │ │
│ │ [多行文本框]   │ │
│ │ [开始研究]     │ │
│ ├────────────────┤ │
│ │ 研究进度条     │ │
│ │ ████████░░ 80% │ │
│ ├────────────────┤ │
│ │ 研究结果预览   │ │
│ └────────────────┘ │
├────────────────────┤
│   研究输出 (3)     │
│ ┌────────────────┐ │
│ │ 📄 报告标题    │ │
│ │ research_report│ │
│ │ 1月18日 14:30  │ │
│ │ ▶ 展开查看内容 │ │
│ └────────────────┘ │
│ ┌────────────────┐ │
│ │ 📄 ...         │ │
│ └────────────────┘ │
└────────────────────┘
```

### SSE 流式处理
```typescript
const reader = res.body?.getReader()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  // 解析 data: 行
  // 更新 researchProgress 状态
}
```

## 依赖关系

### API 端点
- POST /api/research/projects/{id}/research (SSE)
  - Body: { query, include_web_search, max_iterations }
  - 返回: SSE 事件流 (phase, message, progress, output)
- GET /api/research/projects/{id}/outputs
  - 返回: Output[]

### 外部依赖
- framer-motion: AnimatePresence + motion.div
- lucide-react: Search, BookOpen, Loader2, CheckCircle2, ChevronDown, ChevronRight, Clock, FileText

## 样式规范

### 面板
- 宽度: w-80 (320px)
- 背景: bg-gray-50
- 边框: border-l border-gray-200

### 深度研究卡片
- 背景: bg-white
- 圆角: rounded-xl
- 边框: border border-gray-200
- 内边距: p-4

### 输出卡片
- 背景: bg-white
- 圆角: rounded-lg
- 边框: border border-gray-200
- 悬浮: hover:shadow-md

### 进度条
- 背景: bg-gray-200
- 进度: bg-purple-600
- 高度: h-1.5
- 圆角: rounded-full

### 按钮
- 主色: bg-purple-600 text-white
- 悬浮: hover:bg-purple-700
- 禁用: disabled:opacity-50

## 变更日志

### 2026-01-18 - ChatPanel 创建
- 创建 ChatPanel.tsx 对话面板组件
- 从 workspace.tsx 提取对话功能
- 状态提升到父组件，通过 props 传递
- 添加错误处理和网络异常提示
- 支持 Ctrl/Cmd + Enter 快捷发送

### 2026-01-18 - 初始创建
- 创建 ResearchPanel.tsx 组件
- 创建 SourcesPanel.tsx 组件
- 实现深度研究 SSE 流式进度
- 实现可展开的研究输出列表
- 创建 CLAUDE.md 文档

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
