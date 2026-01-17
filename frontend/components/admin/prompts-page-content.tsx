/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/admin/prompts/*)
 * [OUTPUT]: 对外提供 Admin Prompt 版本管理页面
 * [POS]: admin/ 的 Prompt 管理页面，展示/激活/创建 Prompt 版本
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import {
  RefreshCw,
  AlertTriangle,
  Plus,
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  Zap,
  FileText,
  Loader2,
  Star,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'

// ========== 类型定义 ==========

interface Prompt {
  id: number
  name: string
  version: number
  type: string
  system_prompt: string
  user_prompt_template: string
  status: 'active' | 'inactive'
  total_used: number
  avg_score: number | null
  approval_rate: number | null
  created_at: string
  activated_at: string | null
}

interface CreatePromptForm {
  name: string
  type: string
  system_prompt: string
  user_prompt_template: string
}

// ========== 辅助函数 ==========

const formatDate = (isoString: string | null) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatScore = (score: number | null) => {
  if (score === null) return '-'
  return score.toFixed(1)
}

const formatRate = (rate: number | null) => {
  if (rate === null) return '-'
  return `${(rate * 100).toFixed(1)}%`
}

// ========== 组件 ==========

function PromptCard({
  prompt,
  onActivate,
  activating,
}: {
  prompt: Prompt
  onActivate: () => void
  activating: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const isActive = prompt.status === 'active'

  return (
    <div
      className={`bg-[var(--ds-bg)] rounded-xl border-2 transition-all ${
        isActive
          ? 'border-green-300 dark:border-green-700'
          : 'border-[var(--ds-border)]'
      }`}
    >
      {/* 头部信息 */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-500" />
            <span className="font-medium text-[var(--ds-fg)]">{prompt.name}</span>
            <span className="px-2 py-0.5 text-xs rounded bg-[var(--ds-surface)] text-[var(--ds-muted)] font-mono">
              v{prompt.version}
            </span>
          </div>
          {isActive ? (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <CheckCircle className="w-3 h-3" />
              激活中
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
              <Clock className="w-3 h-3" />
              未激活
            </span>
          )}
        </div>

        {/* 类型标签 */}
        <div className="mb-3">
          <span className="px-2 py-1 text-xs rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
            {prompt.type}
          </span>
        </div>

        {/* 统计数据 */}
        <div className="grid grid-cols-3 gap-4 mb-3">
          <div className="text-center">
            <div className="text-lg font-semibold text-[var(--ds-fg)]">
              {prompt.total_used}
            </div>
            <div className="text-xs text-[var(--ds-muted)]">使用次数</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-[var(--ds-fg)] flex items-center justify-center gap-1">
              {formatScore(prompt.avg_score)}
              {prompt.avg_score !== null && (
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
              )}
            </div>
            <div className="text-xs text-[var(--ds-muted)]">平均评分</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-[var(--ds-fg)]">
              {formatRate(prompt.approval_rate)}
            </div>
            <div className="text-xs text-[var(--ds-muted)]">通过率</div>
          </div>
        </div>

        {/* 时间信息 */}
        <div className="flex items-center justify-between text-xs text-[var(--ds-muted)]">
          <span>创建: {formatDate(prompt.created_at)}</span>
          {prompt.activated_at && (
            <span>激活: {formatDate(prompt.activated_at)}</span>
          )}
        </div>
      </div>

      {/* 展开/收起按钮 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 border-t border-[var(--ds-border)] text-sm text-[var(--ds-muted)] hover:bg-[var(--ds-surface)] transition-colors"
      >
        {expanded ? (
          <>
            <ChevronDown className="w-4 h-4" />
            收起 Prompt 内容
          </>
        ) : (
          <>
            <ChevronRight className="w-4 h-4" />
            查看 Prompt 内容
          </>
        )}
      </button>

      {/* 展开内容 */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-[var(--ds-border)]">
          {/* System Prompt */}
          <div className="pt-4">
            <h4 className="text-sm font-medium text-[var(--ds-fg)] mb-2">
              System Prompt
            </h4>
            <pre className="p-3 bg-[var(--ds-surface)] rounded-lg text-xs text-[var(--ds-muted)] whitespace-pre-wrap break-words max-h-48 overflow-y-auto">
              {prompt.system_prompt}
            </pre>
          </div>

          {/* User Prompt Template */}
          <div>
            <h4 className="text-sm font-medium text-[var(--ds-fg)] mb-2">
              User Prompt Template
            </h4>
            <pre className="p-3 bg-[var(--ds-surface)] rounded-lg text-xs text-[var(--ds-muted)] whitespace-pre-wrap break-words max-h-48 overflow-y-auto">
              {prompt.user_prompt_template}
            </pre>
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      {!isActive && (
        <div className="px-4 pb-4">
          <button
            onClick={onActivate}
            disabled={activating}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {activating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            激活此版本
          </button>
        </div>
      )}
    </div>
  )
}

function CreatePromptDialog({
  open,
  onOpenChange,
  onSubmit,
  submitting,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (form: CreatePromptForm) => void
  submitting: boolean
}) {
  const [form, setForm] = useState<CreatePromptForm>({
    name: '',
    type: 'filter',
    system_prompt: '',
    user_prompt_template: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  const handleClose = () => {
    if (!submitting) {
      setForm({
        name: '',
        type: 'filter',
        system_prompt: '',
        user_prompt_template: '',
      })
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-[var(--ds-bg)] border-[var(--ds-border)]">
        <DialogHeader>
          <DialogTitle className="text-[var(--ds-fg)]">创建新版本 Prompt</DialogTitle>
          <DialogDescription className="text-[var(--ds-muted)]">
            创建新的 Prompt 版本，创建后需要手动激活
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-[var(--ds-fg)] mb-1">
              名称
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="例如: signal_filter_v2"
              required
              className="w-full px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] placeholder:text-[var(--ds-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-[var(--ds-fg)] mb-1">
              类型
            </label>
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="filter">filter (过滤)</option>
              <option value="analyzer">analyzer (分析)</option>
              <option value="translator">translator (翻译)</option>
              <option value="summarizer">summarizer (摘要)</option>
            </select>
          </div>

          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-[var(--ds-fg)] mb-1">
              System Prompt
            </label>
            <Textarea
              value={form.system_prompt}
              onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              placeholder="输入系统提示词..."
              required
              rows={6}
              className="w-full px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] placeholder:text-[var(--ds-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          {/* User Prompt Template */}
          <div>
            <label className="block text-sm font-medium text-[var(--ds-fg)] mb-1">
              User Prompt Template
            </label>
            <Textarea
              value={form.user_prompt_template}
              onChange={(e) =>
                setForm({ ...form, user_prompt_template: e.target.value })
              }
              placeholder="输入用户提示词模板，可使用 {title}, {content} 等变量..."
              required
              rows={6}
              className="w-full px-3 py-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg)] text-[var(--ds-fg)] placeholder:text-[var(--ds-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          <DialogFooter className="gap-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--ds-surface)] text-[var(--ds-fg)] hover:bg-[var(--ds-border)] disabled:opacity-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              创建
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ========== 主页面 ==========

export default function PromptsPageContent() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [activatingId, setActivatingId] = useState<number | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const fetchData = async () => {
    try {
      setRefreshing(true)
      const res = await fetch('/api/admin/prompts', { cache: 'no-store' })
      const data = await res.json()

      if (data.success) {
        setPrompts(data.data || [])
        setError(null)
      } else {
        setError(data.error || '获取 Prompt 列表失败')
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
    fetchData()
  }, [])

  const handleActivate = async (id: number) => {
    try {
      setActivatingId(id)
      const res = await fetch(`/api/admin/prompts/${id}/activate`, {
        method: 'POST',
      })
      const data = await res.json()
      if (data.success) {
        fetchData()
      } else {
        console.error('Activate error:', data.error)
      }
    } catch (e) {
      console.error('Activate error:', e)
    } finally {
      setActivatingId(null)
    }
  }

  const handleCreate = async (form: CreatePromptForm) => {
    try {
      setSubmitting(true)
      const res = await fetch('/api/admin/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (data.success) {
        setDialogOpen(false)
        fetchData()
      } else {
        console.error('Create error:', data.error)
      }
    } catch (e) {
      console.error('Create error:', e)
    } finally {
      setSubmitting(false)
    }
  }

  // 按类型分组
  const groupedPrompts = prompts.reduce(
    (acc, prompt) => {
      const type = prompt.type
      if (!acc[type]) {
        acc[type] = []
      }
      acc[type].push(prompt)
      return acc
    },
    {} as Record<string, Prompt[]>
  )

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
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">Prompt 版本管理</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              管理和追踪不同版本的 Prompt，查看效果数据
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              刷新
            </button>
            <button
              onClick={() => setDialogOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              创建新版本
            </button>
          </div>
        </div>

        {/* 按类型分组显示 */}
        {Object.keys(groupedPrompts).length > 0 ? (
          <div className="space-y-8">
            {Object.entries(groupedPrompts).map(([type, typePrompts]) => (
              <div key={type}>
                <h2 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
                  <span className="px-2 py-1 text-sm rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                    {type}
                  </span>
                  <span className="text-[var(--ds-muted)] text-sm font-normal">
                    ({typePrompts.length} 个版本)
                  </span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {typePrompts.map((prompt) => (
                    <PromptCard
                      key={prompt.id}
                      prompt={prompt}
                      onActivate={() => handleActivate(prompt.id)}
                      activating={activatingId === prompt.id}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-12 text-center">
            <FileText className="w-12 h-12 text-[var(--ds-muted)] mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--ds-fg)] mb-2">
              暂无 Prompt
            </h3>
            <p className="text-[var(--ds-muted)] mb-4">
              点击「创建新版本」按钮创建第一个 Prompt
            </p>
            <button
              onClick={() => setDialogOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              创建新版本
            </button>
          </div>
        )}

        {/* 创建对话框 */}
        <CreatePromptDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSubmit={handleCreate}
          submitting={submitting}
        />
      </div>
    </div>
  )
}
