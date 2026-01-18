/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/stats/scheduler)
 * [OUTPUT]: 对外提供调度器状态页面
 * [POS]: admin/ 的调度器监控页面，展示定时任务状态
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw,
  AlertTriangle,
  Clock,
  CheckCircle,
  Play,
  Loader2,
} from 'lucide-react'

// ========== 类型定义 ==========

interface SchedulerJob {
  id: string
  name: string
  trigger: string
  next_run: string | null
  next_run_human: string
}

interface SchedulerStatus {
  status: string
  jobs: SchedulerJob[]
  message?: string
}

// ========== 任务名称映射 ==========

const JOB_LABELS: Record<string, string> = {
  twitter_pipeline: 'Twitter 采集',
  main_pipeline: 'RSS 内容采集',
  daily_digest: '每日精选生成',
  weekly_digest: '每周精选生成',
  newsletter_job: '周刊生成',
}

const JOB_DESCRIPTIONS: Record<string, string> = {
  twitter_pipeline: '从 XGoing 采集 Twitter 推文',
  main_pipeline: '采集 Blog RSS / Podcast / Video 数据',
  daily_digest: '生成今日精选内容汇总',
  weekly_digest: '生成本周精选内容汇总',
  newsletter_job: '自动生成并发布周刊',
}

// ========== 组件 ==========

function JobCard({
  job,
  onTrigger,
  triggering,
}: {
  job: SchedulerJob
  onTrigger: () => void
  triggering: boolean
}) {
  const label = JOB_LABELS[job.id] || job.name
  const description = JOB_DESCRIPTIONS[job.id] || job.trigger

  const formatNextRun = (isoString: string | null) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-500" />
          <span className="font-medium text-[var(--ds-fg)]">{label}</span>
        </div>
        <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
          运行中
        </span>
      </div>

      <p className="text-sm text-[var(--ds-muted)] mb-3">{description}</p>

      <div className="flex items-center justify-between text-sm">
        <div className="text-[var(--ds-muted)]">
          <span>下次运行：</span>
          <span className="font-mono text-[var(--ds-fg)]">
            {formatNextRun(job.next_run)}
          </span>
          <span className="ml-2 text-indigo-500">({job.next_run_human})</span>
        </div>
        <button
          onClick={onTrigger}
          disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {triggering ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5" />
          )}
          立即执行
        </button>
      </div>
    </div>
  )
}

// ========== 主页面 ==========

export default function SchedulerPage() {
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setRefreshing(true)
      const res = await fetch('/api/stats/scheduler', { cache: 'no-store' })

      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }

      const data = await res.json()

      if (data.success) {
        setScheduler(data.data)
        setError(null)
      } else {
        setError(data.error || '获取调度器状态失败')
      }
    } catch (e) {
      setError('无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    // 每 30 秒自动刷新
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleTrigger = async (jobId: string) => {
    // 根据任务 ID 映射到对应的触发端点
    // 部分任务直接触发对应的 API 端点，部分任务触发信号源采集
    const jobTriggerConfig: Record<string, { type: 'source' | 'digest'; target: string }> = {
      twitter_pipeline: { type: 'source', target: 'twitter' },
      main_pipeline: { type: 'source', target: 'hackernews' },
      daily_digest: { type: 'digest', target: 'daily' },
      weekly_digest: { type: 'digest', target: 'weekly' },
      newsletter_job: { type: 'digest', target: 'newsletter' },
    }

    const config = jobTriggerConfig[jobId]
    if (!config) {
      console.warn(`No trigger config for job: ${jobId}`)
      return
    }

    // 根据任务类型选择不同的 API 端点
    const apiUrl = config.type === 'source'
      ? `/api/sources/trigger/${config.target}`
      : `/api/digest/trigger/${config.target}`

    try {
      setTriggeringJob(jobId)
      const res = await fetch(apiUrl, {
        method: 'POST',
      })

      if (!res.ok) {
        console.error('Trigger failed:', res.status)
        return
      }

      const data = await res.json()
      if (data.success) {
        setTimeout(fetchData, 2000)
      }
    } catch (e) {
      console.error('Trigger error:', e)
    } finally {
      setTriggeringJob(null)
    }
  }

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
              onClick={fetchData}
              className="text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">定时任务调度</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              查看和管理自动采集任务的调度状态
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  scheduler?.status === 'running'
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-yellow-500'
                }`}
              />
              <span className="text-sm text-[var(--ds-muted)]">
                {scheduler?.status === 'running' ? '调度器运行中' : '调度器已停止'}
              </span>
            </div>
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>

        {/* 任务列表 */}
        <div className="space-y-4">
          {scheduler?.jobs && scheduler.jobs.length > 0 ? (
            scheduler.jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onTrigger={() => handleTrigger(job.id)}
                triggering={triggeringJob === job.id}
              />
            ))
          ) : (
            <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-8 text-center">
              <Clock className="w-12 h-12 text-[var(--ds-muted)] mx-auto mb-4" />
              <p className="text-[var(--ds-muted)]">暂无调度任务</p>
            </div>
          )}
        </div>

        {/* 调度器消息 */}
        {scheduler?.message && (
          <div className="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-700 dark:text-yellow-400">
              {scheduler.message}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
