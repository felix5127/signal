# components/research/panels/
> L2 | 父级: ../CLAUDE.md

## 职责
研究工作台的面板组件，实现 NotebookLM 风格三栏布局的各个面板。

## 设计风格
- **Mercury.com 浅色系**: #FBFCFD 背景, #1E3A5F 主色调, #8B5CF6 强调色
- **圆角规范**: 12px-16px (输入框/卡片), 24px (大按钮)
- **间距**: 16px 内边距, 12px 组件间距

## 成员清单

**SourcesPanel.tsx**: 左侧来源面板 (300px)
- 职责: NotebookLM 风格来源管理（添加/选择/删除/搜索）
- 导出: SourcesPanel({ projectId, sources, onSourcesChange, selectedSources, onSelectedSourcesChange, isCollapsed, onToggleCollapse }), Source 类型
- 技术细节:
  - Header: "来源" + 折叠图标
  - "+ 添加来源" 按钮 (#1E3A5F)
  - "试用 Deep Research" 链接 (#8B5CF6 紫色)
  - 搜索框 "在网络中搜索新来源"
  - 筛选按钮 (Web / Fast Research)
  - "选择所有来源" 复选框
  - 来源列表（复选框 + 文件图标 + 标题 + 状态）
- API: POST /api/research/projects/{id}/sources, DELETE /api/research/sources/{id}

**ChatPanel.tsx**: 中间对话面板 (flex-1)
- 职责: NotebookLM 风格 AI 对话界面
- 导出: ChatPanel({ projectId, projectName, sourceCount, messages, onMessagesChange, sessionId, onSessionIdChange })
- 技术细节:
  - Header: "对话" + 设置/更多图标
  - 空状态: 项目图标 + 标题 + 来源数 + 建议问题卡片
  - 消息气泡: 用户(#1E3A5F) / AI(白色边框)
  - AI 消息操作按钮: 保存到笔记 / 复制 / 点赞
  - 底部输入框 (圆角24px + 圆形发送按钮)
  - 行高: AI 消息 1.8
- API: POST /api/research/projects/{id}/chat

**StudioPanel.tsx**: 右侧 Studio 面板 (320px)
- 职责: NotebookLM 风格工具网格 + 笔记 + 输出列表
- 导出: StudioPanel({ projectId, outputs, onOutputsChange, isCollapsed, onToggleCollapse })
- 技术细节:
  - Header: "Studio" + 折叠图标
  - 工具网格 (2x3):
    - 音频概览 (#F8F9FA)
    - 视频概览 (#E8F4FD)
    - 思维导图 (#FEF3E8)
    - 报告 (#F0FDF4)
    - 信息图 (#FEF2F2)
    - 演示文稿 (#F5F3FF)
  - Deep Research 输入框 + 进度条
  - "相关笔记" 列表 + "添加笔记" 按钮
  - 研究输出列表（可展开）
- API: POST /api/research/projects/{id}/research (SSE), GET /api/research/projects/{id}/outputs

**index.ts**: 模块导出入口
- 导出: StudioPanel, ChatPanel, SourcesPanel, Source 类型
- 兼容: ResearchPanel (别名 StudioPanel)

## 布局结构

```
┌─────────────────┬────────────────────────────────┬─────────────────────┐
│ Sources (300px) │ Chat (flex-1)                  │ Studio (320px)      │
│                 │                                │                     │
│ ┌─────────────┐ │ ┌────────────────────────────┐ │ ┌─────────────────┐ │
│ │ 来源 + [<]  │ │ │ 对话 + [设置] [更多]       │ │ │ Studio + [>]    │ │
│ ├─────────────┤ │ ├────────────────────────────┤ │ ├─────────────────┤ │
│ │ [+添加来源] │ │ │                            │ │ │ [音频] [视频]   │ │
│ │ 试用 Deep.. │ │ │   ┌──────────────────┐     │ │ │ [思维] [报告]   │ │
│ ├─────────────┤ │ │   │ 项目图标         │     │ │ │ [信息] [演示]   │ │
│ │ [搜索来源]  │ │ │   │ 项目名称         │     │ │ ├─────────────────┤ │
│ │ [Web][Fast] │ │ │   │ 3 个来源         │     │ │ │ Deep Research   │ │
│ ├─────────────┤ │ │   └──────────────────┘     │ │ │ [输入问题...]   │ │
│ │ [x] 全选    │ │ │                            │ │ │ [开始研究]      │ │
│ ├─────────────┤ │ │   ┌──────────────────┐     │ │ ├─────────────────┤ │
│ │ [x] 来源1   │ │ │   │ 建议问题卡片 1   │     │ │ │ 相关笔记 [+]    │ │
│ │ [x] 来源2   │ │ │   │ 建议问题卡片 2   │     │ │ │ ┌─────────────┐ │ │
│ │ [x] 来源3   │ │ │   │ 建议问题卡片 3   │     │ │ │ │ 笔记项      │ │ │
│ │             │ │ │   └──────────────────┘     │ │ │ └─────────────┘ │ │
│ │             │ │ │                            │ │ ├─────────────────┤ │
│ │             │ │ ├────────────────────────────┤ │ │ 研究输出 (3)    │ │
│ │             │ │ │ [输入消息...        ] [▶]  │ │ │ ┌─────────────┐ │ │
│ └─────────────┘ │ └────────────────────────────┘ │ │ │ 输出项 1    │ │ │
│                 │                                │ │ │ 输出项 2    │ │ │
│                 │                                │ │ └─────────────┘ │ │
└─────────────────┴────────────────────────────────┴─────────────────────┘
```

## 依赖关系

### API 端点
- POST /api/research/projects/{id}/sources - 添加来源
- DELETE /api/research/sources/{id} - 删除来源
- POST /api/research/projects/{id}/chat - 对话
- POST /api/research/projects/{id}/research (SSE) - 深度研究
- GET /api/research/projects/{id}/outputs - 获取输出列表

### 外部依赖
- framer-motion: AnimatePresence + motion.div
- lucide-react: 图标库

## 样式规范

### 颜色
- 背景: #FBFCFD
- 主色: #1E3A5F
- 强调: #8B5CF6 (紫色)
- 边框: rgba(0, 0, 0, 0.06)

### 面板
- 左侧: w-[300px], 可折叠到 48px
- 中间: flex-1, min-w-0
- 右侧: w-[320px], 可折叠到 48px

### 输入框
- 圆角: rounded-xl (12px) / rounded-3xl (24px 大输入框)
- 背景: bg-[#FBFCFD]
- 边框: border-gray-200
- 聚焦: ring-[#1E3A5F]/20

### 按钮
- 主按钮: bg-[#1E3A5F] text-white rounded-xl
- 次按钮: border border-gray-200 rounded-lg

## 变更日志

### 2026-01-26 - NotebookLM 风格重构
- SourcesPanel.tsx 重构: 添加选择状态、搜索框、筛选按钮、Deep Research 链接
- ChatPanel.tsx 重构: 添加项目标题区、建议问题卡片、消息操作按钮、圆角输入框
- 新增 StudioPanel.tsx: 替代 ResearchPanel，添加工具网格(2x3)、相关笔记区
- 删除 ResearchPanel.tsx (由 StudioPanel 替代)
- index.ts 更新: 导出 StudioPanel，保留 ResearchPanel 别名兼容

### 2026-01-18 - 初始创建
- 创建 ResearchPanel.tsx 组件
- 创建 SourcesPanel.tsx 组件
- 创建 ChatPanel.tsx 组件
- 实现深度研究 SSE 流式进度
- 创建 CLAUDE.md 文档

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
