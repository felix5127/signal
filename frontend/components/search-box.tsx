// Input: 用户输入（搜索关键词）、onSearch 回调
// Output: 防抖后的搜索关键词
// Position: 首页搜索组件，提供全文搜索输入框
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Input } from '@/lib/design-system/web/components/Input'
import { Loader2, Search, X } from 'lucide-react'

interface SearchBoxProps {
  /** 初始搜索词 */
  value?: string
  /** 搜索回调 */
  onSearch: (keyword: string) => void
  /** 清除搜索回调 */
  onClear?: () => void
  /** 占位符文本 */
  placeholder?: string
  /** 防抖延迟（毫秒） */
  debounceMs?: number
  /** 是否正在加载 */
  loading?: boolean
  /** 额外的 CSS 类名 */
  className?: string
}

/**
 * 搜索框组件
 *
 * 特性：
 * - 防抖处理（默认 300ms）
 * - 支持清除按钮
 * - 支持 Enter 键立即搜索
 * - 响应式设计
 */
export function SearchBox({
  value = '',
  onSearch,
  onClear,
  placeholder = '搜索标题、摘要、标签...',
  debounceMs = 300,
  loading = false,
  className,
}: SearchBoxProps) {
  const [inputValue, setInputValue] = useState(value)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 同步外部 value 变化
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // 防抖搜索
  const debouncedSearch = useCallback(
    (keyword: string) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      debounceTimerRef.current = setTimeout(() => {
        onSearch(keyword.trim())
      }, debounceMs)
    },
    [onSearch, debounceMs]
  )

  // 清理定时器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    debouncedSearch(newValue)
  }

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      // 立即触发搜索，取消防抖
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      onSearch(inputValue.trim())
    } else if (e.key === 'Escape') {
      // ESC 清除搜索
      handleClear()
    }
  }

  // 处理清除
  const handleClear = () => {
    setInputValue('')
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    onSearch('')
    onClear?.()
  }

  return (
    <div className={cn('relative', className)}>
      <Input
        type="text"
        variant="glass"
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        startAdornment={
          loading ? (
            <Loader2 className="w-5 h-5 animate-spin text-slate-500" />
          ) : (
            <Search className="w-5 h-5 text-slate-500" />
          )
        }
        endAdornment={
          inputValue && (
            <button
              onClick={handleClear}
              className={cn(
                'text-slate-400 hover:text-slate-600',
                'transition-colors'
              )}
              aria-label="清除搜索"
            >
              <X className="w-5 h-5" />
            </button>
          )
        }
      />
    </div>
  )
}
