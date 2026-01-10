/**
 * [INPUT]: 依赖 React useState/useEffect、markdown-renderer 组件、lucide-react 图标、Next.js useRouter
 * [OUTPUT]: 对外提供深度研究按钮和报告展示组件，点击后跳转到研究页面
 * [POS]: components/ 的深度研究交互组件，被 resource-detail.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, CheckCircle2, Loader2, AlertCircle, BookOpen, Clock } from 'lucide-react'
import MarkdownRenderer from './markdown-renderer'

interface DeepResearchProps {
  resourceId: number
  resourceType?: 'signal' | 'resource'
  inline?: boolean  // 内联模式：只显示按钮，不显示报告
  reportOnly?: boolean  // 仅报告模式：只显示报告内容（用于独立展示区）
}

interface ResearchReport {
  resource_id: number
  title: string
  content: string
  generated_at: string | null
  tokens_used: number
  cost_usd: number
  strategy: string
  sources: string[]
  metadata: Record<string, any>
}

// 预估生成时间（秒）
const ESTIMATED_SECONDS = 180

// 按钮样式配置 - 统一立体阴影系统
const buttonStyles = {
  default: {
    background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
    boxShadow: '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
    hoverBoxShadow: '0 6px 20px color-mix(in srgb, var(--primary) 45%, transparent), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.15)',
  },
  loading: {
    background: '#9ca3af',
    boxShadow: '0 4px 12px rgba(156, 163, 175, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
  polling: {
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
    hoverBoxShadow: '0 6px 20px rgba(59, 130, 246, 0.45), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.15)',
  },
  success: {
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
}

export default function DeepResearchButton({ resourceId, resourceType = 'resource', inline = false, reportOnly = false }: DeepResearchProps) {
  const router = useRouter()
  const [status, setStatus] = useState<'idle' | 'loading' | 'polling' | 'success' | 'error'>('idle')
  const [report, setReport] = useState<ResearchReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pollingCount, setPollingCount] = useState(0)

  // 计算剩余时间
  const getRemainingTime = () => {
    const remaining = Math.max(0, ESTIMATED_SECONDS - pollingCount * 5)
    if (remaining > 60) {
      return `${Math.ceil(remaining / 60)}分${remaining % 60}秒`
    }
    return `${remaining}秒`
  }

  // 使用相对路径
  const getApiUrl = (path: string) => {
    // 开发环境直接访问后端，绕过 Next.js 代理
    return process.env.NODE_ENV === 'development'
      ? `http://localhost:8000/api/resources/${resourceId}/deep-research${path}`
      : `/api/resources/${resourceId}/deep-research${path}`
  }

  // 检查是否已有报告
  useEffect(() => {
    checkExistingReport()
  }, [resourceId])

  const checkExistingReport = async () => {
    try {
      const res = await fetch(getApiUrl(''))
      if (res.ok) {
        const result = await res.json()
        const reportData = result.data || result

        // Defensive: Ensure sources is always an array
        if (reportData.sources && typeof reportData.sources === 'string') {
          // If it's a string, try to parse it as JSON
          try {
            const parsed = JSON.parse(reportData.sources)
            reportData.sources = Array.isArray(parsed) ? parsed : [parsed]
          } catch {
            // If parsing fails, split by comma or create single-item array
            reportData.sources = reportData.sources.split(',').map((s: string) => s.trim())
          }
        } else if (!reportData.sources) {
          reportData.sources = []
        }

        setReport(reportData)
        setStatus('success')
      }
    } catch (e) {
      // 报告不存在，保持 idle 状态
    }
  }

  // 轮询检查报告状态
  useEffect(() => {
    if (status !== 'polling') return

    const interval = setInterval(async () => {
      setPollingCount(prev => prev + 1)

      try {
        const res = await fetch(getApiUrl(''))
        if (res.ok) {
          const result = await res.json()
          const reportData = result.data || result
          setReport(reportData)
          setStatus('success')
          setPollingCount(0)
        }
      } catch (e) {
        // 继续轮询
      }
      // 移除120s超时限制，持续轮询直到成功或用户离开页面
    }, 5000)

    return () => clearInterval(interval)
  }, [status, pollingCount, resourceId])

  const handleGenerate = async () => {
    setStatus('loading')
    setError(null)

    try {
      const apiUrl = getApiUrl('?strategy=lightweight')
      console.log('[DeepResearch] 发起请求:', apiUrl)

      const res = await fetch(apiUrl, { method: 'POST' })

      console.log('[DeepResearch] 响应状态:', res.status)

      if (!res.ok) {
        const errorText = await res.text()
        console.error('[DeepResearch] 请求失败:', errorText)
        throw new Error(`生成请求失败 (${res.status})`)
      }

      const data = await res.json()
      console.log('[DeepResearch] 响应数据:', data)

      if (data.data?.status === 'cached') {
        // 已有缓存报告，直接显示
        console.log('[DeepResearch] 使用缓存报告')
        await checkExistingReport()
      } else {
        // 任务已启动 (status: pending)，显示生成中状态，2秒后跳转
        console.log('[DeepResearch] 任务已启动，准备跳转到研究页面')
        setStatus('polling')
        // 设置2秒后自动跳转到研究页面，让用户看到生成状态
        setTimeout(() => {
          router.push('/research')
        }, 2000)
      }
    } catch (e: any) {
      console.error('[DeepResearch] 错误:', e)
      setStatus('error')
      setError(e.message || '生成失败，请重试')
    }
  }

  // 仅报告模式：只显示报告内容
  if (reportOnly) {
    if (status === 'success' && report) {
      return (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-2xl p-8 border-2 border-gray-200 dark:border-gray-800">
          <div className="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-200 dark:border-gray-800">
            <div>
              <div className="text-xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Search className="w-5 h-5 text-purple-600" />
                深度研究报告
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                生成于 {report.generated_at ? new Date(report.generated_at).toLocaleString('zh-CN') : '未知'}
                {' • '}Token: {report.tokens_used}
                {' • '}成本: ${report.cost_usd?.toFixed(4) || '0.0000'}
              </div>
            </div>
          </div>

          {/* Markdown 内容渲染 */}
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed text-base">
            <MarkdownRenderer content={report.content} />
          </div>

          {/* 来源列表 */}
          {report.sources && report.sources.length > 0 && (
            <div className="mt-8 pt-6 border-t-2 border-gray-200 dark:border-gray-800">
              <div className="text-base font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                参考来源 ({report.sources.length})
              </div>
              <ul className="list-none p-0">
                {report.sources.slice(0, 5).map((source, idx) => (
                  <li key={idx} className="mb-2">
                    <a
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 dark:text-purple-400 text-sm no-underline hover:underline transition-all"
                    >
                      [{idx + 1}] {source}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )
    }
    return null  // 没有报告时不显示任何内容
  }

  // 内联模式：只显示按钮
  if (inline) {
    const baseButtonClass = "inline-flex items-center gap-2 px-6 py-3 rounded-xl border-none font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"

    if (status === 'success' && report) {
      return (
        <button
          disabled
          className={`${baseButtonClass} text-white opacity-80 cursor-default`}
          style={buttonStyles.success}
        >
          <CheckCircle2 className="w-4 h-4" />
          已生成报告
        </button>
      )
    }

    if (status === 'polling') {
      return (
        <button
          disabled
          className={`${baseButtonClass} text-white cursor-wait`}
          style={buttonStyles.polling}
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          剩余 {getRemainingTime()}
        </button>
      )
    }

    const currentStyle = status === 'loading' ? buttonStyles.loading : buttonStyles.default

    return (
      <button
        onClick={handleGenerate}
        disabled={status === 'loading'}
        className={`${baseButtonClass} text-white ${status === 'loading' ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        style={currentStyle}
        onMouseEnter={(e) => {
          if (status !== 'loading') {
            e.currentTarget.style.boxShadow = buttonStyles.default.hoverBoxShadow
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = currentStyle.boxShadow
        }}
      >
        {status === 'loading' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            提交中...
          </>
        ) : (
          <>
            <Search className="w-4 h-4" />
            深度研究
          </>
        )}
      </button>
    )
  }

  // 完整模式（默认）：显示紧凑按钮和报告
  const baseButtonClass = "inline-flex items-center gap-2 px-6 py-3 rounded-xl border-none font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"

  // 根据状态选择样式
  const getButtonStyle = () => {
    if (status === 'polling') return buttonStyles.polling
    if (status === 'loading') return buttonStyles.loading
    if (status === 'success' && report) return buttonStyles.success
    return buttonStyles.default
  }

  const currentButtonStyle = getButtonStyle()
  const canHover = status !== 'loading' && status !== 'polling'

  return (
    <div>
      {/* 紧凑按钮：始终显示 */}
      <button
        onClick={handleGenerate}
        disabled={status === 'loading' || status === 'polling'}
        className={`${baseButtonClass} text-white ${status === 'loading' || status === 'polling' ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        style={currentButtonStyle}
        onMouseEnter={(e) => {
          if (canHover) {
            e.currentTarget.style.boxShadow = buttonStyles.default.hoverBoxShadow
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = currentButtonStyle.boxShadow
        }}
      >
        {status === 'success' && report ? (
          <>
            <CheckCircle2 className="w-4 h-4" />
            已生成报告
          </>
        ) : status === 'polling' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            剩余 {getRemainingTime()}
          </>
        ) : status === 'loading' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            提交中...
          </>
        ) : (
          <>
            <Search className="w-4 h-4" />
            深度研究
          </>
        )}
      </button>

      {/* 错误提示 */}
      {status === 'error' && error && (
        <div className="mt-3 text-red-500 text-sm flex items-center gap-1">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* 报告展示 */}
      {status === 'success' && report && (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-2xl p-8 mt-4 border-2 border-gray-200 dark:border-gray-800">
          <div className="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-200 dark:border-gray-800">
            <div>
              <div className="text-xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Search className="w-5 h-5 text-purple-600" />
                深度研究报告
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                生成于 {report.generated_at ? new Date(report.generated_at).toLocaleString('zh-CN') : '未知'}
                {' • '}Token: {report.tokens_used}
                {' • '}成本: ${report.cost_usd?.toFixed(4) || '0.0000'}
              </div>
            </div>
          </div>

          {/* Markdown 内容渲染 */}
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed text-base">
            <MarkdownRenderer content={report.content} />
          </div>

          {/* 来源列表 */}
          {report.sources && report.sources.length > 0 && (
            <div className="mt-8 pt-6 border-t-2 border-gray-200 dark:border-gray-800">
              <div className="text-base font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                参考来源 ({report.sources.length})
              </div>
              <ul className="list-none p-0">
                {report.sources.slice(0, 5).map((source, idx) => (
                  <li key={idx} className="mb-2">
                    <a
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 dark:text-purple-400 text-sm no-underline hover:underline transition-all"
                    >
                      [{idx + 1}] {source}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
