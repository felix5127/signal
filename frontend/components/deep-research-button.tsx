/**
 * [INPUT]: 依赖 React useState、lucide-react 图标、Next.js useRouter
 * [OUTPUT]: 对外提供深度研究按钮，点击后创建研究项目并跳转到工作台
 * [POS]: components/ 的深度研究入口组件，被 resource-detail.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Loader2, AlertCircle } from 'lucide-react'

interface DeepResearchProps {
  resourceId: number
  resourceTitle: string
  resourceContent?: string  // 资源内容，用于添加到研究项目
  resourceUrl?: string      // 资源原始链接
}

// 按钮样式配置 - 使用与"阅读原文"按钮一致的 Mercury 风格颜色
const buttonStyles = {
  default: {
    background: '#1E3A5F',
  },
  hover: {
    background: '#152840',
  },
  loading: {
    background: '#9ca3af',
  },
}

// API URL helper
const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DeepResearchButton({
  resourceId,
  resourceTitle,
  resourceContent,
  resourceUrl,
}: DeepResearchProps) {
  const router = useRouter()
  const apiUrl = getApiUrl()
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  // ============================================================
  // 核心逻辑: 创建项目 → 添加源材料 → 跳转工作台
  // ============================================================
  const handleClick = async () => {
    if (status === 'loading') return

    setStatus('loading')
    setError(null)

    try {
      // Step 1: 创建研究项目
      const projectName = `研究: ${resourceTitle.substring(0, 50)}`
      const projectRes = await fetch(`${apiUrl}/api/research/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: projectName,
          description: `基于资源 #${resourceId} 的深度研究`,
        }),
      })

      if (!projectRes.ok) {
        throw new Error('创建研究项目失败')
      }

      const project = await projectRes.json()
      const projectId = project.id

      // Step 2: 添加源材料（如果有内容或链接）
      if (resourceContent || resourceUrl) {
        const sourceBody: {
          source_type: string
          title: string
          original_url?: string
          content?: string
        } = {
          source_type: resourceUrl ? 'url' : 'text',
          title: resourceTitle,
        }

        if (resourceUrl) {
          sourceBody.original_url = resourceUrl
        }
        if (resourceContent) {
          sourceBody.content = resourceContent
        }

        await fetch(`${apiUrl}/api/research/projects/${projectId}/sources`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sourceBody),
        })
        // 不检查结果，源材料添加失败不影响跳转
      }

      // Step 3: 跳转到研究工作台
      router.push(`/research/workspace/${projectId}`)
    } catch (e: any) {
      console.error('[DeepResearch] Error:', e)
      setStatus('error')
      setError(e.message || '操作失败，请重试')
    }
  }

  // ============================================================
  // 渲染 - 使用与"阅读原文"按钮一致的 Mercury 风格
  // ============================================================
  return (
    <div>
      <button
        onClick={handleClick}
        disabled={status === 'loading'}
        className={`group inline-flex items-center gap-2 px-7 py-3.5 rounded-[10px] text-white text-base font-medium transition-all ${
          status === 'loading'
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-[#1E3A5F] hover:bg-[#152840] cursor-pointer'
        }`}
      >
        {status === 'loading' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            创建研究项目...
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
    </div>
  )
}
