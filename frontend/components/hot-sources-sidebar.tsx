// Input: 热门来源 API 数据，type 参数
// Output: 热门来源侧边栏组件（使用设计系统）
// Position: 首页右侧边栏，显示热门来源列表
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/lib/design-system/web/components/Button'

interface HotSource {
  name: string
  icon: string
  totalCount: number
  qualifiedCount: number
}

interface HotSourcesResponse {
  items: HotSource[]
}

interface HotSourcesSidebarProps {
  type: string
  onSourceSelect: (sourceName: string) => void
  currentSource?: string
}

export function HotSourcesSidebar({ type, onSourceSelect, currentSource }: HotSourcesSidebarProps) {
  const [sources, setSources] = useState<HotSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHotSources = async () => {
      setLoading(true)
      setError(null)

      try {
        const response = await fetch(
          `/api/sources/hot?type=${type}&limit=10`
        )

        if (!response.ok) {
          throw new Error(`获取热门来源失败: ${response.status}`)
        }

        const data: HotSourcesResponse = await response.json()
        setSources(data.items)
      } catch (err) {
        console.error('获取热门来源失败:', err)
        setError(err instanceof Error ? err.message : '获取数据失败')
      } finally {
        setLoading(false)
      }
    }

    fetchHotSources()
  }, [type])

  if (loading) {
    return (
      <aside className="w-full">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-4 sticky top-20 shadow-card">
          <h3 className="font-semibold text-[var(--ds-fg)] mb-4">
            热门来源
          </h3>
          <div className="flex items-center justify-center py-4">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--ds-muted)]" />
          </div>
        </div>
      </aside>
    )
  }

  if (error || sources.length === 0) {
    return (
      <aside className="w-full">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-4 sticky top-20 shadow-card">
          <h3 className="font-semibold text-[var(--ds-fg)] mb-4">
            热门来源
          </h3>
          <p className="text-sm text-[var(--ds-muted)] text-center py-4">
            {error || '暂无数据'}
          </p>
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-full">
      <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-4 sticky top-20 shadow-card">
        <h3 className="font-semibold text-[var(--ds-fg)] mb-4">
          热门来源
        </h3>
        <ul className="space-y-1">
          {sources.map((source, index) => {
            const isSelected = currentSource === source.name
            // 使用 name + index 组合确保 key 唯一性
            const uniqueKey = `${source.name}-${index}`
            return (
              <li key={uniqueKey}>
                <button
                  onClick={() => onSourceSelect(source.name)}
                  className={`
                    flex items-center gap-2 w-full p-2.5 rounded-2xl
                    transition-all duration-150 text-left
                    ${isSelected
                      ? 'bg-[#F3F2FF] dark:bg-[#6258FF]/10 ring-1 ring-[#CDCBFF] dark:ring-[#6258FF]'
                      : 'hover:bg-[var(--ds-surface-2)]'
                    }
                  `}
                  title={`总数: ${source.totalCount} | 高分: ${source.qualifiedCount}`}
                >
                  {/* 来源图标 */}
                  {source.icon ? (
                    <img
                      src={source.icon}
                      className="w-5 h-5 rounded-md flex-shrink-0"
                      alt=""
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.style.display = 'none'
                      }}
                    />
                  ) : (
                    <div className="w-5 h-5 rounded-md bg-[var(--ds-surface-2)] flex-shrink-0" />
                  )}

                  {/* 来源名称 */}
                  <span className={cn(
                    "flex-1 text-sm truncate",
                    isSelected ? "text-[#6258FF] dark:text-[#CDCBFF] font-medium" : "text-[var(--ds-fg)]"
                  )}>
                    {source.name}
                  </span>

                  {/* 文章数量 */}
                  <span className={cn(
                    "text-xs flex-shrink-0",
                    isSelected ? "text-[#6258FF] dark:text-[#CDCBFF]" : "text-[var(--ds-muted)]"
                  )}>
                    {source.totalCount}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>

        {/* 清除筛选 */}
        {currentSource && (
          <Button
            variant="secondary"
            size="sm"
            className="mt-4 w-full"
            onClick={() => onSourceSelect('')}
          >
            清除来源筛选
          </Button>
        )}
      </div>
    </aside>
  )
}
