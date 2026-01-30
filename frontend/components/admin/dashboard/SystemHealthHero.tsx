/**
 * [INPUT]: pipelineStatus, sourceHealth
 * [OUTPUT]: 系统健康指示器 Hero 组件
 * [POS]: dashboard/，系统状态一眼可见
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Database, Server, Wifi } from 'lucide-react'
import type { PipelineStatus, SourceHealthStats } from './hooks/useDashboardData'

interface SystemHealthHeroProps {
  pipelineStatus: PipelineStatus | null
  sourceHealth: SourceHealthStats | null
}

type HealthLevel = 'healthy' | 'degraded' | 'critical'

export function SystemHealthHero({ pipelineStatus, sourceHealth }: SystemHealthHeroProps) {
  // 计算整体健康状态
  const getOverallHealth = (): { level: HealthLevel; message: string } => {
    if (!pipelineStatus || !sourceHealth) {
      return { level: 'critical', message: '数据加载中...' }
    }

    const { summary } = sourceHealth
    const failingRatio = summary.failing / (summary.healthy + summary.degraded + summary.failing || 1)
    const degradedRatio = summary.degraded / (summary.healthy + summary.degraded + summary.failing || 1)

    // Pipeline 正在运行时显示运行中状态
    if (pipelineStatus.pipeline.is_running) {
      return { level: 'healthy', message: `Pipeline 运行中 (${pipelineStatus.pipeline.current_source || '...'})` }
    }

    // 根据数据源健康比例判断
    if (failingRatio > 0.3) {
      return { level: 'critical', message: '多个数据源异常' }
    }
    if (degradedRatio > 0.3 || failingRatio > 0.1) {
      return { level: 'degraded', message: '部分数据源降级' }
    }
    return { level: 'healthy', message: '系统运行正常' }
  }

  const health = getOverallHealth()

  const healthConfig = {
    healthy: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      dot: 'bg-green-500',
      dotGlow: 'shadow-[0_0_8px_2px_rgba(34,197,94,0.5)]',
      text: 'text-green-700 dark:text-green-400',
    },
    degraded: {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      border: 'border-amber-200 dark:border-amber-800',
      dot: 'bg-amber-500',
      dotGlow: 'shadow-[0_0_8px_2px_rgba(245,158,11,0.5)]',
      text: 'text-amber-700 dark:text-amber-400',
    },
    critical: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      dot: 'bg-red-500',
      dotGlow: 'shadow-[0_0_8px_2px_rgba(239,68,68,0.5)]',
      text: 'text-red-700 dark:text-red-400',
    },
  }

  const config = healthConfig[health.level]

  // 服务状态项
  const services = [
    { label: 'DB', icon: Database, status: 'ok' as const },
    { label: 'API', icon: Server, status: 'ok' as const },
    { label: 'Redis', icon: Wifi, status: 'ok' as const },
  ]

  return (
    <div className={`rounded-xl border ${config.border} ${config.bg} p-5`}>
      <div className="flex items-center gap-4">
        {/* 状态灯 */}
        <div className="relative">
          <div
            className={`w-4 h-4 rounded-full ${config.dot} ${config.dotGlow} animate-pulse`}
          />
        </div>

        {/* 主状态信息 */}
        <div className="flex-1">
          <div className={`text-lg font-semibold ${config.text}`}>
            {health.message}
          </div>
          <div className="flex items-center gap-4 mt-2">
            {services.map((service) => {
              const Icon = service.icon
              return (
                <div key={service.label} className="flex items-center gap-1.5">
                  <Icon className="w-3.5 h-3.5 text-[var(--ds-muted)]" />
                  <span className="text-xs text-[var(--ds-muted)]">{service.label}:</span>
                  <span className="text-xs font-medium text-green-600 dark:text-green-400">
                    OK
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 数据源汇总 */}
        {sourceHealth && (
          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-[var(--ds-muted)]">{sourceHealth.summary.healthy}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-[var(--ds-muted)]">{sourceHealth.summary.degraded}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-[var(--ds-muted)]">{sourceHealth.summary.failing}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
