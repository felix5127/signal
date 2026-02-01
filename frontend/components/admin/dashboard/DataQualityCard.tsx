/**
 * [INPUT]: dataQuality stats
 * [OUTPUT]: 数据完整率卡片组件
 * [POS]: dashboard/，数据质量监控
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Activity, Mic, FileType } from 'lucide-react'
import type { DataQualityStats } from './hooks/useDashboardData'

interface DataQualityCardProps {
  data: DataQualityStats | null
}

export function DataQualityCard({ data }: DataQualityCardProps) {
  if (!data) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-[var(--ds-fg)]">数据完整率</h3>
        </div>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">加载中...</div>
      </div>
    )
  }

  // 只显示播客和文章（视频数据源已禁用）
  const items = [
    {
      label: '播客',
      icon: Mic,
      rate: data.podcast_quality.completeness_rate,
      detail: `${data.podcast_quality.has_audio_url}/${data.podcast_quality.total} 有音频`,
    },
    {
      label: '文章',
      icon: FileType,
      rate: data.article_quality.completeness_rate,
      detail: `${data.article_quality.has_content}/${data.article_quality.total} 有内容`,
    },
  ]

  const getColorClass = (rate: number) => {
    if (rate >= 80) return 'bg-green-500'
    if (rate >= 50) return 'bg-amber-500'
    return 'bg-red-500'
  }

  const getTextColorClass = (rate: number) => {
    if (rate >= 80) return 'text-green-600 dark:text-green-400'
    if (rate >= 50) return 'text-amber-600 dark:text-amber-400'
    return 'text-red-600 dark:text-red-400'
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-indigo-500" />
        <h3 className="text-lg font-semibold text-[var(--ds-fg)]">数据完整率</h3>
      </div>

      {/* 整体完整率 */}
      <div className="mb-4 p-3 bg-[var(--ds-surface)] rounded-lg">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-[var(--ds-muted)]">整体完整率</span>
          <span className={`text-lg font-bold ${getTextColorClass(data.overall_completeness)}`}>
            {data.overall_completeness.toFixed(1)}%
          </span>
        </div>
        <div className="h-2 bg-[var(--ds-border)] rounded-full overflow-hidden">
          <div
            className={`h-full ${getColorClass(data.overall_completeness)} rounded-full transition-all duration-500`}
            style={{ width: `${data.overall_completeness}%` }}
          />
        </div>
      </div>

      {/* 各类型完整率 */}
      <div className="space-y-3">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <div key={item.label} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-[var(--ds-muted)]" />
                  <span className="text-sm text-[var(--ds-fg)]">{item.label}</span>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-medium ${getTextColorClass(item.rate)}`}>
                    {item.rate.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-[var(--ds-surface)] rounded-full overflow-hidden">
                <div
                  className={`h-full ${getColorClass(item.rate)} rounded-full transition-all duration-500`}
                  style={{ width: `${item.rate}%` }}
                />
              </div>
              <div className="text-xs text-[var(--ds-muted)]">{item.detail}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
