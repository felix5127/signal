/**
 * [INPUT]: 依赖 React useState/useEffect，Backend API (/api/admin/stats/*)
 * [OUTPUT]: 对外提供管理后台统计仪表板页面
 * [POS]: admin/ 的数据统计总览页面，展示资源/状态/分数分布/趋势
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import {
  RefreshCw,
  AlertTriangle,
  BarChart3,
  FileText,
  Calendar,
  Star,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  Hourglass,
  Send,
} from 'lucide-react'

// ========== 类型定义 ==========

interface StatsOverview {
  total: number
  by_status: {
    pending: number
    approved: number
    rejected: number
    published: number
  }
  today: {
    total: number
    published: number
  }
  avg_llm_score: number
  sources: {
    total: number
    whitelist: number
  }
}

type DailyStats = Array<{
  date: string
  total: number
  published: number
}>

type ScoreDistribution = Record<string, number>

// ========== 子组件 ==========

function MetricCard({
  icon: Icon,
  label,
  value,
  subValue,
  color = 'indigo',
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  subValue?: string
  color?: 'indigo' | 'green' | 'amber' | 'blue'
}) {
  const colorMap = {
    indigo: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    amber: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <span className="text-sm text-[var(--ds-muted)]">{label}</span>
      </div>
      <div className="text-2xl font-bold text-[var(--ds-fg)]">{value}</div>
      {subValue && (
        <div className="text-sm text-[var(--ds-muted)] mt-1">{subValue}</div>
      )}
    </div>
  )
}

function StatusCard({
  overview,
}: {
  overview: StatsOverview
}) {
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

function DailyChart({
  data,
}: {
  data: DailyStats
}) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">近 7 日趋势</h3>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">暂无数据</div>
      </div>
    )
  }

  const maxTotal = Math.max(...data.map((d) => d.total), 1)

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
        近 7 日趋势
      </h3>
      <div className="flex items-end gap-2 h-40">
        {data.map((day) => {
          const totalHeight = (day.total / maxTotal) * 100
          const publishedHeight = day.total > 0 ? (day.published / day.total) * totalHeight : 0

          return (
            <div
              key={day.date}
              className="flex-1 flex flex-col items-center gap-1"
            >
              {/* 柱状图 */}
              <div className="w-full flex flex-col items-center justify-end h-32 relative">
                {/* 总数柱 */}
                <div
                  className="w-full max-w-8 bg-indigo-200 dark:bg-indigo-900/50 rounded-t transition-all duration-500"
                  style={{ height: `${totalHeight}%` }}
                >
                  {/* 已发布部分（覆盖在底部） */}
                  <div
                    className="absolute bottom-0 left-0 right-0 mx-auto w-full max-w-8 bg-indigo-500 rounded-t transition-all duration-500"
                    style={{ height: `${publishedHeight}%` }}
                  />
                </div>
              </div>
              {/* 日期标签 */}
              <div className="text-xs text-[var(--ds-muted)] whitespace-nowrap">
                {new Date(day.date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
              </div>
            </div>
          )
        })}
      </div>
      {/* 图例 */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-[var(--ds-border)]">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-200 dark:bg-indigo-900/50" />
          <span className="text-xs text-[var(--ds-muted)]">采集总数</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-500" />
          <span className="text-xs text-[var(--ds-muted)]">已发布</span>
        </div>
      </div>
    </div>
  )
}

function ScoreDistributionChart({
  data,
}: {
  data: ScoreDistribution
}) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">LLM 评分分布</h3>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">暂无数据</div>
      </div>
    )
  }

  const maxCount = Math.max(...Object.values(data), 1)
  const labels = ['0分', '1分', '2分', '3分', '4分', '5分']

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
        LLM 评分分布
      </h3>
      <div className="space-y-3">
        {labels.map((label, index) => {
          const count = data[String(index)] || 0
          const percent = (count / maxCount) * 100

          return (
            <div key={index} className="flex items-center gap-3">
              <div className="w-10 text-sm text-[var(--ds-muted)] text-right">
                {label}
              </div>
              <div className="flex-1 h-6 bg-[var(--ds-surface)] rounded overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded transition-all duration-500 flex items-center justify-end pr-2"
                  style={{ width: `${Math.max(percent, 2)}%` }}
                >
                  {count > 0 && (
                    <span className="text-xs font-medium text-white">
                      {count.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ========== 主组件 ==========

export default function DashboardPageContent() {
  const [overview, setOverview] = useState<StatsOverview | null>(null)
  const [daily, setDaily] = useState<DailyStats | null>(null)
  const [scores, setScores] = useState<ScoreDistribution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      setRefreshing(true)
      setError(null)

      const [overviewRes, dailyRes, scoresRes] = await Promise.all([
        fetch('/api/admin/stats/overview', { cache: 'no-store' }),
        fetch('/api/admin/stats/daily?days=7', { cache: 'no-store' }),
        fetch('/api/admin/stats/score-distribution', { cache: 'no-store' }),
      ])

      const [overviewData, dailyData, scoresData] = await Promise.all([
        overviewRes.json(),
        dailyRes.json(),
        scoresRes.json(),
      ])

      if (!overviewRes.ok || !dailyRes.ok || !scoresRes.ok) {
        throw new Error('获取统计数据失败')
      }

      setOverview(overviewData)
      setDaily(dailyData)
      setScores(scoresData)
    } catch (e) {
      setError(e instanceof Error ? e.message : '无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

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

  // ========== 正常渲染 ==========

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">数据统计</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              资源采集与审核数据总览
            </p>
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

        {/* 核心指标卡片 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={FileText}
            label="资源总数"
            value={overview?.total.toLocaleString() ?? '-'}
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

        {/* 状态分布 + 日趋势 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {overview && <StatusCard overview={overview} />}
          {daily && <DailyChart data={daily} />}
        </div>

        {/* 评分分布 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {scores && <ScoreDistributionChart data={scores} />}

          {/* 快速操作提示 */}
          <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
            <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-500" />
              数据说明
            </h3>
            <div className="space-y-3 text-sm text-[var(--ds-muted)]">
              <p>
                <strong className="text-[var(--ds-fg)]">LLM 评分：</strong>
                AI 对内容质量的评估分数，0-5 分制。高分内容更具价值。
              </p>
              <p>
                <strong className="text-[var(--ds-fg)]">状态流转：</strong>
                待审核 → 已通过/已拒绝 → 已发布
              </p>
              <p>
                <strong className="text-[var(--ds-fg)]">趋势图：</strong>
                浅色柱表示采集总数，深色部分表示最终发布数量。
              </p>
              <p>
                <strong className="text-[var(--ds-fg)]">白名单源：</strong>
                高质量来源，跳过 AI 评分直接发布。
              </p>
            </div>
          </div>
        </div>

        {/* 最后更新时间 */}
        <div className="mt-6 flex items-center justify-center gap-2 text-sm text-[var(--ds-muted)]">
          <Clock className="w-4 h-4" />
          <span>数据每 60 秒自动刷新</span>
        </div>
      </div>
    </div>
  )
}
