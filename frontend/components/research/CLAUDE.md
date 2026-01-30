# components/research/
> L2 | 父级: components/CLAUDE.md

## 职责
研究助手 UI 组件，实现 NotebookLM 风格项目管理和工作台功能。

## 设计风格
- **Mercury.com 浅色系**: #FBFCFD 背景, #1E3A5F 主色调
- **强调色**: #8B5CF6 (紫色)
- **圆角规范**: 12px-16px (卡片/输入框), 24px (大按钮)

## 成员清单
project-list.tsx: NotebookLM 风格项目列表组件，卡片网格布局，支持创建/删除/菜单操作
workspace.tsx: 工作台组件，NotebookLM 风格三栏布局（左侧来源 + 中间对话 + 右侧 Studio）

## 子目录
panels/: 工作台面板组件（SourcesPanel, ChatPanel, StudioPanel），详见 panels/CLAUDE.md

## 路由结构
```
/research                   → project-list.tsx (项目列表首页)
/research/workspace/[id]    → workspace.tsx (项目工作台)
```

## 功能说明

### project-list.tsx (NotebookLM 风格)
- **设计风格**: Mercury.com 浅色系 (#FBFCFD 背景, #1E3A5F 主色调, 16px 圆角)
- **Simple Navbar**: Logo (Radar 图标 + Signal Hunter) + 设置按钮 + PRO 徽章
- **项目网格**: 4 列响应式布局 (1-2-3-4 列)
- **新建卡片**: 虚线边框 + 圆形加号图标 + hover 状态
- **项目卡片**:
  - 尺寸: 295px x 200px (aspect-[295/200])
  - 浅色背景 (8 种颜色轮换: #E8F4FD, #FEF3E8, #F0FDF4 等)
  - 左上: Emoji 图标 (40px, 16 种 Emoji 轮换)
  - 右上: 更多菜单图标 (hover 显示)
  - 底部: 标题 (2 行) + 日期和来源数
  - 交互: hover 提升 + tap 缩放 + Spring 物理动画
- **下拉菜单**: 重命名 + 删除操作
- **创建项目弹窗**: 居中模态框 + 表单输入
- **路由跳转**: 点击卡片跳转至 /research/workspace/[id]

### workspace.tsx (NotebookLM 风格三栏布局)
```
┌─────────────────┬────────────────────────────────┬─────────────────────┐
│ Sources (300px) │ Chat (flex-1)                  │ Studio (320px)      │
│ SourcesPanel    │ ChatPanel                      │ StudioPanel         │
│ 来源管理         │ AI 对话                        │ 工具网格 + 笔记      │
└─────────────────┴────────────────────────────────┴─────────────────────┘
```
- **桌面端**: 三栏同时显示，支持面板折叠
- **移动端**: 中间面板 + 侧边栏抽屉（可滑出）
- **Simple Navbar**: 返回按钮 + Logo + 项目标题 + 设置 + PRO
- **状态管理**: workspace.tsx 管理所有状态，通过 props 传递给子面板

## 技术细节

### 三栏布局
- 左侧来源面板: 300px 宽度，可折叠
- 中间对话面板: flex-1 自适应
- 右侧 Studio 面板: 320px 宽度，可折叠
- 移动端: 固定定位抽屉 + 遮罩层

### 状态设计
- `project`: 当前项目信息
- `sources`: 来源列表
- `selectedSources`: 选中的来源 ID 数组
- `outputs`: 输出列表
- `chatMessages`: 对话消息历史
- `sessionId`: 对话会话 ID
- `leftPanelCollapsed` / `rightPanelCollapsed`: 面板折叠状态

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
- panels/: SourcesPanel, ChatPanel, StudioPanel

## 变更日志

### 2026-01-26 - NotebookLM 风格三栏布局重构
- workspace.tsx 重构为 NotebookLM 风格
- Simple Navbar: 返回按钮 + Logo + 项目标题 + 设置 + PRO 徽章
- 左侧来源面板 (300px): 添加选择状态、搜索框、筛选按钮
- 中间对话面板 (flex-1): 项目标题区、建议问题卡片、圆角输入框
- 右侧 Studio 面板 (320px): 工具网格(2x3)、Deep Research、相关笔记
- 支持面板折叠功能
- 移动端抽屉式侧边栏

### 2026-01-26 - NotebookLM 风格项目列表页重构
- project-list.tsx 重构为 NotebookLM 风格卡片网格布局
- 新增 Simple Navbar 组件 (Logo + 设置 + PRO 徽章)
- 新增 NewProjectCard 组件 (虚线边框 + 圆形加号)
- 新增 ProjectCard 组件 (浅色背景 + Emoji + 下拉菜单)
- 设计风格: Mercury.com 浅色系 (#FBFCFD, #1E3A5F, 16px 圆角)
- 卡片颜色: 8 种浅色背景轮换
- Emoji 图标: 16 种 Emoji 根据项目 ID 轮换
- 交互动画: Spring 物理引擎 (stiffness: 400, damping: 25)

### 2026-01-18 - 三面板布局重构
- workspace.tsx 从 4 标签页切换改为三面板同屏布局
- 创建 panels/ 子目录，拆分为 SourcesPanel、ChatPanel、ResearchPanel
- 移动端支持侧边栏抽屉模式

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
