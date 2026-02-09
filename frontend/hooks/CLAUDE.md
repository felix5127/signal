# hooks/
> L2 | 父级: ../CLAUDE.md

## 成员清单

**use-toast.ts**: Toast 通知 Hook
- 技术细节: 基于 sonner 库的封装，提供 success/error/info/warning/promise 方法
- 导出: useToast() hook
- 消费方: 需要显示通知的组件
- 依赖: sonner

**use-sse.ts**: SSE 流式通信 Hook
- 技术细节: 使用 fetch + ReadableStream (非 EventSource，因需 POST + JSON body)
- 导出: useSSE() hook, Reference 类型
- 消费方: ChatPanel (对话流式输出), StudioPanel (报告/思维导图生成)
- 支持事件: text/tool_start/tool_end/done/error
- 返回: { content, isStreaming, error, references, activeTools, start, stop }

## 依赖关系

### 外部依赖
- sonner: Toast 通知库

### 内部依赖
- 无

## 使用示例

```tsx
import { useToast } from '@/hooks/use-toast'

function MyComponent() {
  const { success, error } = useToast()

  const handleAction = async () => {
    try {
      await doSomething()
      success('操作成功！')
    } catch {
      error('操作失败，请重试')
    }
  }
}
```

## 变更日志

### 2026-02-09 - SSE 流式通信 Hook
- 新增 use-sse.ts: 通用 SSE 流式通信 Hook
- 支持 5 种事件类型 (text/tool_start/tool_end/done/error)
- 支持流中断和组件卸载清理
- 被 ChatPanel 和 StudioPanel 消费

### 2025-01-10 - 创建 Toast Hook
- ✅ 创建 use-toast.ts
- ✅ 集成到 app/layout.tsx (Toaster 组件)
- ✅ L3 头部注释标准化

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
