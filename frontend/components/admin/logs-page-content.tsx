/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/sources/runs)
 * [OUTPUT]: 对外提供采集日志页面
 * [POS]: admin/ 的采集日志页面，展示详细的采集历史记录
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Filter,
  FileText,
} from 'lucide-react'

// ========== 类型定义 ==========

interface RunFunnel {
  fetched: number
  rule_filtered: number
  dedup_filtered: number
  llm_filtered: number
  saved: number
}

interface SourceRun {
  id: number
  source_type: string
  status: string
  started_at: string
  ended_at: string | null
  funnel: RunFunnel | null
  error_message: string | null
}

// ========== 常量 ==========

const SOURCE_LABELS: Record<string, string> = {
  hackernews: 'Hacker News',
  github: 'GitHub',
  huggingface: 'Hugging Face',
  twitter: 'Twitter',
  arxiv: 'arXiv',
  producthunt: 'Product Hunt',
  blog: 'Blog RSS',
  podcast: 'Podcast',
  video: 'Video',
}

const STATUS_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'success', label: '成功' },
  { value: 'partial', label: '部分成功' },
  { value: 'error', label: '失败' },
]

// ========== 组件 ==========

function LogRow({
  run,
  isExpanded,
  onToggle,
}: {
  run: SourceRun
  isExpanded: boolean
  onToggle: () => void
}) {
  const formatTime = (isoString: string) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const getStatusIcon = () => {
    switch (run.status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'partial':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusLabel = () => {
    switch (run.status) {
      case 'success':
        return '成功'
      case 'partial':
        return '部分成功'
      case 'error':
        return '失败'
      default:
        return '未知'
    }
  }

  const getDuration = () => {
    if (!run.started_at || !run.ended_at) return '-'
    const start = new Date(run.started_at)
    const end = new Date(run.ended_at)
    const diff = (end.getTime() - start.getTime()) / 1000
    if (diff < 60) return `${Math.round(diff)}秒`
    return `${Math.round(diff / 60)}分钟`
  }

  return (
    <>
      <tr
        onClick={onToggle}
        className="border-b border-[var(--ds-border)] hover:bg-[var(--ds-surface)] cursor-pointer transition-colors"
      >
        <td className="py-3 px-4">
          <span className="font-mono text-sm text-[var(--ds-fg)]">
            {formatTime(run.started_at)}
          </span>
        </td>
        <td className="py-3 px-4">
          <span className="px-2 py-1 rounded bg-[var(--ds-surface)] text-[var(--ds-fg)] text-sm">
            {SOURCE_LABELS[run.source_type] || run.source_type}
          </span>
        </td>
        <td className="py-3 px-4">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="text-sm">{getStatusLabel()}</span>
          </div>
        </td>
        <td className="py-3 px-4 text-right font-mono text-sm text-[var(--ds-fg)]">
          {run.funnel?.fetched || 0}
        </td>
        <td className="py-3 px-4 text-right font-mono text-sm text-[var(--ds-fg)]">
          {run.funnel?.saved || 0}
        </td>
        <td className="py-3 px-4 text-right font-mono text-sm text-[var(--ds-muted)]">
          {getDuration()}
        </td>
        <td className="py-3 px-4 text-right">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-[var(--ds-muted)]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[var(--ds-muted)]" />
          )}
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-[var(--ds-surface)]">
          <td colSpan={7} className="px-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              {/* 漏斗详情 */}
              <div>
                <h4 className="text-sm font-medium text-[var(--ds-fg)] mb-2">
                  采集漏斗
                </h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">原始抓取</span>
                    <span className="font-mono">{run.funnel?.fetched || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">规则过滤后</span>
                    <span className="font-mono">{run.funnel?.rule_filtered || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">去重后</span>
                    <span className="font-mono">{run.funnel?.dedup_filtered || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">LLM 过滤后</span>
                    <span className="font-mono">{run.funnel?.llm_filtered || 0}</span>
                  </div>
                  <div className="flex justify-between font-medium text-green-600">
                    <span>最终存储</span>
                    <span className="font-mono">{run.funnel?.saved || 0}</span>
                  </div>
                </div>
              </div>

              {/* 错误信息 */}
              <div>
                <h4 className="text-sm font-medium text-[var(--ds-fg)] mb-2">
                  执行详情
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">开始时间</span>
                    <span className="font-mono">{formatTime(run.started_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">结束时间</span>
                    <span className="font-mono">{run.ended_at ? formatTime(run.ended_at) : '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--ds-muted)]">耗时</span>
                    <span className="font-mono">{getDuration()}</span>
                  </div>
                </div>
                {run.error_message && (
                  <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
                    {run.error_message}
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ========== 主页面 ==========

export default function LogsPage() {
  const [runs, setRuns] = useState<SourceRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  const fetchData = async (reset = false) => {
    try {
      setRefreshing(true)
      const currentPage = reset ? 1 : page
      const res = await fetch(
        `/api/sources/runs?page=${currentPage}&page_size=50`,
        { cache: 'no-store' }
      )
      const data = await res.json()

      if (data.success) {
        const items = data.data.items || []
        if (reset) {
          setRuns(items)
          setPage(1)
        } else {
          setRuns((prev) => [...prev, ...items])
        }
        setHasMore(items.length === 50)
        setError(null)
      } else {
        setError(data.error || '获取采集日志失败')
      }
    } catch (e) {
      setError('无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData(true)
  }, [])

  const filteredRuns =
    statusFilter === 'all'
      ? runs
      : runs.filter((run) => run.status === statusFilter)

  const handleLoadMore = () => {
    setPage((p) => p + 1)
    fetchData()
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
              onClick={() => fetchData(true)}
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
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">采集日志</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              查看详细的采集历史记录和错误信息
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* 状态筛选 */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-[var(--ds-muted)]" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>

        {/* 日志表格 */}
        <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[var(--ds-surface)]">
                <tr className="text-left text-sm text-[var(--ds-muted)]">
                  <th className="py-3 px-4 font-medium">时间</th>
                  <th className="py-3 px-4 font-medium">信号源</th>
                  <th className="py-3 px-4 font-medium">状态</th>
                  <th className="py-3 px-4 font-medium text-right">抓取</th>
                  <th className="py-3 px-4 font-medium text-right">存储</th>
                  <th className="py-3 px-4 font-medium text-right">耗时</th>
                  <th className="py-3 px-4 font-medium text-right"></th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((run) => (
                  <LogRow
                    key={run.id}
                    run={run}
                    isExpanded={expandedId === run.id}
                    onToggle={() =>
                      setExpandedId(expandedId === run.id ? null : run.id)
                    }
                  />
                ))}
                {filteredRuns.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center">
                      <FileText className="w-12 h-12 text-[var(--ds-muted)] mx-auto mb-4" />
                      <p className="text-[var(--ds-muted)]">暂无采集记录</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* 加载更多 */}
          {hasMore && filteredRuns.length > 0 && (
            <div className="p-4 text-center border-t border-[var(--ds-border)]">
              <button
                onClick={handleLoadMore}
                disabled={refreshing}
                className="px-6 py-2 text-sm text-indigo-600 hover:text-indigo-700 transition-colors disabled:opacity-50"
              >
                {refreshing ? '加载中...' : '加载更多'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
