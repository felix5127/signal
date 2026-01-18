# Signal Hunter 研究助手 - 前端组件技术方案

> 版本: 1.0 | 日期: 2026-01-17 | 状态: 设计中

---

## 目录

1. [研究工作台布局](#1-研究工作台布局)
2. [核心组件设计](#2-核心组件设计)
3. [SSE 流式更新](#3-sse-流式更新)
4. [状态管理](#4-状态管理)
5. [代码示例](#5-代码示例)

---

## 1. 研究工作台布局

### 1.1 三栏布局架构

研究工作台采用三栏可调整布局，使用 `@radix-ui/react-resizable` 实现面板尺寸调节。

```
┌────────────────────────────────────────────────────────────────────────┐
│  ← 返回     📓 研究项目名称                                   [设置] ⚙️  │
├──────────┬────────────────────────────────────┬─────────────────────────┤
│          │                                    │                         │
│  左栏     │              中栏                  │          右栏           │
│  材料面板  │            输出面板                │        对话面板         │
│          │                                    │                         │
│  250px   │             1fr                    │         380px          │
│  min:200 │           min:400                  │       min:320          │
│  max:350 │                                    │       max:500          │
│          │                                    │                         │
└──────────┴────────────────────────────────────┴─────────────────────────┘
```

### 1.2 面板职责划分

| 面板 | 位置 | 默认宽度 | 职责 |
|------|------|---------|------|
| **SourcePanel** | 左栏 | 250px | 材料列表、选择器、添加入口 |
| **OutputPanel** | 中栏 | 自适应 | 研究输出展示、进度显示、操作按钮 |
| **ChatPanel** | 右栏 | 380px | 对话历史、输入框、上下文指示 |

### 1.3 响应式策略

```typescript
// breakpoints 断点设计
const breakpoints = {
  mobile: 0,      // 单栏堆叠
  tablet: 768,    // 双栏 (材料+输出，对话折叠)
  desktop: 1280,  // 三栏完整展示
}

// 移动端行为
// - 使用 Sheet 抽屉代替侧栏
// - 底部标签页切换面板
// - 对话面板全屏模态
```

---

## 2. 核心组件设计

### 2.1 组件层级结构

```
frontend/
├── app/
│   └── (dashboard)/
│       └── research/
│           ├── page.tsx                    # 项目列表页
│           └── [id]/
│               └── page.tsx                # 研究工作台页
├── components/
│   └── research/
│       ├── project-list.tsx                # 项目列表
│       ├── project-card.tsx                # 项目卡片
│       ├── workspace.tsx                   # 研究工作台容器
│       ├── workspace-header.tsx            # 工作台头部
│       ├── panels/
│       │   ├── source-panel.tsx            # 左栏: 材料面板
│       │   ├── output-panel.tsx            # 中栏: 输出面板
│       │   └── chat-panel.tsx              # 右栏: 对话面板
│       ├── source-selector.tsx             # 材料选择器
│       ├── source-item.tsx                 # 材料列表项
│       ├── source-upload.tsx               # 材料上传
│       ├── research-progress.tsx           # 研究进度条
│       ├── research-todos.tsx              # 任务步骤列表
│       ├── output-viewer.tsx               # 输出查看器
│       ├── output-tabs.tsx                 # 输出类型标签页
│       ├── chat-message.tsx                # 对话消息气泡
│       └── chat-input.tsx                  # 对话输入框
├── hooks/
│   ├── use-projects.ts                     # 项目列表 Hook
│   ├── use-research.ts                     # 研究任务 Hook
│   ├── use-chat.ts                         # 对话 Hook
│   └── use-sse.ts                          # SSE 流式 Hook
└── lib/
    └── stores/
        ├── research-store.ts               # 研究状态 Store
        └── ui-store.ts                     # UI 状态 Store
```

### 2.2 ResearchProjectList - 项目列表

```typescript
/**
 * [INPUT]: 依赖 useProjects hook 获取项目列表
 * [OUTPUT]: 对外提供研究项目列表展示组件
 * [POS]: research/ 页面的核心内容，展示用户所有研究项目
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface ResearchProject {
  id: string
  name: string
  description?: string
  status: 'active' | 'archived'
  sourceCount: number
  outputCount: number
  createdAt: string
  updatedAt: string
  lastResearchedAt?: string
}

interface ProjectListProps {
  onCreateProject: () => void
  onSelectProject: (id: string) => void
}

// 功能特性
// - 项目卡片网格/列表视图切换
// - 按状态/时间筛选
// - 快速搜索
// - 项目归档/删除操作
// - 空状态引导
```

**交互设计**:
- 卡片 hover 提升 (hoverLift)
- 点击进入工作台
- 右键菜单: 重命名/归档/删除
- Spring 动画序列进场

### 2.3 ResearchWorkspace - 研究工作台

```typescript
/**
 * [INPUT]: 依赖 projectId 从路由获取，useResearchStore 管理状态
 * [OUTPUT]: 对外提供完整的研究工作台容器组件
 * [POS]: research/[id] 的核心页面组件，组合三栏面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface WorkspaceProps {
  projectId: string
}

// 布局实现
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'

function ResearchWorkspace({ projectId }: WorkspaceProps) {
  return (
    <div className="h-screen flex flex-col">
      <WorkspaceHeader projectId={projectId} />

      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* 左栏: 材料面板 */}
        <ResizablePanel
          defaultSize={20}
          minSize={15}
          maxSize={30}
          className="bg-gray-50"
        >
          <SourcePanel projectId={projectId} />
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* 中栏: 输出面板 */}
        <ResizablePanel defaultSize={50} minSize={30}>
          <OutputPanel projectId={projectId} />
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* 右栏: 对话面板 */}
        <ResizablePanel
          defaultSize={30}
          minSize={25}
          maxSize={40}
          className="bg-gray-50"
        >
          <ChatPanel projectId={projectId} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
```

### 2.4 SourcePanel - 材料面板

```typescript
/**
 * [INPUT]: 依赖 projectId 获取材料列表，useResearchStore 读写选中状态
 * [OUTPUT]: 对外提供材料列表展示与选择组件
 * [POS]: workspace 左栏，管理研究材料的选择与添加
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface Source {
  id: string
  sourceType: 'url' | 'pdf' | 'audio' | 'video' | 'text'
  title: string
  originalUrl?: string
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  summary?: string
  metadata: Record<string, unknown>
  createdAt: string
}

interface SourcePanelProps {
  projectId: string
}

// 功能特性
// - 材料列表展示 (ScrollArea)
// - 复选框批量选择
// - 全选/反选
// - 材料类型图标
// - 处理状态指示
// - 添加材料入口 (URL/文件上传)
// - 拖拽排序
```

**材料类型图标映射**:

| 类型 | 图标 | 颜色 |
|------|------|------|
| url | Link | blue-500 |
| pdf | FileText | red-500 |
| audio | Headphones | purple-500 |
| video | Video | pink-500 |
| text | FileEdit | gray-500 |

### 2.5 OutputPanel - 输出面板

```typescript
/**
 * [INPUT]: 依赖 useResearch hook 获取研究输出，useResearchStore 获取任务状态
 * [OUTPUT]: 对外提供研究输出展示与进度组件
 * [POS]: workspace 中栏，核心内容展示区域
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface Output {
  id: string
  outputType: 'summary' | 'mindmap' | 'report' | 'podcast'
  title: string
  content: string
  contentFormat: 'markdown' | 'html' | 'json'
  filePath?: string
  createdAt: string
}

interface OutputPanelProps {
  projectId: string
}

// 面板状态
type PanelState =
  | 'empty'      // 无输出，显示引导
  | 'selecting'  // 选择材料中
  | 'running'    // 研究进行中
  | 'completed'  // 展示输出结果

// 功能特性
// - 输出类型 Tabs (摘要/导图/报告/播客)
// - Markdown 渲染 (react-markdown + remark-gfm)
// - 思维导图 Markdown 缩进渲染
// - 研究进度实时展示
// - 操作按钮: 重新生成/导出/生成播客
// - 空状态引导
```

**输出类型标签页设计**:

```typescript
const outputTabs = [
  { id: 'summary', label: '摘要', icon: FileText },
  { id: 'mindmap', label: '导图', icon: GitBranch },
  { id: 'report', label: '报告', icon: BookOpen },
  { id: 'podcast', label: '播客', icon: Mic },
]
```

### 2.6 ChatPanel - 对话面板

```typescript
/**
 * [INPUT]: 依赖 useChat hook 管理对话状态，useSSE 处理流式响应
 * [OUTPUT]: 对外提供对话交互界面组件
 * [POS]: workspace 右栏，提供基于研究上下文的对话能力
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
  isStreaming?: boolean
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  contextSourceIds: string[]
  createdAt: string
}

interface ChatPanelProps {
  projectId: string
}

// 功能特性
// - 对话历史 (ScrollArea + 自动滚动)
// - 消息气泡 (用户/AI 区分样式)
// - 流式响应实时显示
// - 上下文源指示
// - 输入框 (Textarea + Cmd/Ctrl+Enter 发送)
// - 会话切换
// - 清空对话
```

**消息气泡样式**:

```typescript
// 用户消息
const userMessageStyle = "bg-primary text-primary-foreground ml-auto max-w-[80%]"

// AI 消息
const assistantMessageStyle = "bg-muted mr-auto max-w-[85%]"

// 流式响应指示
const streamingIndicator = (
  <span className="inline-flex gap-1">
    <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" />
    <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce delay-100" />
    <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce delay-200" />
  </span>
)
```

### 2.7 ResearchProgress - 研究进度

```typescript
/**
 * [INPUT]: 依赖 useResearchStore 获取当前任务进度和 todos
 * [OUTPUT]: 对外提供研究任务进度展示组件
 * [POS]: OutputPanel 内部，研究进行时显示
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

interface TaskProgress {
  taskId: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  currentStep: string
  todos: Todo[]
  startedAt: string
}

interface ResearchProgressProps {
  progress: TaskProgress
  onCancel: () => void
}

// 功能特性
// - 进度条 (Progress 组件)
// - 任务步骤列表 (todos)
// - 当前步骤高亮
// - 完成步骤打勾
// - 取消按钮
// - 预估剩余时间
```

**进度条动画**:

```typescript
// 使用 Spring 动画平滑过渡
<motion.div
  className="h-full bg-primary rounded-full"
  initial={{ width: 0 }}
  animate={{ width: `${progress}%` }}
  transition={{
    type: "spring",
    stiffness: 200,
    damping: 30
  }}
/>
```

---

## 3. SSE 流式更新

### 3.1 useSSE Hook 设计

```typescript
/**
 * [INPUT]: 依赖 url 和 options 配置
 * [OUTPUT]: 对外提供 SSE 连接管理和数据流处理
 * [POS]: hooks/ 目录，被 useResearch 和 useChat 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { useState, useCallback, useRef, useEffect } from 'react'

// ============================================================
//                        类型定义
// ============================================================

interface SSEEvent<T = unknown> {
  event: string
  data: T
}

interface UseSSEOptions<T> {
  /** 收到消息时回调 */
  onMessage?: (event: SSEEvent<T>) => void
  /** 发生错误时回调 */
  onError?: (error: Error) => void
  /** 连接完成时回调 */
  onComplete?: () => void
  /** 是否自动重连 */
  autoReconnect?: boolean
  /** 重连间隔 (ms) */
  reconnectInterval?: number
  /** 最大重连次数 */
  maxRetries?: number
}

interface UseSSEReturn<T> {
  /** 开始 SSE 连接 */
  connect: (body?: Record<string, unknown>) => void
  /** 断开 SSE 连接 */
  disconnect: () => void
  /** 是否已连接 */
  isConnected: boolean
  /** 是否正在加载 */
  isLoading: boolean
  /** 最新接收的数据 */
  data: T | null
  /** 错误信息 */
  error: Error | null
}

// ============================================================
//                        Hook 实现
// ============================================================

export function useSSE<T = unknown>(
  url: string,
  options: UseSSEOptions<T> = {}
): UseSSEReturn<T> {
  const {
    onMessage,
    onError,
    onComplete,
    autoReconnect = false,
    reconnectInterval = 3000,
    maxRetries = 3,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const abortControllerRef = useRef<AbortController | null>(null)
  const retryCountRef = useRef(0)

  // 连接 SSE (使用 fetch + ReadableStream)
  const connect = useCallback(async (body?: Record<string, unknown>) => {
    // 清理旧连接
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: abortControllerRef.current.signal,
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`SSE connection failed: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('Response body is null')
      }

      setIsConnected(true)
      retryCountRef.current = 0

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          onComplete?.()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6)
              const parsed = JSON.parse(jsonStr) as T
              setData(parsed)
              onMessage?.({ event: 'message', data: parsed })
            } catch {
              // 忽略解析错误
            }
          } else if (line.startsWith('event: ')) {
            const eventName = line.slice(7)
            if (eventName === 'complete' || eventName === 'done') {
              onComplete?.()
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err)
        onError?.(err)

        // 自动重连逻辑
        if (autoReconnect && retryCountRef.current < maxRetries) {
          retryCountRef.current++
          setTimeout(() => connect(body), reconnectInterval)
        }
      }
    } finally {
      setIsConnected(false)
      setIsLoading(false)
    }
  }, [url, onMessage, onError, onComplete, autoReconnect, reconnectInterval, maxRetries])

  // 断开连接
  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsConnected(false)
    setIsLoading(false)
  }, [])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connect,
    disconnect,
    isConnected,
    isLoading,
    data,
    error,
  }
}
```

### 3.2 研究进度实时更新

```typescript
/**
 * useResearch - 研究任务 Hook
 * 封装研究任务的发起、进度监听、取消等操作
 */

import { useSSE } from './use-sse'
import { useResearchStore } from '@/lib/stores/research-store'

interface ResearchSSEEvent {
  type: 'start' | 'progress' | 'partial' | 'complete' | 'error'
  taskId?: string
  step?: number
  total?: number
  message?: string
  todos?: Todo[]
  outputType?: string
  content?: string
  outputs?: Output[]
  error?: string
}

export function useResearch(projectId: string) {
  const { setTaskProgress, setCurrentTask, addOutput } = useResearchStore()
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''

  const { connect, disconnect, isConnected, isLoading, error } = useSSE<ResearchSSEEvent>(
    `${apiUrl}/api/projects/${projectId}/research`,
    {
      onMessage: (event) => {
        const { data } = event

        switch (data.type) {
          case 'start':
            setCurrentTask({
              id: data.taskId!,
              status: 'running',
              startedAt: new Date().toISOString(),
            })
            break

          case 'progress':
            setTaskProgress({
              taskId: data.taskId!,
              status: 'running',
              progress: Math.round((data.step! / data.total!) * 100),
              currentStep: data.message!,
              todos: data.todos || [],
            })
            break

          case 'partial':
            // 部分输出 (流式内容)
            if (data.outputType && data.content) {
              addOutput({
                type: data.outputType,
                content: data.content,
                isPartial: true,
              })
            }
            break

          case 'complete':
            setTaskProgress({
              taskId: data.taskId!,
              status: 'completed',
              progress: 100,
            })
            if (data.outputs) {
              data.outputs.forEach(output => addOutput(output))
            }
            break

          case 'error':
            setTaskProgress({
              taskId: data.taskId!,
              status: 'failed',
              error: data.error,
            })
            break
        }
      },
      onComplete: () => {
        // 连接完成
      },
      onError: (err) => {
        console.error('Research SSE error:', err)
      },
    }
  )

  // 发起研究
  const startResearch = useCallback((request: {
    sourceIds: string[]
    outputTypes: string[]
    task?: string
  }) => {
    connect(request)
  }, [connect])

  // 取消研究
  const cancelResearch = useCallback(async (taskId: string) => {
    disconnect()
    await fetch(`${apiUrl}/api/projects/${projectId}/research/${taskId}/cancel`, {
      method: 'POST',
    })
  }, [disconnect, apiUrl, projectId])

  return {
    startResearch,
    cancelResearch,
    isRunning: isConnected || isLoading,
    error,
  }
}
```

### 3.3 对话流式响应

```typescript
/**
 * useChat - 对话 Hook
 * 封装对话消息的发送和流式接收
 */

import { useSSE } from './use-sse'
import { useResearchStore } from '@/lib/stores/research-store'

interface ChatSSEEvent {
  type: 'start' | 'token' | 'done' | 'error'
  sessionId?: string
  content?: string
  fullContent?: string
  tokensUsed?: number
  error?: string
}

export function useChat(projectId: string) {
  const { addMessage, updateLastMessage, chatMessages } = useResearchStore()
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''
  const streamingContentRef = useRef('')

  const { connect, disconnect, isConnected, isLoading } = useSSE<ChatSSEEvent>(
    `${apiUrl}/api/projects/${projectId}/chat`,
    {
      onMessage: (event) => {
        const { data } = event

        switch (data.type) {
          case 'start':
            // 添加空的 AI 消息占位
            addMessage({
              id: data.sessionId!,
              role: 'assistant',
              content: '',
              isStreaming: true,
            })
            streamingContentRef.current = ''
            break

          case 'token':
            // 累积内容
            streamingContentRef.current += data.content || ''
            updateLastMessage({
              content: streamingContentRef.current,
              isStreaming: true,
            })
            break

          case 'done':
            // 完成流式响应
            updateLastMessage({
              content: data.fullContent || streamingContentRef.current,
              isStreaming: false,
            })
            streamingContentRef.current = ''
            break

          case 'error':
            updateLastMessage({
              content: `Error: ${data.error}`,
              isStreaming: false,
            })
            break
        }
      },
    }
  )

  // 发送消息
  const sendMessage = useCallback((message: string, contextSourceIds?: string[]) => {
    // 先添加用户消息
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
    })

    // 发起 SSE 连接
    connect({
      message,
      contextSourceIds,
    })
  }, [connect, addMessage])

  return {
    sendMessage,
    cancelChat: disconnect,
    isStreaming: isConnected || isLoading,
    messages: chatMessages,
  }
}
```

---

## 4. 状态管理

### 4.1 技术选型对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **Zustand** | 轻量、简洁、TS 友好 | 无内置持久化 | 全局 UI 状态、研究状态 |
| **TanStack Query** | 缓存、重试、失效 | 学习曲线 | 服务端数据、API 请求 |
| **组合使用** | 各取所长 | 复杂度 | 本项目推荐 |

### 4.2 Zustand Store 设计

```typescript
/**
 * [INPUT]: 无外部依赖
 * [OUTPUT]: 对外提供研究状态管理 Store
 * [POS]: lib/stores/ 全局状态管理，被 research 组件消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// ============================================================
//                        类型定义
// ============================================================

interface Project {
  id: string
  name: string
  description?: string
  status: 'active' | 'archived'
  sourceCount: number
  outputCount: number
}

interface Source {
  id: string
  sourceType: string
  title: string
  processingStatus: string
}

interface Output {
  id?: string
  type: string
  content: string
  isPartial?: boolean
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  createdAt?: string
}

interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
}

interface TaskProgress {
  taskId: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  currentStep?: string
  todos?: Todo[]
  error?: string
  startedAt?: string
}

interface ResearchState {
  // 当前项目
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void

  // 项目材料
  sources: Source[]
  setSources: (sources: Source[]) => void
  addSource: (source: Source) => void
  removeSource: (id: string) => void

  // 选中的材料 ID
  selectedSourceIds: string[]
  toggleSource: (id: string) => void
  selectAllSources: () => void
  clearSelection: () => void

  // 研究任务
  currentTask: { id: string; status: string; startedAt: string } | null
  setCurrentTask: (task: { id: string; status: string; startedAt: string } | null) => void
  taskProgress: TaskProgress | null
  setTaskProgress: (progress: Partial<TaskProgress>) => void

  // 研究输出
  outputs: Output[]
  addOutput: (output: Output) => void
  clearOutputs: () => void

  // 对话消息
  chatMessages: Message[]
  addMessage: (message: Message) => void
  updateLastMessage: (update: Partial<Message>) => void
  clearMessages: () => void

  // 面板状态
  panelSizes: { left: number; right: number }
  setPanelSizes: (sizes: { left: number; right: number }) => void
}

// ============================================================
//                        Store 实现
// ============================================================

export const useResearchStore = create<ResearchState>()(
  persist(
    immer((set, get) => ({
      // ========== 当前项目 ==========
      currentProject: null,
      setCurrentProject: (project) =>
        set((state) => {
          state.currentProject = project
          // 切换项目时清空状态
          state.sources = []
          state.selectedSourceIds = []
          state.outputs = []
          state.chatMessages = []
          state.currentTask = null
          state.taskProgress = null
        }),

      // ========== 项目材料 ==========
      sources: [],
      setSources: (sources) =>
        set((state) => {
          state.sources = sources
        }),
      addSource: (source) =>
        set((state) => {
          state.sources.push(source)
        }),
      removeSource: (id) =>
        set((state) => {
          state.sources = state.sources.filter((s) => s.id !== id)
          state.selectedSourceIds = state.selectedSourceIds.filter((sid) => sid !== id)
        }),

      // ========== 选中材料 ==========
      selectedSourceIds: [],
      toggleSource: (id) =>
        set((state) => {
          const idx = state.selectedSourceIds.indexOf(id)
          if (idx === -1) {
            state.selectedSourceIds.push(id)
          } else {
            state.selectedSourceIds.splice(idx, 1)
          }
        }),
      selectAllSources: () =>
        set((state) => {
          state.selectedSourceIds = state.sources.map((s) => s.id)
        }),
      clearSelection: () =>
        set((state) => {
          state.selectedSourceIds = []
        }),

      // ========== 研究任务 ==========
      currentTask: null,
      setCurrentTask: (task) =>
        set((state) => {
          state.currentTask = task
        }),
      taskProgress: null,
      setTaskProgress: (progress) =>
        set((state) => {
          if (state.taskProgress) {
            Object.assign(state.taskProgress, progress)
          } else {
            state.taskProgress = progress as TaskProgress
          }
        }),

      // ========== 研究输出 ==========
      outputs: [],
      addOutput: (output) =>
        set((state) => {
          // 如果是部分输出，更新已有的同类型输出
          if (output.isPartial) {
            const existingIdx = state.outputs.findIndex((o) => o.type === output.type)
            if (existingIdx !== -1) {
              state.outputs[existingIdx] = output
            } else {
              state.outputs.push(output)
            }
          } else {
            state.outputs.push(output)
          }
        }),
      clearOutputs: () =>
        set((state) => {
          state.outputs = []
        }),

      // ========== 对话消息 ==========
      chatMessages: [],
      addMessage: (message) =>
        set((state) => {
          state.chatMessages.push({
            ...message,
            createdAt: message.createdAt || new Date().toISOString(),
          })
        }),
      updateLastMessage: (update) =>
        set((state) => {
          const lastIdx = state.chatMessages.length - 1
          if (lastIdx >= 0) {
            Object.assign(state.chatMessages[lastIdx], update)
          }
        }),
      clearMessages: () =>
        set((state) => {
          state.chatMessages = []
        }),

      // ========== 面板状态 ==========
      panelSizes: { left: 20, right: 30 },
      setPanelSizes: (sizes) =>
        set((state) => {
          state.panelSizes = sizes
        }),
    })),
    {
      name: 'research-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 仅持久化面板尺寸
        panelSizes: state.panelSizes,
      }),
    }
  )
)
```

### 4.3 TanStack Query 缓存策略

```typescript
/**
 * [INPUT]: 依赖 @tanstack/react-query
 * [OUTPUT]: 对外提供 API 数据获取和缓存管理
 * [POS]: hooks/ 目录，封装服务端数据请求
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

// ============================================================
//                        Query Keys
// ============================================================

export const queryKeys = {
  // 项目相关
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  projectSources: (id: string) => ['projects', id, 'sources'] as const,
  projectOutputs: (id: string) => ['projects', id, 'outputs'] as const,
  projectChatSessions: (id: string) => ['projects', id, 'chat-sessions'] as const,
}

// ============================================================
//                        项目 Hooks
// ============================================================

/** 获取项目列表 */
export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => api.get('/projects'),
    staleTime: 5 * 60 * 1000, // 5 分钟
  })
}

/** 获取项目详情 */
export function useProject(id: string) {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => api.get(`/projects/${id}`),
    enabled: !!id,
  })
}

/** 创建项目 */
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      api.post('/projects', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects })
    },
  })
}

/** 删除项目 */
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects })
    },
  })
}

// ============================================================
//                        材料 Hooks
// ============================================================

/** 获取项目材料列表 */
export function useProjectSources(projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectSources(projectId),
    queryFn: () => api.get(`/projects/${projectId}/sources`),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 分钟
  })
}

/** 添加材料 */
export function useAddSource(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { sourceType: string; url?: string; file?: File }) => {
      if (data.file) {
        const formData = new FormData()
        formData.append('file', data.file)
        return api.post(`/projects/${projectId}/sources/upload`, formData)
      }
      return api.post(`/projects/${projectId}/sources`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projectSources(projectId),
      })
    },
  })
}

/** 删除材料 */
export function useDeleteSource(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sourceId: string) =>
      api.delete(`/projects/${projectId}/sources/${sourceId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projectSources(projectId),
      })
    },
  })
}

// ============================================================
//                        输出 Hooks
// ============================================================

/** 获取项目输出列表 */
export function useProjectOutputs(projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectOutputs(projectId),
    queryFn: () => api.get(`/projects/${projectId}/outputs`),
    enabled: !!projectId,
    staleTime: 1 * 60 * 1000, // 1 分钟
  })
}

// ============================================================
//                        缓存失效策略
// ============================================================

/**
 * 缓存时间配置:
 *
 * | 数据类型 | staleTime | gcTime | 理由 |
 * |----------|-----------|--------|------|
 * | 项目列表 | 5min | 30min | 变化频率低 |
 * | 项目详情 | 2min | 10min | 可能被编辑 |
 * | 材料列表 | 2min | 10min | 可能被添加/删除 |
 * | 输出列表 | 1min | 5min | 研究完成后更新 |
 * | 对话会话 | 30s | 5min | 频繁变化 |
 */

// Query Client 全局配置
export const queryClientConfig = {
  defaultOptions: {
    queries: {
      staleTime: 2 * 60 * 1000,    // 默认 2 分钟
      gcTime: 10 * 60 * 1000,      // 垃圾回收 10 分钟
      retry: 1,                     // 重试 1 次
      refetchOnWindowFocus: false,  // 切换窗口不自动刷新
    },
  },
}
```

---

## 5. 代码示例

### 5.1 研究工作台完整实现

```typescript
/**
 * [INPUT]: 依赖 projectId 路由参数，useResearchStore，useProjectSources，useResearch
 * [OUTPUT]: 对外提供完整的研究工作台页面组件
 * [POS]: app/(dashboard)/research/[id]/page.tsx 的页面组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Settings } from 'lucide-react'

import { SourcePanel } from '@/components/research/panels/source-panel'
import { OutputPanel } from '@/components/research/panels/output-panel'
import { ChatPanel } from '@/components/research/panels/chat-panel'
import { useProject, useProjectSources } from '@/hooks/use-projects'
import { useResearchStore } from '@/lib/stores/research-store'
import { fadeInUp } from '@/lib/motion'

export default function ResearchWorkspacePage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  // 数据获取
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: sources, isLoading: sourcesLoading } = useProjectSources(projectId)

  // 状态管理
  const {
    setCurrentProject,
    setSources,
    panelSizes,
    setPanelSizes,
  } = useResearchStore()

  // 初始化项目和材料数据
  useEffect(() => {
    if (project) {
      setCurrentProject(project)
    }
  }, [project, setCurrentProject])

  useEffect(() => {
    if (sources) {
      setSources(sources)
    }
  }, [sources, setSources])

  // 加载状态
  if (projectLoading || sourcesLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  // 项目不存在
  if (!project) {
    return (
      <div className="h-screen flex flex-col items-center justify-center">
        <h2 className="text-xl font-semibold mb-2">项目不存在</h2>
        <Button variant="outline" onClick={() => router.push('/research')}>
          返回项目列表
        </Button>
      </div>
    )
  }

  return (
    <motion.div
      className="h-screen flex flex-col bg-background"
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
    >
      {/* ============================================================
                              头部导航
          ============================================================ */}
      <header className="h-14 border-b flex items-center justify-between px-4 bg-background/95 backdrop-blur">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/research')}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="font-semibold text-lg">{project.name}</h1>
        </div>
        <Button variant="ghost" size="icon">
          <Settings className="w-4 h-4" />
        </Button>
      </header>

      {/* ============================================================
                              三栏布局
          ============================================================ */}
      <ResizablePanelGroup
        direction="horizontal"
        className="flex-1"
        onLayout={(sizes) => {
          if (sizes.length === 3) {
            setPanelSizes({ left: sizes[0], right: sizes[2] })
          }
        }}
      >
        {/* ---------- 左栏: 材料面板 ---------- */}
        <ResizablePanel
          defaultSize={panelSizes.left}
          minSize={15}
          maxSize={30}
          className="bg-muted/30"
        >
          <SourcePanel projectId={projectId} />
        </ResizablePanel>

        <ResizableHandle withHandle className="w-1 bg-border hover:bg-primary/20" />

        {/* ---------- 中栏: 输出面板 ---------- */}
        <ResizablePanel defaultSize={100 - panelSizes.left - panelSizes.right} minSize={30}>
          <OutputPanel projectId={projectId} />
        </ResizablePanel>

        <ResizableHandle withHandle className="w-1 bg-border hover:bg-primary/20" />

        {/* ---------- 右栏: 对话面板 ---------- */}
        <ResizablePanel
          defaultSize={panelSizes.right}
          minSize={20}
          maxSize={40}
          className="bg-muted/30"
        >
          <ChatPanel projectId={projectId} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </motion.div>
  )
}
```

### 5.2 材料面板实现

```typescript
/**
 * [INPUT]: 依赖 projectId，useResearchStore，useAddSource
 * [OUTPUT]: 对外提供材料列表与选择组件
 * [POS]: workspace 左栏组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Link,
  FileText,
  Headphones,
  Video,
  FileEdit,
  Plus,
  CheckSquare,
  Square,
  Loader2,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useResearchStore } from '@/lib/stores/research-store'
import { useAddSource } from '@/hooks/use-projects'
import { fadeInUp, staggerContainerFast } from '@/lib/motion'
import { cn } from '@/lib/utils'

// 材料类型图标映射
const sourceIcons = {
  url: { icon: Link, color: 'text-blue-500' },
  pdf: { icon: FileText, color: 'text-red-500' },
  audio: { icon: Headphones, color: 'text-purple-500' },
  video: { icon: Video, color: 'text-pink-500' },
  text: { icon: FileEdit, color: 'text-gray-500' },
}

interface SourcePanelProps {
  projectId: string
}

export function SourcePanel({ projectId }: SourcePanelProps) {
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [urlInput, setUrlInput] = useState('')

  const {
    sources,
    selectedSourceIds,
    toggleSource,
    selectAllSources,
    clearSelection,
  } = useResearchStore()

  const addSourceMutation = useAddSource(projectId)

  // 添加 URL 材料
  const handleAddUrl = async () => {
    if (!urlInput.trim()) return

    await addSourceMutation.mutateAsync({
      sourceType: 'url',
      url: urlInput.trim(),
    })

    setUrlInput('')
    setAddDialogOpen(false)
  }

  // 全选/取消全选
  const allSelected = sources.length > 0 && selectedSourceIds.length === sources.length
  const handleToggleAll = () => {
    if (allSelected) {
      clearSelection()
    } else {
      selectAllSources()
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* ========== 头部 ========== */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">材料</h2>
          <span className="text-xs text-muted-foreground">
            已选 {selectedSourceIds.length}/{sources.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* 全选按钮 */}
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start"
            onClick={handleToggleAll}
          >
            {allSelected ? (
              <CheckSquare className="w-4 h-4 mr-2" />
            ) : (
              <Square className="w-4 h-4 mr-2" />
            )}
            {allSelected ? '取消全选' : '全选'}
          </Button>

          {/* 添加材料 */}
          <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline">
                <Plus className="w-4 h-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>添加材料</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    网页链接
                  </label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="https://..."
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddUrl()}
                    />
                    <Button
                      onClick={handleAddUrl}
                      disabled={addSourceMutation.isPending}
                    >
                      {addSourceMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        '添加'
                      )}
                    </Button>
                  </div>
                </div>
                {/* TODO: 文件上传区域 */}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* ========== 材料列表 ========== */}
      <ScrollArea className="flex-1">
        <motion.div
          className="p-2 space-y-1"
          variants={staggerContainerFast}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence>
            {sources.map((source) => {
              const Icon = sourceIcons[source.sourceType as keyof typeof sourceIcons]?.icon || FileText
              const iconColor = sourceIcons[source.sourceType as keyof typeof sourceIcons]?.color || 'text-gray-500'
              const isSelected = selectedSourceIds.includes(source.id)
              const isProcessing = source.processingStatus === 'processing'

              return (
                <motion.div
                  key={source.id}
                  variants={fadeInUp}
                  layout
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                    isSelected ? 'bg-primary/10' : 'hover:bg-muted'
                  )}
                  onClick={() => toggleSource(source.id)}
                >
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleSource(source.id)}
                    className="mt-0.5"
                  />

                  <div className={cn('mt-0.5', iconColor)}>
                    {isProcessing ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {source.title || '未命名材料'}
                    </p>
                    {source.processingStatus === 'pending' && (
                      <p className="text-xs text-muted-foreground">等待处理...</p>
                    )}
                    {source.processingStatus === 'processing' && (
                      <p className="text-xs text-blue-500">处理中...</p>
                    )}
                    {source.processingStatus === 'failed' && (
                      <p className="text-xs text-red-500">处理失败</p>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {sources.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">暂无材料</p>
              <p className="text-xs mt-1">点击上方按钮添加</p>
            </div>
          )}
        </motion.div>
      </ScrollArea>
    </div>
  )
}
```

### 5.3 对话面板实现

```typescript
/**
 * [INPUT]: 依赖 projectId，useChat hook，useResearchStore
 * [OUTPUT]: 对外提供对话交互界面组件
 * [POS]: workspace 右栏组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, User, Bot, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChat } from '@/hooks/use-chat'
import { useResearchStore } from '@/lib/stores/research-store'
import { fadeInUp } from '@/lib/motion'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  projectId: string
}

export function ChatPanel({ projectId }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { selectedSourceIds, clearMessages } = useResearchStore()
  const { sendMessage, cancelChat, isStreaming, messages } = useChat(projectId)

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // 发送消息
  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isStreaming) return

    sendMessage(trimmed, selectedSourceIds)
    setInput('')

    // 重置 textarea 高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  // Cmd/Ctrl + Enter 发送
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  // 自动调整 textarea 高度
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
  }

  return (
    <div className="h-full flex flex-col">
      {/* ========== 头部 ========== */}
      <div className="p-4 border-b flex items-center justify-between">
        <div>
          <h2 className="font-semibold">对话</h2>
          {selectedSourceIds.length > 0 && (
            <p className="text-xs text-muted-foreground">
              基于 {selectedSourceIds.length} 个材料
            </p>
          )}
        </div>
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground"
            onClick={clearMessages}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* ========== 消息列表 ========== */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <AnimatePresence mode="popLayout">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full flex items-center justify-center text-muted-foreground"
            >
              <div className="text-center">
                <Bot className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p className="text-sm">基于材料进行对话</p>
                <p className="text-xs mt-1">选择材料后输入问题</p>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  variants={fadeInUp}
                  initial="hidden"
                  animate="visible"
                  layout
                  className={cn(
                    'flex gap-3',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}

                  <div
                    className={cn(
                      'rounded-2xl px-4 py-2.5 max-w-[85%]',
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    )}
                  >
                    {message.role === 'assistant' ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                        {message.isStreaming && (
                          <span className="inline-flex gap-1 ml-1">
                            <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" />
                            <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:0.1s]" />
                            <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:0.2s]" />
                          </span>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>

                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-primary-foreground" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>
      </ScrollArea>

      {/* ========== 输入区域 ========== */}
      <div className="p-4 border-t bg-background">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            placeholder="输入问题... (Cmd+Enter 发送)"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            className="min-h-[44px] max-h-[200px] resize-none"
            rows={1}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="flex-shrink-0"
          >
            {isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        {isStreaming && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 text-muted-foreground"
            onClick={cancelChat}
          >
            停止生成
          </Button>
        )}
      </div>
    </div>
  )
}
```

---

## 附录

### A. 依赖清单

```json
{
  "dependencies": {
    "@radix-ui/react-resizable": "^1.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.5.0",
    "immer": "^10.0.0",
    "framer-motion": "^11.0.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0"
  }
}
```

### B. 动画预设引用

本方案使用项目现有的 Apple 级 Spring 动效系统，详见 `/frontend/lib/motion.ts`。

主要动画预设:
- `fadeInUp`: 淡入上移进场
- `staggerContainer`: 序列进场容器
- `staggerContainerFast`: 快速序列进场
- `hoverLift`: 悬浮提升效果
- `tapScale`: 点击缩放反馈

### C. 设计系统遵循

本方案遵循项目现有的微拟物设计语言:
- 三段式渐变背景
- 三层阴影系统
- 16px - 32px 大圆角
- hover scale-[1.02], active scale-[0.97] 微交互

---

## [PROTOCOL]

变更时更新此头部，然后检查 docs/CLAUDE.md
