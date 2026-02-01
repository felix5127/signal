/**
 * [INPUT]: transcription stats
 * [OUTPUT]: 转写成功率卡片组件
 * [POS]: dashboard/，转写任务监控
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { FileText, Mic, AlertCircle } from 'lucide-react'
import type { TranscriptionStats } from './hooks/useDashboardData'

interface TranscriptionCardProps {
  data: TranscriptionStats | null
}

export function TranscriptionCard({ data }: TranscriptionCardProps) {
  if (!data) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-5 h-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-[var(--ds-fg)]">转写成功率</h3>
        </div>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">加载中...</div>
      </div>
    )
  }

  // 只显示播客转写（视频数据源已禁用）
  const items = [
    {
      label: '播客转写',
      icon: Mic,
      transcribed: data.podcast.transcribed,
      total: data.podcast.with_audio,
      rate: data.podcast.success_rate,
      pending: data.podcast.pending,
    },
  ]

  const getColorClass = (rate: number) => {
    if (rate >= 80) return 'bg-green-500'
    if (rate >= 50) return 'bg-amber-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-indigo-500" />
        <h3 className="text-lg font-semibold text-[var(--ds-fg)]">转写成功率</h3>
      </div>

      {/* 转写统计 */}
      <div className="space-y-4 mb-4">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <div key={item.label} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-[var(--ds-muted)]" />
                  <span className="text-sm text-[var(--ds-fg)]">{item.label}</span>
                </div>
                <span className="text-sm font-medium text-[var(--ds-fg)]">
                  {item.rate.toFixed(1)}%
                </span>
              </div>
              <div className="h-1.5 bg-[var(--ds-surface)] rounded-full overflow-hidden">
                <div
                  className={`h-full ${getColorClass(item.rate)} rounded-full transition-all duration-500`}
                  style={{ width: `${Math.max(item.rate, 2)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs text-[var(--ds-muted)]">
                <span>{item.transcribed}/{item.total} 已转写</span>
                <span className="text-amber-600 dark:text-amber-400">待转写: {item.pending}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* 最近失败 */}
      {data.recent_failures.length > 0 && (
        <div className="border-t border-[var(--ds-border)] pt-3">
          <div className="flex items-center gap-1 text-xs text-[var(--ds-muted)] mb-2">
            <AlertCircle className="w-3 h-3" />
            <span>待转写内容</span>
          </div>
          <div className="space-y-1">
            {data.recent_failures.slice(0, 3).map((item) => (
              <div
                key={item.resource_id}
                className="text-xs text-[var(--ds-muted)] truncate"
                title={item.title}
              >
                {item.title}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
