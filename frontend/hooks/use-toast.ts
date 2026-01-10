/**
 * [INPUT]: 依赖 sonner 库
 * [OUTPUT]: Toast 通知 Hook
 * [POS]: hooks/ 的工具函数，被各组件消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { toast } from 'sonner'

export function useToast() {
  return {
    success: (message: string) => toast.success(message),
    error: (message: string) => toast.error(message),
    info: (message: string) => toast.info(message),
    warning: (message: string) => toast.warning(message),
    promise: <T,>(
      promise: Promise<T>,
      {
        loading,
        success,
        error,
      }: {
        loading: string
        success: string | ((data: T) => string)
        error: string | ((err: Error) => string)
      }
    ) => toast.promise(promise, { loading, success, error }),
  }
}
