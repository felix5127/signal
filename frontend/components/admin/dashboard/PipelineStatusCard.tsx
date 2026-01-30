/**
 * [INPUT]: pipelineStatus
 * [OUTPUT]: Pipeline 状态卡片，含实时倒计时
 * [POS]: dashboard/，Pipeline 运行状态展示
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import { Play, Pause, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import type { PipelineStatus } from './hooks/useDashboardData'

interface PipelineStatusCardProps {
  pipelineStatus: PipelineStatus | null
}

export function PipelineStatusCard({ pipelineStatus }: PipelineStatusCardProps) {
  const [countdown, setCountdown] = useState<number | null>(null)

  // 倒计时更新
  useEffect(() => {
    if (pipelineStatus?.next_run.countdown_seconds) {
      setCountdown(pipelineStatus.next_run.countdown_seconds)

      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev === null || prev <= 0) return 0
          return prev - 1
        })
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [pipelineStatus?.next_run.countdown_seconds])

  if (!pipelineStatus) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
        <div className="h-20 flex items-center justify-center text-[var(--ds-muted)]">
          加载中...
        </div>
      </div>
    )
  }

  const { pipeline, last_run, queue } = pipelineStatus

  // 格式化倒计时
  const formatCountdown = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  // 格式化时间
  const formatTime = (isoString: string | null): string => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  // 状态图标和颜色
  const getStatusDisplay = () => {
    if (pipeline.is_running) {
      return {
        icon: Loader2,
        iconClass: 'text-blue-500 animate-spin',
        label: '运行中',
        labelClass: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30',
      }
    }
    if (last_run.status === 'success') {
      return {
        icon: CheckCircle,
        iconClass: 'text-green-500',
        label: '空闲',
        labelClass: 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30',
      }
    }
    if (last_run.status === 'failed') {
      return {
        icon: XCircle,
        iconClass: 'text-red-500',
        label: '上次失败',
        labelClass: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30',
      }
    }
    return {
      icon: Pause,
      iconClass: 'text-gray-500',
      label: '空闲',
      labelClass: 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30',
    }
  }

  const status = getStatusDisplay()
  const StatusIcon = status.icon

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Play className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold text-[var(--ds-fg)]">实时任务状态</h3>
        </div>
        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${status.labelClass}`}>
          <StatusIcon className={`w-3 h-3 inline-block mr-1 ${status.iconClass}`} />
          {status.label}
        </span>
      </div>

      <div className="space-y-3">
        {/* Pipeline 状态 */}
        {pipeline.is_running && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--ds-muted)]">当前源</span>
            <span className="font-medium text-[var(--ds-fg)]">
              {pipeline.current_source || '...'}
            </span>
          </div>
        )}

        {/* 上次运行 */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--ds-muted)]">最近运行</span>
          <span className="text-[var(--ds-fg)]">
            {formatTime(last_run.finished_at)}
            {last_run.status && (
              <span className={`ml-1 ${
                last_run.status === 'success' ? 'text-green-500' : 'text-red-500'
              }`}>
                ({last_run.status === 'success' ? `保存 ${last_run.saved_count}` : '失败'})
              </span>
            )}
          </span>
        </div>

        {/* 下次运行倒计时 */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--ds-muted)]">下次运行</span>
          <span className="font-medium text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {countdown !== null ? formatCountdown(countdown) : '-'}
          </span>
        </div>

        {/* 队列状态 */}
        <div className="pt-3 border-t border-[var(--ds-border)]">
          <div className="text-xs text-[var(--ds-muted)] mb-2">处理队列</div>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-[var(--ds-surface)] rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-amber-600 dark:text-amber-400">
                {queue.pending_translation}
              </div>
              <div className="text-xs text-[var(--ds-muted)]">待翻译</div>
            </div>
            <div className="bg-[var(--ds-surface)] rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                {queue.pending_transcription}
              </div>
              <div className="text-xs text-[var(--ds-muted)]">待转写</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
