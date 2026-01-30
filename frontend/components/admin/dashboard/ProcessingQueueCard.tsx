/**
 * [INPUT]: pipelineStatus (queue stats)
 * [OUTPUT]: 处理队列卡片组件
 * [POS]: dashboard/，待处理任务队列展示
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Languages, Mic } from 'lucide-react'
import type { PipelineStatus } from './hooks/useDashboardData'

interface ProcessingQueueCardProps {
  pipelineStatus: PipelineStatus | null
}

export function ProcessingQueueCard({ pipelineStatus }: ProcessingQueueCardProps) {
  if (!pipelineStatus) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
        <div className="h-20 flex items-center justify-center text-[var(--ds-muted)]">
          加载中...
        </div>
      </div>
    )
  }

  const { queue } = pipelineStatus

  const items = [
    {
      label: '待翻译',
      value: queue.pending_translation,
      icon: Languages,
      color: 'amber',
      bgClass: 'bg-amber-100 dark:bg-amber-900/30',
      textClass: 'text-amber-600 dark:text-amber-400',
    },
    {
      label: '待转写',
      value: queue.pending_transcription,
      icon: Mic,
      color: 'purple',
      bgClass: 'bg-purple-100 dark:bg-purple-900/30',
      textClass: 'text-purple-600 dark:text-purple-400',
    },
  ]

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
      <h3 className="text-sm font-medium text-[var(--ds-muted)] mb-3">处理队列</h3>
      <div className="space-y-3">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <div key={item.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${item.bgClass}`}>
                  <Icon className={`w-4 h-4 ${item.textClass}`} />
                </div>
                <span className="text-sm text-[var(--ds-fg)]">{item.label}</span>
              </div>
              <span className={`text-xl font-bold ${item.textClass}`}>
                {item.value}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
