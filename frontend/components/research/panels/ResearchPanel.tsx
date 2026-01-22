/**
 * [INPUT]: 依赖 projectId, outputs 数组, onOutputsChange 回调
 * [OUTPUT]: 对外提供 ResearchPanel 组件
 * [POS]: components/research/panels 的右侧研究面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  BookOpen,
  Loader2,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  FileText,
} from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

interface ResearchProgress {
  phase: string
  message: string
  progress: number
  data?: { output?: string }
}

interface Output {
  id: string
  output_type: string
  title: string
  content?: string
  created_at: string
}

interface ResearchPanelProps {
  projectId: string
  outputs: Output[]
  onOutputsChange: (outputs: Output[]) => void
}

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 研究面板组件
// ============================================================

export default function ResearchPanel({
  projectId,
  outputs,
  onOutputsChange,
}: ResearchPanelProps) {
  const apiUrl = getApiUrl()

  // 研究状态
  const [researchQuery, setResearchQuery] = useState('')
  const [researching, setResearching] = useState(false)
  const [researchProgress, setResearchProgress] = useState<ResearchProgress | null>(null)
  const [researchResult, setResearchResult] = useState<string | null>(null)

  // 输出展开状态
  const [expandedOutputId, setExpandedOutputId] = useState<string | null>(null)

  // ============================================================
  // 研究功能 (SSE)
  // ============================================================

  const handleStartResearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!researchQuery.trim() || researching) return

    setResearching(true)
    setResearchProgress(null)
    setResearchResult(null)

    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: researchQuery,
          include_web_search: true,
          max_iterations: 5,
        }),
      })

      if (!res.ok) {
        throw new Error('Research request failed')
      }

      // SSE 流式读取
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            // 事件类型，暂不处理
            continue
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.phase) {
                setResearchProgress(data)
              }

              if (data.output) {
                setResearchResult(data.output)
                // 刷新输出列表
                fetchOutputs()
              }

              if (data.error) {
                console.error('Research error:', data.error)
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (e) {
      console.error('Research failed:', e)
    } finally {
      setResearching(false)
    }
  }

  // ============================================================
  // 获取输出列表
  // ============================================================

  const fetchOutputs = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/outputs`)
      if (res.ok) {
        const data = await res.json()
        onOutputsChange(data)
      }
    } catch (e) {
      console.error('Failed to fetch outputs:', e)
    }
  }, [apiUrl, projectId, onOutputsChange])

  // ============================================================
  // 输出展开/收起
  // ============================================================

  const toggleOutputExpand = (outputId: string) => {
    setExpandedOutputId(prev => (prev === outputId ? null : outputId))
  }

  // ============================================================
  // 格式化时间
  // ============================================================

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // ============================================================
  // 输出类型图标
  // ============================================================

  const getOutputIcon = (type: string) => {
    switch (type) {
      case 'research_report':
        return <BookOpen className="w-4 h-4" />
      case 'summary':
        return <FileText className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  // ============================================================
  // 渲染
  // ============================================================

  return (
    <div className="w-80 h-full bg-gray-50 border-l border-gray-200 flex flex-col">
      {/* 深度研究区 */}
      <div className="p-4 border-b border-gray-200">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Search className="w-4 h-4 text-purple-600" />
            深度研究
          </h3>

          <form onSubmit={handleStartResearch}>
            <textarea
              value={researchQuery}
              onChange={(e) => setResearchQuery(e.target.value)}
              placeholder="输入研究问题..."
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              disabled={researching}
            />

            <button
              type="submit"
              disabled={researching || !researchQuery.trim()}
              className="mt-3 w-full px-3 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {researching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  研究中...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  开始研究
                </>
              )}
            </button>
          </form>

          {/* 研究进度 */}
          <AnimatePresence>
            {researchProgress && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 overflow-hidden"
              >
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    {researchProgress.phase === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                    )}
                    <span className="text-xs font-medium text-gray-700">
                      {researchProgress.message}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <motion.div
                      className="bg-purple-600 h-1.5 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${researchProgress.progress * 100}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 研究结果预览 */}
          <AnimatePresence>
            {researchResult && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 overflow-hidden"
              >
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span className="text-xs font-semibold text-green-700">研究完成</span>
                  </div>
                  <p className="text-xs text-gray-600 line-clamp-3">
                    {researchResult.substring(0, 150)}...
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 输出列表区 */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-purple-600" />
          研究输出
          {outputs.length > 0 && (
            <span className="text-xs text-gray-500">({outputs.length})</span>
          )}
        </h3>

        {outputs.length === 0 ? (
          <div className="text-center py-8">
            <BookOpen className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-xs text-gray-500">还没有研究输出</p>
            <p className="text-xs text-gray-400 mt-1">发起研究后，报告会显示在这里</p>
          </div>
        ) : (
          <div className="space-y-2">
            {outputs.map((output) => (
              <motion.div
                key={output.id}
                layout
                className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* 输出标题行 */}
                <button
                  onClick={() => toggleOutputExpand(output.id)}
                  className="w-full px-3 py-2.5 flex items-start gap-2 text-left hover:bg-gray-50 transition-colors"
                >
                  <div className="mt-0.5 text-purple-600">
                    {getOutputIcon(output.output_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
                      {output.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                        {output.output_type}
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(output.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="mt-0.5 text-gray-400">
                    {expandedOutputId === output.id ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                </button>

                {/* 展开内容 */}
                <AnimatePresence>
                  {expandedOutputId === output.id && output.content && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="border-t border-gray-100"
                    >
                      <div className="px-3 py-2 bg-gray-50 max-h-48 overflow-y-auto">
                        <div
                          className="text-xs text-gray-600 prose prose-xs max-w-none"
                          dangerouslySetInnerHTML={{
                            __html: output.content.replace(/\n/g, '<br>'),
                          }}
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
