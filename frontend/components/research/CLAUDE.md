# components/research/
> L2 | 父级: components/CLAUDE.md

## 职责
研究助手 UI 组件，提供项目管理、工作台、源材料、研究和对话功能。

## 成员清单
project-list.tsx: 项目列表组件，展示所有研究项目，支持创建/删除
workspace.tsx: 工作台组件，三面板同屏布局（左侧源材料 + 中间对话 + 右侧研究）

## 子目录
panels/: 工作台面板组件（ResearchPanel 等），详见 panels/CLAUDE.md

## 路由结构
```
/research/projects          → project-list.tsx (项目列表)
/research/workspace/[id]    → workspace.tsx (项目工作台)
```

## 功能说明

### project-list.tsx
- **项目列表**: 展示用户创建的所有研究项目
- **创建项目**: 弹窗表单，输入项目名称
- **删除项目**: 确认后删除项目及关联数据
- **状态管理**: 项目数量、源材料数、输出数统计

### workspace.tsx (三面板布局)
```
┌────────────────┬──────────────────────────────┬────────────────────┐
│ 左侧 (w-72)    │ 中间 (flex-1)                │ 右侧 (w-80)        │
│ SourcesPanel   │ ChatPanel                    │ ResearchPanel      │
│ 源材料列表      │ AI 对话                      │ 深度研究 + 输出     │
└────────────────┴──────────────────────────────┴────────────────────┘
```
- **桌面端**: 三面板同时显示
- **移动端**: 中间面板 + 侧边栏抽屉（可滑出）
- **状态管理**: workspace.tsx 管理所有状态，通过 props 传递给子面板

## 技术细节

### SSE 流式处理 (workspace.tsx)
```typescript
const reader = res.body?.getReader()
while (true) {
  const { done, value } = await reader.read()
  // 解析 event: 和 data: 行
  // 更新进度状态
}
```

### 状态设计
- `project`: 当前项目信息
- `sources`: 源材料列表
- `outputs`: 输出列表
- `researchProgress`: 研究进度 (phase/message/progress)
- `chatMessages`: 对话消息历史
- `sessionId`: 对话会话 ID

## 依赖关系

### API 端点
- GET /api/research/projects
- POST /api/research/projects
- DELETE /api/research/projects/{id}
- GET /api/research/projects/{id}/sources
- POST /api/research/projects/{id}/sources
- DELETE /api/research/sources/{id}
- POST /api/research/projects/{id}/research (SSE)
- POST /api/research/projects/{id}/chat
- GET /api/research/projects/{id}/outputs

### 外部依赖
- framer-motion: 动画
- lucide-react: 图标

### 内部依赖
- @/lib/motion: Spring 动画预设

## 变更日志

### 2026-01-18 - 三面板布局重构
- workspace.tsx 从 4 标签页切换改为三面板同屏布局
- 创建 panels/ 子目录，拆分为 SourcesPanel、ChatPanel、ResearchPanel
- 左侧面板 (w-72): 源材料管理
- 中间面板 (flex-1): AI 对话
- 右侧面板 (w-80): 深度研究 + 输出列表
- 移动端支持侧边栏抽屉模式（滑动展开）
- 面板组件采用状态提升模式，由 workspace.tsx 统一管理状态

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
