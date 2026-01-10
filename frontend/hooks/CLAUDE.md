# hooks/
> L2 | 父级: ../CLAUDE.md

## 成员清单

**use-toast.ts**: Toast 通知 Hook
- 技术细节: 基于 sonner 库的封装，提供 success/error/info/warning/promise 方法
- 导出: useToast() hook
- 消费方: 需要显示通知的组件
- 依赖: sonner

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

### 2025-01-10 - 创建 Toast Hook
- ✅ 创建 use-toast.ts
- ✅ 集成到 app/layout.tsx (Toaster 组件)
- ✅ L3 头部注释标准化

## [PROTOCOL]
变更时更新此头部，然后检查 CLAUDE.md
