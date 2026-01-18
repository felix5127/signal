# components/research/
> L2 | 父级: components/CLAUDE.md

## 职责
研究助手 UI 组件，提供项目管理、工作台、源材料、研究和对话功能。

## 成员清单
project-list.tsx: 项目列表组件，展示所有研究项目，支持创建/删除
workspace.tsx: 工作台组件，集成源材料管理/研究/对话/输出四个功能区

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

### workspace.tsx
- **源材料管理**: 添加 URL/文本、上传文件、删除源
- **研究功能**: 输入研究问题，SSE 流式接收进度和结果
- **对话功能**: 项目内问答对话，基于项目材料回答
- **输出管理**: 查看生成的研究报告列表

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

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
