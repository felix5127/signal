/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/sources/*)
 * [OUTPUT]: 对外提供 Admin 信号源控制台页面
 * [POS]: admin/ 的信号源管理页面，增强版（含手动触发）
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, useEffect, useRef, useCallback } from 'react'
import { formatTime } from '@/lib/admin-utils'
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  AlertCircle,
  Rss,
  Github,
  Twitter,
  FileText,
  Mic,
  Video,
  Newspaper,
  Sparkles,
  Database,
  Play,
  Loader2,
  ChevronRight,
  ChevronDown,
  Filter,
  Info,
} from 'lucide-react'

// ========== 类型定义 ==========

interface SourceHealth {
  status: string
  message: string
}

interface SourceStats24h {
  fetched: number
  saved: number
  run_count: number
}

interface SourceStatus {
  source_type: string
  enabled: boolean
  health: SourceHealth
  last_run: any
  stats_24h: SourceStats24h
}

interface FunnelStats {
  fetched: number
  rule_filtered: number
  dedup_filtered: number
  llm_filtered: number
  saved: number
  hours: number
}

interface SourceRunFunnel {
  fetched: number
  saved: number
}

interface SourceRun {
  id: number
  source_type: string
  status: 'success' | 'partial' | 'error'
  started_at: string
  ended_at: string | null
  funnel: SourceRunFunnel | null
  error_message: string | null
}

// ========== 图标映射 ==========

const SOURCE_ICONS: Record<string, any> = {
  hackernews: Newspaper,
  github: Github,
  huggingface: Sparkles,
  twitter: Twitter,
  arxiv: FileText,
  producthunt: Rss,
  blog: FileText,
  podcast: Mic,
  video: Video,
}

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

// ========== 组件 ==========

function SourceCard({
  source,
  onToggle,
  onTrigger,
  triggering,
}: {
  source: SourceStatus
  onToggle: () => void
  onTrigger: () => void
  triggering: boolean
}) {
  const Icon = SOURCE_ICONS[source.source_type] || Database
  const label = SOURCE_LABELS[source.source_type] || source.source_type

  const getStatusColor = () => {
    if (!source.enabled) return 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700'
    switch (source.health.status) {
      case 'healthy': return 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700'
      case 'warning': return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
      case 'error': return 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700'
      default: return 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700'
    }
  }

  const getStatusIcon = () => {
    if (!source.enabled) return <XCircle className="w-5 h-5 text-gray-400" />
    switch (source.health.status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'warning': return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'error': return <XCircle className="w-5 h-5 text-red-500" />
      default: return <AlertCircle className="w-5 h-5 text-gray-400" />
    }
  }

  return (
    <div className={`rounded-xl border-2 p-4 transition-all hover:shadow-md ${getStatusColor()}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-[var(--ds-fg)]" />
          <span className="font-medium text-[var(--ds-fg)]">{label}</span>
        </div>
        {getStatusIcon()}
      </div>

      <div className="text-sm text-[var(--ds-muted)] mb-3">
        {source.health.message}
      </div>

      <div className="flex items-center justify-between text-sm mb-3">
        <span className="text-[var(--ds-muted)]">
          24h: <span className="font-mono font-medium text-[var(--ds-fg)]">{source.stats_24h.saved}</span> 条
        </span>
        <span className="text-[var(--ds-muted)]">
          抓取: <span className="font-mono font-medium text-[var(--ds-fg)]">{source.stats_24h.fetched}</span>
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onTrigger}
          disabled={triggering || !source.enabled}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {triggering ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5" />
          )}
          触发采集
        </button>
        <button
          onClick={onToggle}
          className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            source.enabled
              ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200'
              : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200'
          }`}
        >
          {source.enabled ? '禁用' : '启用'}
        </button>
      </div>
    </div>
  )
}

function FunnelChart({ funnel }: { funnel: FunnelStats }) {
  const maxWidth = 100
  const stages = [
    { label: '抓取', value: funnel.fetched, color: 'bg-blue-500' },
    { label: '规则过滤', value: funnel.rule_filtered, color: 'bg-indigo-500' },
    { label: '去重', value: funnel.dedup_filtered, color: 'bg-purple-500' },
    { label: 'LLM过滤', value: funnel.llm_filtered, color: 'bg-pink-500' },
    { label: '存储', value: funnel.saved, color: 'bg-green-500' },
  ]

  const maxValue = Math.max(...stages.map(s => s.value), 1)

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
        采集漏斗 (最近 {funnel.hours} 小时)
      </h3>
      <div className="space-y-3">
        {stages.map((stage, index) => (
          <div key={stage.label} className="flex items-center gap-4">
            <span className="w-20 text-sm text-[var(--ds-muted)]">{stage.label}</span>
            <div className="flex-1 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
              <div
                className={`h-full ${stage.color} transition-all duration-500`}
                style={{ width: `${(stage.value / maxValue) * maxWidth}%` }}
              />
            </div>
            <span className="w-16 text-right font-mono text-sm text-[var(--ds-fg)]">
              {stage.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function RunsTable({ runs }: { runs: SourceRun[] }) {
  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
        最近采集记录
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--ds-muted)] border-b border-[var(--ds-border)]">
              <th className="pb-2 font-medium">时间</th>
              <th className="pb-2 font-medium">信号源</th>
              <th className="pb-2 font-medium">状态</th>
              <th className="pb-2 font-medium text-right">抓取</th>
              <th className="pb-2 font-medium text-right">存储</th>
              <th className="pb-2 font-medium text-right">错误</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-b border-[var(--ds-border)] last:border-0">
                <td className="py-2 text-[var(--ds-fg)]">{formatTime(run.started_at)}</td>
                <td className="py-2">
                  <span className="px-2 py-1 rounded bg-[var(--ds-surface)] text-[var(--ds-fg)]">
                    {SOURCE_LABELS[run.source_type] || run.source_type}
                  </span>
                </td>
                <td className="py-2">
                  {run.status === 'success' ? (
                    <span className="text-green-500">成功</span>
                  ) : run.status === 'partial' ? (
                    <span className="text-yellow-500">部分成功</span>
                  ) : (
                    <span className="text-red-500">失败</span>
                  )}
                </td>
                <td className="py-2 text-right font-mono text-[var(--ds-fg)]">
                  {run.funnel?.fetched || 0}
                </td>
                <td className="py-2 text-right font-mono text-[var(--ds-fg)]">
                  {run.funnel?.saved || 0}
                </td>
                <td className="py-2 text-right">
                  {run.error_message ? (
                    <span className="text-red-500 text-xs" title={run.error_message}>
                      {run.error_message.substring(0, 20)}...
                    </span>
                  ) : (
                    <span className="text-[var(--ds-muted)]">-</span>
                  )}
                </td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-[var(--ds-muted)]">
                  暂无采集记录
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ========== 过滤规则说明 ==========

function FilteringRulesPanel() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-[var(--ds-surface)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-indigo-500" />
          <span className="font-medium text-[var(--ds-fg)]">过滤规则说明</span>
          <span className="text-xs text-[var(--ds-muted)] px-2 py-0.5 bg-[var(--ds-surface)] rounded">
            规则过滤 + LLM 过滤
          </span>
        </div>
        <ChevronDown
          className={`w-5 h-5 text-[var(--ds-muted)] transition-transform ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {expanded && (
        <div className="px-6 pb-6 border-t border-[var(--ds-border)]">
          <div className="grid md:grid-cols-2 gap-6 pt-4">
            {/* 规则过滤 */}
            <div>
              <h4 className="flex items-center gap-2 font-medium text-[var(--ds-fg)] mb-3">
                <span className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs flex items-center justify-center">1</span>
                规则过滤 (initial_filter.py)
              </h4>
              <ul className="space-y-2 text-sm text-[var(--ds-muted)]">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>语言检测</strong>: 仅保留中文/英文内容</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>内容长度</strong>: 标题 &gt;5字符，正文 &gt;50字符</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>关键词匹配</strong>: 包含 AI/ML/LLM/Agent 等技术词</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span><strong>来源白名单</strong>: 优先处理可信来源</span>
                </li>
              </ul>
            </div>

            {/* LLM 过滤 */}
            <div>
              <h4 className="flex items-center gap-2 font-medium text-[var(--ds-fg)] mb-3">
                <span className="w-6 h-6 rounded-full bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 text-xs flex items-center justify-center">2</span>
                LLM 过滤 (filter.py)
              </h4>
              <p className="text-sm text-[var(--ds-muted)] mb-2">
                满足以下 <strong>任一条件</strong> 即通过:
              </p>
              <ul className="space-y-2 text-sm text-[var(--ds-muted)]">
                <li className="flex items-start gap-2">
                  <span className="text-pink-500 font-medium">A.</span>
                  <span>发布新代码/新模型/新论文</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-pink-500 font-medium">B.</span>
                  <span>包含可复现的实验结果或 Benchmark</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-pink-500 font-medium">C.</span>
                  <span>提供可使用的工具/API/Demo</span>
                </li>
              </ul>
              <p className="text-xs text-[var(--ds-muted)] mt-3 p-2 bg-[var(--ds-surface)] rounded">
                💡 LLM 使用 Moonshot Kimi API 进行智能判断
              </p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-[var(--ds-border)]">
            <p className="text-xs text-[var(--ds-muted)]">
              <Info className="w-3.5 h-3.5 inline mr-1" />
              配置文件位置: <code className="px-1 py-0.5 bg-[var(--ds-surface)] rounded">backend/app/processors/initial_filter.py</code> 和 <code className="px-1 py-0.5 bg-[var(--ds-surface)] rounded">backend/app/processors/filter.py</code>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// ========== 主页面 ==========

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<SourceStatus[]>([])
  const [funnel, setFunnel] = useState<FunnelStats | null>(null)
  const [runs, setRuns] = useState<SourceRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [triggeringSource, setTriggeringSource] = useState<string | null>(null)

  // 使用 useRef 追踪正在进行的触发操作，避免 fetchData 覆盖状态
  const triggeringRef = useRef<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setRefreshing(true)

      // 使用 Promise.allSettled 确保单个请求失败不影响其他请求
      const results = await Promise.allSettled([
        fetch('/api/sources/status', { cache: 'no-store' }),
        fetch('/api/sources/funnel?hours=24', { cache: 'no-store' }),
        fetch('/api/sources/runs?page=1&page_size=20', { cache: 'no-store' }),
      ])

      // 处理 status 响应
      if (results[0].status === 'fulfilled' && results[0].value.ok) {
        const statusData = await results[0].value.json()
        if (statusData.success) {
          setSources(statusData.data.sources)
        }
      }

      // 处理 funnel 响应
      if (results[1].status === 'fulfilled' && results[1].value.ok) {
        const funnelData = await results[1].value.json()
        if (funnelData.success) {
          setFunnel(funnelData.data)
        }
      }

      // 处理 runs 响应
      if (results[2].status === 'fulfilled' && results[2].value.ok) {
        const runsData = await results[2].value.json()
        if (runsData.success) {
          setRuns(runsData.data.items || [])
        }
      }

      // 检查是否全部失败
      const allFailed = results.every(
        (r) => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.ok)
      )
      if (allFailed) {
        setError('无法连接到后端 API')
      } else {
        setError(null)
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
  }, [fetchData])

  const handleToggle = async (sourceType: string) => {
    try {
      const res = await fetch(`/api/sources/toggle/${sourceType}`, {
        method: 'POST',
      })
      if (!res.ok) {
        console.error('Toggle failed:', res.status)
        return
      }
      const data = await res.json()
      if (data.success) {
        fetchData()
      }
    } catch (e) {
      console.error('Toggle error:', e)
    }
  }

  const handleTrigger = async (sourceType: string) => {
    try {
      // 同步更新 ref 和 state
      triggeringRef.current = sourceType
      setTriggeringSource(sourceType)

      const res = await fetch(`/api/sources/trigger/${sourceType}`, {
        method: 'POST',
      })

      if (!res.ok) {
        console.error('Trigger failed:', res.status)
        return
      }

      const data = await res.json()
      if (data.success) {
        // 延迟刷新，给后端一点时间处理
        // 只在当前触发操作仍在进行时刷新
        setTimeout(() => {
          if (triggeringRef.current === sourceType) {
            fetchData()
          }
        }, 2000)
      }
    } catch (e) {
      console.error('Trigger error:', e)
    } finally {
      // 只有当当前操作是这个 sourceType 时才清除
      if (triggeringRef.current === sourceType) {
        triggeringRef.current = null
        setTriggeringSource(null)
      }
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
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">信号源控制台</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              管理数据采集源，查看采集状态和漏斗数据
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

        {/* 过滤规则说明 */}
        <div className="mb-8">
          <FilteringRulesPanel />
        </div>

        {/* 信号源卡片网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {sources.map((source) => (
            <SourceCard
              key={source.source_type}
              source={source}
              onToggle={() => handleToggle(source.source_type)}
              onTrigger={() => handleTrigger(source.source_type)}
              triggering={triggeringSource === source.source_type}
            />
          ))}
        </div>

        {/* 漏斗图 */}
        {funnel && (
          <div className="mb-8">
            <FunnelChart funnel={funnel} />
          </div>
        )}

        {/* 采集记录 */}
        <RunsTable runs={runs} />
      </div>
    </div>
  )
}
