/**
 * [INPUT]: sourceHealth stats
 * [OUTPUT]: RSS 源健康卡片组件
 * [POS]: dashboard/，数据源健康监控
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Radio, CheckCircle } from 'lucide-react'
import type { SourceHealthStats } from './hooks/useDashboardData'

interface SourceHealthCardProps {
  data: SourceHealthStats | null
}

export function SourceHealthCard({ data }: SourceHealthCardProps) {
  if (!data) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Radio className="w-5 h-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-[var(--ds-fg)]">RSS 源健康</h3>
        </div>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">加载中...</div>
      </div>
    )
  }

  const { summary, sources } = data

  // 只显示有问题的源（degraded 或 failing）
  const problemSources = sources.filter(
    (s) => s.health_status === 'degraded' || s.health_status === 'failing'
  ).slice(0, 5)

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
            正常
          </span>
        )
      case 'degraded':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
            降级
          </span>
        )
      case 'failing':
        return (
          <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
            失败
          </span>
        )
      default:
        return null
    }
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <div className="flex items-center gap-2 mb-4">
        <Radio className="w-5 h-5 text-indigo-500" />
        <h3 className="text-lg font-semibold text-[var(--ds-fg)]">RSS 源健康</h3>
      </div>

      {/* 汇总统计 */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-xl font-bold text-green-600 dark:text-green-400">
            {summary.healthy}
          </div>
          <div className="text-xs text-green-700 dark:text-green-500">健康</div>
        </div>
        <div className="text-center p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
          <div className="text-xl font-bold text-amber-600 dark:text-amber-400">
            {summary.degraded}
          </div>
          <div className="text-xs text-amber-700 dark:text-amber-500">降级</div>
        </div>
        <div className="text-center p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="text-xl font-bold text-red-600 dark:text-red-400">
            {summary.failing}
          </div>
          <div className="text-xs text-red-700 dark:text-red-500">失败</div>
        </div>
      </div>

      {/* 问题源列表 */}
      {problemSources.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs text-[var(--ds-muted)] font-medium">需要关注的源：</div>
          {problemSources.map((source) => (
            <div
              key={source.id}
              className="flex items-center justify-between p-2 bg-[var(--ds-surface)] rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm text-[var(--ds-fg)] truncate">{source.name}</div>
                <div className="text-xs text-[var(--ds-muted)]">
                  成功率 {source.collection_success_rate.toFixed(0)}%
                </div>
              </div>
              {getStatusBadge(source.health_status)}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4 text-sm text-[var(--ds-muted)]">
          <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
          所有数据源运行正常
        </div>
      )}
    </div>
  )
}
