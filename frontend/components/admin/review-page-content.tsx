/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/admin/review/*)
 * [OUTPUT]: 对外提供 Admin 内容审核页面
 * [POS]: admin/ 的内容审核页面，人工审核 LLM 筛选结果
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useCallback } from 'react'
import { formatTime } from '@/lib/admin-utils'
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  MessageSquare,
  Filter,
  BarChart3,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

// ========== 类型定义 ==========

interface ReviewItem {
  id: number
  title: string
  url: string
  source_name: string
  llm_score: number
  llm_reason: string
  review_status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

interface ReviewListResponse {
  items: ReviewItem[]
  total: number
  page: number
  page_size: number
}

interface ReviewStats {
  total: number
  pending: number
  approved: number
  rejected: number
  today_reviewed: number
}

type FilterStatus = 'all' | 'pending' | 'approved' | 'rejected'

// ========== 状态标签映射 ==========

const STATUS_CONFIG: Record<FilterStatus, { label: string; color: string; bgColor: string }> = {
  all: { label: '全部', color: 'text-[var(--ds-fg)]', bgColor: 'bg-[var(--ds-surface)]' },
  pending: { label: '待审核', color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20' },
  approved: { label: '已通过', color: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-50 dark:bg-green-900/20' },
  rejected: { label: '已拒绝', color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-50 dark:bg-red-900/20' },
}

// ========== 工具函数 ==========

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400'
  if (score >= 60) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function getScoreBgColor(score: number): string {
  if (score >= 80) return 'bg-green-50 dark:bg-green-900/20'
  if (score >= 60) return 'bg-yellow-50 dark:bg-yellow-900/20'
  return 'bg-red-50 dark:bg-red-900/20'
}

// ========== 统计卡片组件 ==========

function StatsCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: number
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-[var(--ds-muted)]">{label}</p>
          <p className="text-2xl font-bold text-[var(--ds-fg)] mt-1">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

// ========== 筛选标签组件 ==========

function FilterTabs({
  activeFilter,
  onFilterChange,
  stats,
}: {
  activeFilter: FilterStatus
  onFilterChange: (filter: FilterStatus) => void
  stats: ReviewStats | null
}) {
  const filters: { key: FilterStatus; count: number | undefined }[] = [
    { key: 'all', count: stats?.total },
    { key: 'pending', count: stats?.pending },
    { key: 'approved', count: stats?.approved },
    { key: 'rejected', count: stats?.rejected },
  ]

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {filters.map(({ key, count }) => {
        const config = STATUS_CONFIG[key]
        const isActive = activeFilter === key
        return (
          <button
            key={key}
            onClick={() => onFilterChange(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                : 'bg-[var(--ds-surface)] text-[var(--ds-muted)] hover:bg-[var(--ds-bg)] hover:text-[var(--ds-fg)]'
            }`}
          >
            {config.label}
            {count !== undefined && (
              <span
                className={`px-1.5 py-0.5 rounded text-xs ${
                  isActive
                    ? 'bg-indigo-200 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-300'
                    : 'bg-[var(--ds-bg)] text-[var(--ds-muted)]'
                }`}
              >
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

// ========== 审核项卡片组件 ==========

function ReviewItemCard({
  item,
  onApprove,
  onReject,
  processing,
}: {
  item: ReviewItem
  onApprove: () => void
  onReject: (comment: string) => void
  processing: boolean
}) {
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectComment, setRejectComment] = useState('')

  const handleReject = () => {
    onReject(rejectComment)
    setShowRejectModal(false)
    setRejectComment('')
  }

  const statusConfig = STATUS_CONFIG[item.review_status]

  return (
    <>
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
              <span className="text-xs text-[var(--ds-muted)]">{item.source_name}</span>
            </div>
            <h3 className="font-medium text-[var(--ds-fg)] line-clamp-2">{item.title}</h3>
          </div>
          <div className={`flex-shrink-0 px-3 py-1.5 rounded-lg ${getScoreBgColor(item.llm_score)}`}>
            <span className={`text-lg font-bold ${getScoreColor(item.llm_score)}`}>{item.llm_score}</span>
          </div>
        </div>

        {/* LLM Reason */}
        <div className="mb-4 p-3 rounded-lg bg-[var(--ds-surface)]">
          <div className="flex items-center gap-1.5 mb-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-[var(--ds-muted)]" />
            <span className="text-xs font-medium text-[var(--ds-muted)]">LLM 评估</span>
          </div>
          <p className="text-sm text-[var(--ds-fg)] leading-relaxed">{item.llm_reason || '暂无评估理由'}</p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-[var(--ds-muted)]">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatTime(item.created_at)}
            </span>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-indigo-500 hover:text-indigo-600 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              查看原文
            </a>
          </div>

          {/* Action Buttons */}
          {item.review_status === 'pending' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowRejectModal(true)}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <XCircle className="w-4 h-4" />
                拒绝
              </button>
              <button
                onClick={onApprove}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {processing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                通过
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">拒绝原因</h3>
            <textarea
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              placeholder="请输入拒绝原因（可选）..."
              className="w-full h-24 px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-surface)] text-[var(--ds-fg)] placeholder:text-[var(--ds-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
            <div className="flex items-center justify-end gap-3 mt-4">
              <button
                onClick={() => {
                  setShowRejectModal(false)
                  setRejectComment('')
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--ds-muted)] hover:bg-[var(--ds-surface)] transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleReject}
                disabled={processing}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                确认拒绝
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// ========== 分页组件 ==========

function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium bg-[var(--ds-surface)] text-[var(--ds-muted)] hover:bg-[var(--ds-bg)] hover:text-[var(--ds-fg)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        上一页
      </button>
      <span className="px-4 py-2 text-sm text-[var(--ds-muted)]">
        {page} / {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium bg-[var(--ds-surface)] text-[var(--ds-muted)] hover:bg-[var(--ds-bg)] hover:text-[var(--ds-fg)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        下一页
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}

// ========== 主页面组件 ==========

export default function ReviewPageContent() {
  const [items, setItems] = useState<ReviewItem[]>([])
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [processingId, setProcessingId] = useState<number | null>(null)
  const [filter, setFilter] = useState<FilterStatus>('pending')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const totalPages = Math.ceil(total / pageSize)

  // 获取审核统计
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/review/stats', { cache: 'no-store' })
      const data = await res.json()
      if (data.success !== false) {
        setStats(data)
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e)
    }
  }, [])

  // 获取审核列表
  const fetchList = useCallback(async () => {
    try {
      setRefreshing(true)
      const status = filter === 'all' ? '' : filter
      const queryParams = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        ...(status && { status }),
      })

      const res = await fetch(`/api/admin/review/list?${queryParams}`, { cache: 'no-store' })
      const data: ReviewListResponse = await res.json()

      if (data.items) {
        setItems(data.items)
        setTotal(data.total)
      }
      setError(null)
    } catch (e) {
      setError('无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [filter, page])

  // 初始加载和刷新
  useEffect(() => {
    fetchList()
    fetchStats()
  }, [fetchList, fetchStats])

  // 处理审核操作
  const handleAction = async (resourceId: number, action: 'approve' | 'reject', comment?: string) => {
    try {
      setProcessingId(resourceId)
      const res = await fetch(`/api/admin/review/${resourceId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...(comment && { comment }) }),
      })

      const data = await res.json()
      if (data.success !== false) {
        // 刷新列表和统计
        fetchList()
        fetchStats()
      }
    } catch (e) {
      console.error('Action error:', e)
    } finally {
      setProcessingId(null)
    }
  }

  // 刷新数据
  const handleRefresh = () => {
    fetchList()
    fetchStats()
  }

  // 筛选变化时重置页码
  const handleFilterChange = (newFilter: FilterStatus) => {
    setFilter(newFilter)
    setPage(1)
  }

  // 加载中状态
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

  // 错误状态
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-8 max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--ds-fg)] mb-2">{error}</h2>
            <button onClick={handleRefresh} className="text-indigo-600 hover:text-indigo-700 transition-colors">
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
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">内容审核</h1>
            <p className="text-[var(--ds-muted)] mt-1">人工审核 LLM 筛选结果，确保内容质量</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            <StatsCard label="总计" value={stats.total} icon={BarChart3} color="bg-indigo-500" />
            <StatsCard label="待审核" value={stats.pending} icon={Clock} color="bg-yellow-500" />
            <StatsCard label="已通过" value={stats.approved} icon={CheckCircle} color="bg-green-500" />
            <StatsCard label="已拒绝" value={stats.rejected} icon={XCircle} color="bg-red-500" />
            <StatsCard label="今日审核" value={stats.today_reviewed} icon={Filter} color="bg-purple-500" />
          </div>
        )}

        {/* 筛选标签 */}
        <div className="mb-6">
          <FilterTabs activeFilter={filter} onFilterChange={handleFilterChange} stats={stats} />
        </div>

        {/* 审核列表 */}
        <div className="space-y-4">
          {items.map((item) => (
            <ReviewItemCard
              key={item.id}
              item={item}
              onApprove={() => handleAction(item.id, 'approve')}
              onReject={(comment) => handleAction(item.id, 'reject', comment)}
              processing={processingId === item.id}
            />
          ))}

          {items.length === 0 && (
            <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-[var(--ds-surface)] flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="text-lg font-medium text-[var(--ds-fg)] mb-2">
                {filter === 'pending' ? '没有待审核的内容' : '暂无数据'}
              </h3>
              <p className="text-[var(--ds-muted)]">
                {filter === 'pending' ? '所有内容都已审核完成' : '当前筛选条件下没有内容'}
              </p>
            </div>
          )}
        </div>

        {/* 分页 */}
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </div>
  )
}
