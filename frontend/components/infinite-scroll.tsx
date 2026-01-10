// Input: hasMore（是否有更多数据）, isLoading（是否加载中）, onLoadMore（加载更多回调）, children（子组件）
// Output: 无限滚动组件，使用 Intersection Observer API
// Position: 列表页容器，自动检测滚动并触发加载
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useEffect, useRef, useCallback } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface InfiniteScrollProps {
  hasMore: boolean
  isLoading: boolean
  onLoadMore: () => void
  threshold?: number
  className?: string
  children?: React.ReactNode
}

export function InfiniteScroll({
  hasMore,
  isLoading,
  onLoadMore,
  threshold = 100,
  className,
  children
}: InfiniteScrollProps) {
  const observerTarget = useRef<HTMLDivElement>(null)

  const handleObserver = useCallback((entries: IntersectionObserverEntry[]) => {
    const [entry] = entries
    if (entry.isIntersecting && hasMore && !isLoading) {
      onLoadMore()
    }
  }, [hasMore, isLoading, onLoadMore])

  useEffect(() => {
    const element = observerTarget.current
    if (!element) return

    const observer = new IntersectionObserver(handleObserver, {
      rootMargin: `${threshold}px`
    })

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [handleObserver, threshold])

  return (
    <div className={cn('flex flex-col', className)}>
      {/* 内容区域 */}
      {children}

      {/* 加载指示器 */}
      <div ref={observerTarget} className="flex justify-center py-8">
        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>加载更多...</span>
          </div>
        )}

        {!hasMore && !isLoading && (
          <div className="text-center">
            <p className="text-sm text-gray-400 dark:text-gray-500">
              没有更多内容了
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
