/**
 * [INPUT]: Backend API (/api/admin/stats/*)
 * [OUTPUT]: 完整的 Admin Dashboard 页面组件
 * [POS]: dashboard/，管理后台统计仪表板入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import {
  RefreshCw,
  AlertTriangle,
  FileText,
  Calendar,
  Star,
  Database,
  Clock,
} from 'lucide-react'

import { useDashboardData } from './hooks/useDashboardData'
import { SystemHealthHero } from './SystemHealthHero'
import { PipelineStatusCard } from './PipelineStatusCard'
import { CollectionFunnel } from './CollectionFunnel'
import { MetricCard } from './MetricCard'
import { ProcessingQueueCard } from './ProcessingQueueCard'
import { StatusDistributionCard } from './StatusDistributionCard'
import { DailyTrendChart } from './DailyTrendChart'
import { DataQualityCard } from './DataQualityCard'
import { SourceHealthCard } from './SourceHealthCard'
import { TranscriptionCard } from './TranscriptionCard'

export default function AdminDashboard() {
  const {
    overview,
    pipelineStatus,
    todayFunnel,
    daily,
    dataQuality,
    sourceHealth,
    transcription,
    loading,
    error,
    refreshing,
    refresh,
    lastRefreshedAt,
  } = useDashboardData()

  // ========== 加载状态 ==========
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-200 dark:border-indigo-800 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[var(--ds-muted)]">加载中...</p>
        </div>
      </div>
    )
  }

  // ========== 错误状态 ==========
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-8 max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--ds-fg)] mb-2">
              {error}
            </h2>
            <button
              onClick={refresh}
              className="text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ========== 正常渲染 ==========
  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">系统总览</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              一眼看清系统全貌
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastRefreshedAt && (
              <span className="text-xs text-[var(--ds-muted)]">
                {lastRefreshedAt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            )}
            <button
              onClick={refresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>

        {/* 第一行：系统健康 + Pipeline 状态 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          <div className="lg:col-span-1">
            <SystemHealthHero pipelineStatus={pipelineStatus} sourceHealth={sourceHealth} />
          </div>
          <div className="lg:col-span-2">
            <PipelineStatusCard pipelineStatus={pipelineStatus} />
          </div>
        </div>

        {/* 第二行：采集漏斗 */}
        <div className="mb-4">
          <CollectionFunnel todayFunnel={todayFunnel} />
        </div>

        {/* 第三行：核心指标卡片 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={FileText}
            label="资源总数"
            value={overview?.total.toLocaleString() ?? '-'}
            subValue={`已发布 ${overview?.by_status.published.toLocaleString() ?? 0}`}
            color="indigo"
          />
          <MetricCard
            icon={Calendar}
            label="今日采集"
            value={overview?.today.total.toLocaleString() ?? '-'}
            subValue={`已发布 ${overview?.today.published ?? 0}`}
            color="green"
          />
          <MetricCard
            icon={Star}
            label="平均 LLM 评分"
            value={overview?.avg_llm_score?.toFixed(2) ?? '-'}
            color="amber"
          />
          <MetricCard
            icon={Database}
            label="信号源数量"
            value={overview?.sources.total ?? '-'}
            subValue={`白名单 ${overview?.sources.whitelist ?? 0}`}
            color="blue"
          />
        </div>

        {/* 第四行：状态分布 + 日趋势 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <StatusDistributionCard overview={overview} />
          <DailyTrendChart data={daily} />
        </div>

        {/* 第五行：数据质量监控 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <DataQualityCard data={dataQuality} />
          <SourceHealthCard data={sourceHealth} />
          <TranscriptionCard data={transcription} />
        </div>

        {/* 最后更新时间 */}
        <div className="mt-6 flex items-center justify-center gap-2 text-sm text-[var(--ds-muted)]">
          <Clock className="w-4 h-4" />
          <span>数据每 30 秒自动刷新</span>
        </div>
      </div>
    </div>
  )
}

// 导出所有子组件
export { SystemHealthHero } from './SystemHealthHero'
export { PipelineStatusCard } from './PipelineStatusCard'
export { CollectionFunnel } from './CollectionFunnel'
export { MetricCard } from './MetricCard'
export { ProcessingQueueCard } from './ProcessingQueueCard'
export { StatusDistributionCard } from './StatusDistributionCard'
export { DailyTrendChart } from './DailyTrendChart'
export { DataQualityCard } from './DataQualityCard'
export { SourceHealthCard } from './SourceHealthCard'
export { TranscriptionCard } from './TranscriptionCard'
export { useDashboardData } from './hooks/useDashboardData'
