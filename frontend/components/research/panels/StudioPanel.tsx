/**
 * [INPUT]: 依赖 projectId, outputs 数组, onOutputsChange 回调, useSSE Hook
 * [OUTPUT]: 对外提供 StudioPanel 组件 (NotebookLM 风格右侧 Studio 面板)
 * [POS]: components/research/panels 的右侧 Studio 面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight,
  ChevronDown,
  Loader2,
  Clock,
  FileText,
  Headphones,
  Video,
  Network,
  FileBarChart,
  Presentation,
  Trash2,
} from 'lucide-react'
import { useSSE } from '@/hooks/use-sse'

// ============================================================
// 类型定义
// ============================================================

interface Output {
  id: string
  output_type: string
  title: string
  content?: string
  content_format?: string
  created_at: string
}

interface StudioPanelProps {
  projectId: string
  outputs: Output[]
  onOutputsChange: (outputs: Output[]) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

// ============================================================
// API 配置
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 设计稿占位笔记
// ============================================================

const SAMPLE_NOTES = [
  { id: '1', title: 'Reinforcement Learning Theory ...', meta: '5 个来源 · 2 天前' },
  { id: '2', title: '自动驾驶中的感知与决策前沿技术...', meta: 'Briefing Doc · 14 个来源 · 2 天前' },
  { id: '3', title: '强化学习算法与训练框架深度解析', meta: 'Briefing Doc · 5 个来源 · 2 天前' },
]

// ============================================================
// 工具网格配置 — 2x2 布局
// ============================================================

const STUDIO_TOOLS = [
  {
    id: 'mindmap',
    name: '思维导图',
    icon: Network,
    bgColor: '#FEF3E8',
    iconColor: '#D97706',
    enabled: true,
  },
  {
    id: 'report',
    name: '报告',
    icon: FileBarChart,
    bgColor: '#F0FDF4',
    iconColor: '#16A34A',
    enabled: true,
  },
  {
    id: 'presentation',
    name: '演示文稿',
    icon: Presentation,
    bgColor: '#F8F9FA',
    iconColor: '#1E3A5F',
    enabled: false,
  },
  {
    id: 'audio',
    name: '音频概览',
    icon: Headphones,
    bgColor: '#EEF2FF',
    iconColor: '#4F46E5',
    enabled: false,
  },
]

// ============================================================
// 子组件: 工具卡片
// ============================================================

interface ToolCardProps {
  tool: typeof STUDIO_TOOLS[0]
  onClick: () => void
  isLoading?: boolean
}

function ToolCard({ tool, onClick, isLoading }: ToolCardProps) {
  const Icon = tool.icon

  return (
    <motion.button
      whileHover={tool.enabled ? { scale: 1.02 } : undefined}
      whileTap={tool.enabled ? { scale: 0.98 } : undefined}
      onClick={onClick}
      disabled={!tool.enabled || isLoading}
      className="flex flex-col items-start gap-2 p-4 rounded-xl h-20
        transition-all hover:shadow-sm
        disabled:opacity-50 disabled:cursor-not-allowed"
      style={{ backgroundColor: tool.bgColor }}
    >
      {isLoading ? (
        <Loader2 className="w-5 h-5 animate-spin" style={{ color: tool.iconColor }} />
      ) : (
        <Icon className="w-5 h-5" style={{ color: tool.iconColor }} />
      )}
      <div className="flex flex-col">
        <span className="text-xs font-normal text-[#272735]">{tool.name}</span>
        {!tool.enabled && (
          <span className="text-[10px] text-gray-400">即将推出</span>
        )}
      </div>
    </motion.button>
  )
}

// ============================================================
// 子组件: 输出项 (可展开)
// ============================================================

const OUTPUT_ICONS: Record<string, typeof FileText> = {
  report: FileBarChart,
  research_report: FileBarChart,
  mindmap: Network,
  audio: Headphones,
  video: Video,
}

function OutputItem({
  output,
  isExpanded,
  onToggle,
  onDelete,
}: {
  output: Output
  isExpanded: boolean
  onToggle: () => void
  onDelete: () => void
}) {
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const Icon = OUTPUT_ICONS[output.output_type] || FileText

  return (
    <motion.div
      layout
      className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-sm transition-shadow"
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="mt-0.5 text-[#1E3A5F]">
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-[#1E3A5F] line-clamp-2">
            {output.title}
          </h4>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(output.created_at)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 mt-0.5">
          <button
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            className="p-1 rounded-md opacity-0 group-hover:opacity-100
              hover:bg-red-50 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5 text-red-400 hover:text-red-500" />
          </button>
          <div className="text-gray-400">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && output.content && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-100"
          >
            <div className="px-4 py-3 bg-gray-50 max-h-64 overflow-y-auto">
              <pre className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">
                {output.content}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================
// 主组件: StudioPanel
// ============================================================

export default function StudioPanel({
  projectId,
  outputs,
  onOutputsChange,
  isCollapsed = false,
  onToggleCollapse,
}: StudioPanelProps) {

  // 状态
  const [expandedOutputId, setExpandedOutputId] = useState<string | null>(null)
  const [generatingTool, setGeneratingTool] = useState<string | null>(null)
  const wasStreamingRef = useRef(false)

  const sse = useSSE()

  // ============================================================
  // 获取输出列表
  // ============================================================

  const fetchOutputs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/research/projects/${projectId}/outputs`)
      if (res.ok) {
        const data = await res.json()
        onOutputsChange(data)
      }
    } catch {
      // 静默失败
    }
  }, [projectId, onOutputsChange])

  // ============================================================
  // 流式结束处理: 刷新输出列表
  // ============================================================

  useEffect(() => {
    const wasStreaming = wasStreamingRef.current
    wasStreamingRef.current = sse.isStreaming

    if (wasStreaming && !sse.isStreaming) {
      setGeneratingTool(null)
      fetchOutputs()
    }
  }, [sse.isStreaming, fetchOutputs])

  // ============================================================
  // 工具点击 — 启动 SSE 生成
  // ============================================================

  const handleToolClick = (toolId: string) => {
    if (toolId !== 'report' && toolId !== 'mindmap') return
    if (sse.isStreaming || generatingTool) return

    setGeneratingTool(toolId)

    const endpoint = toolId === 'report'
      ? `${API_URL}/api/research/projects/${projectId}/generate/report`
      : `${API_URL}/api/research/projects/${projectId}/generate/mindmap`

    sse.start(endpoint, {})
  }

  // ============================================================
  // 删除输出
  // ============================================================

  const handleDeleteOutput = async (outputId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/research/outputs/${outputId}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        onOutputsChange(outputs.filter(o => o.id !== outputId))
      }
    } catch {
      // 静默失败
    }
  }

  // ============================================================
  // 折叠态渲染
  // ============================================================

  if (isCollapsed) {
    return (
      <div className="w-12 bg-white border-l border-gray-200 flex flex-col items-center py-4">
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-gray-600 rotate-180" />
        </button>
      </div>
    )
  }

  // ============================================================
  // 完整渲染
  // ============================================================

  return (
    <div className="w-[320px] bg-white border-l border-[#E8E5E0] flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-5 py-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-[#272735] text-base">Studio</h2>
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-[#6B6B6B]" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5">
        {/* 工具网格 — 2x2 */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {STUDIO_TOOLS.map((tool) => (
            <ToolCard
              key={tool.id}
              tool={tool}
              onClick={() => handleToolClick(tool.id)}
              isLoading={generatingTool === tool.id}
            />
          ))}
        </div>

        {/* 生成进度 */}
        {generatingTool && sse.isStreaming && (
          <div className="mb-4 p-3 bg-gray-50 rounded-xl border border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="w-4 h-4 animate-spin text-[#1E3A5F]" />
              <span className="text-xs font-medium text-[#272735]">
                正在生成{generatingTool === 'report' ? '报告' : '思维导图'}...
              </span>
            </div>
            {sse.content && (
              <p className="text-xs text-gray-500 line-clamp-3">
                {sse.content.slice(0, 200)}
              </p>
            )}
          </div>
        )}

        {/* 生成错误 */}
        {sse.error && !sse.isStreaming && (
          <div className="mb-4 p-3 bg-red-50 rounded-xl border border-red-200">
            <p className="text-xs text-red-600">生成失败，请重试</p>
          </div>
        )}

        {/* 研究输出列表 */}
        {outputs.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-[#272735] mb-3">
              研究输出 ({outputs.length})
            </h3>
            <div className="space-y-2">
              {outputs.map(output => (
                <OutputItem
                  key={output.id}
                  output={output}
                  isExpanded={expandedOutputId === output.id}
                  onToggle={() =>
                    setExpandedOutputId(
                      expandedOutputId === output.id ? null : output.id
                    )
                  }
                  onDelete={() => handleDeleteOutput(output.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* 相关笔记 (设计稿占位) */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-[#272735]">相关笔记</h3>
          </div>

          <div className="space-y-0">
            {SAMPLE_NOTES.map((note, index) => (
              <div
                key={note.id}
                className={`py-3 ${index < SAMPLE_NOTES.length - 1 ? 'border-b border-[#E8E5E0]' : ''}`}
              >
                <h4 className="text-[13px] font-medium text-[#272735] mb-1 line-clamp-1">
                  {note.title}
                </h4>
                <p className="text-xs text-[#9A9A9A]">{note.meta}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
