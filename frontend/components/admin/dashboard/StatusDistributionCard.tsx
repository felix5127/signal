/**
 * [INPUT]: overview (by_status)
 * [OUTPUT]: 状态分布卡片组件
 * [POS]: dashboard/，资源状态分布可视化
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Hourglass, CheckCircle, XCircle, Send } from 'lucide-react'
import type { StatsOverview } from './hooks/useDashboardData'

interface StatusDistributionCardProps {
  overview: StatsOverview | null
}

export function StatusDistributionCard({ overview }: StatusDistributionCardProps) {
  if (!overview) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">状态分布</h3>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">加载中...</div>
      </div>
    )
  }

  const statusItems = [
    { key: 'pending', label: '待审核', icon: Hourglass, color: 'text-amber-500', bg: 'bg-amber-500' },
    { key: 'approved', label: '已通过', icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500' },
    { key: 'rejected', label: '已拒绝', icon: XCircle, color: 'text-red-500', bg: 'bg-red-500' },
    { key: 'published', label: '已发布', icon: Send, color: 'text-blue-500', bg: 'bg-blue-500' },
  ] as const

  const total = Object.values(overview.by_status).reduce((sum, val) => sum + val, 0)

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">状态分布</h3>
      <div className="space-y-4">
        {statusItems.map((item) => {
          const count = overview.by_status[item.key]
          const percent = total > 0 ? (count / total) * 100 : 0
          const Icon = item.icon

          return (
            <div key={item.key} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${item.color}`} />
                  <span className="text-sm text-[var(--ds-fg)]">{item.label}</span>
                </div>
                <span className="text-sm font-medium text-[var(--ds-fg)]">
                  {count.toLocaleString()}
                </span>
              </div>
              <div className="h-2 bg-[var(--ds-surface)] rounded-full overflow-hidden">
                <div
                  className={`h-full ${item.bg} rounded-full transition-all duration-500`}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
