/**
 * [INPUT]: 依赖 projectId, outputs 数组, onOutputsChange 回调
 * [OUTPUT]: 对外提供 StudioPanel 组件 (NotebookLM 风格右侧 Studio 面板)
 * [POS]: components/research/panels 的右侧 Studio 面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight,
  ChevronDown,
  Plus,
  Loader2,
  CheckCircle2,
  Clock,
  FileText,
  Headphones,
  Video,
  Network,
  FileBarChart,
  Image as ImageIcon,
  Presentation,
  StickyNote,
  Trash2,
  Search,
  BookOpen,
} from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

interface Output {
  id: string
  output_type: string
  title: string
  content?: string
  created_at: string
}

interface Note {
  id: string
  title: string
  content: string
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
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 工具网格项配置 - 设计稿: 2x2 布局，4个工具
// ============================================================

const STUDIO_TOOLS = [
  {
    id: 'mindmap',
    name: '思维导图',
    icon: Network,
    bgColor: '#FEF3E8',
    iconColor: '#D97706',
    description: '生成思维导图',
  },
  {
    id: 'report',
    name: '报告',
    icon: FileBarChart,
    bgColor: '#F0FDF4',
    iconColor: '#16A34A',
    description: '生成研究报告',
  },
  {
    id: 'presentation',
    name: '演示文稿',
    icon: Presentation,
    bgColor: '#F8F9FA',
    iconColor: '#1E3A5F',
    description: '生成演示文稿',
  },
  {
    id: 'audio',
    name: '音频概览',
    icon: Headphones,
    bgColor: '#EEF2FF',
    iconColor: '#4F46E5',
    description: '生成音频总结',
  },
]

// ============================================================
// 工具卡片组件
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
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isLoading}
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
      <span className="text-xs font-normal text-[#272735]">{tool.name}</span>
    </motion.button>
  )
}

// ============================================================
// 输出项组件
// ============================================================

function OutputItem({
  output,
  isExpanded,
  onToggle,
}: {
  output: Output
  isExpanded: boolean
  onToggle: () => void
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

  const getOutputIcon = (type: string) => {
    switch (type) {
      case 'research_report':
        return <FileBarChart className="w-4 h-4" />
      case 'audio':
        return <Headphones className="w-4 h-4" />
      case 'video':
        return <Video className="w-4 h-4" />
      case 'mindmap':
        return <Network className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  return (
    <motion.div
      layout
      className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-sm transition-shadow"
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="mt-0.5 text-[#1E3A5F]">
          {getOutputIcon(output.output_type)}
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
        <div className="mt-0.5 text-gray-400">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
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
            <div className="px-4 py-3 bg-gray-50 max-h-48 overflow-y-auto">
              <div
                className="text-xs text-gray-600 prose prose-xs max-w-none leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: output.content.replace(/\n/g, '<br>'),
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================
// 笔记项组件
// ============================================================

function NoteItem({
  note,
  onDelete,
}: {
  note: Note
  onDelete: () => void
}) {
  return (
    <div className="group flex items-start gap-3 p-3 bg-white rounded-xl border border-gray-200
      hover:shadow-sm transition-all">
      <StickyNote className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-700 line-clamp-2">{note.content}</p>
      </div>
      <button
        onClick={onDelete}
        className="p-1 rounded-md opacity-0 group-hover:opacity-100
          hover:bg-red-50 transition-all shrink-0"
      >
        <Trash2 className="w-3.5 h-3.5 text-red-500" />
      </button>
    </div>
  )
}

// ============================================================
// 主组件
// ============================================================

export default function StudioPanel({
  projectId,
  outputs,
  onOutputsChange,
  isCollapsed = false,
  onToggleCollapse,
}: StudioPanelProps) {
  const apiUrl = getApiUrl()

  // 状态
  const [expandedOutputId, setExpandedOutputId] = useState<string | null>(null)
  const [generatingTool, setGeneratingTool] = useState<string | null>(null)
  const [notes, setNotes] = useState<Note[]>([])

  // Deep Research 状态
  const [researchQuery, setResearchQuery] = useState('')
  const [researching, setResearching] = useState(false)
  const [researchProgress, setResearchProgress] = useState<{
    phase: string
    message: string
    progress: number
  } | null>(null)

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
  // 工具生成
  // ============================================================

  const handleToolClick = async (toolId: string) => {
    if (generatingTool) return

    setGeneratingTool(toolId)

    // 模拟生成过程
    await new Promise((resolve) => setTimeout(resolve, 2000))

    setGeneratingTool(null)
    fetchOutputs()
  }

  // ============================================================
  // 深度研究 (SSE)
  // ============================================================

  const handleStartResearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!researchQuery.trim() || researching) return

    setResearching(true)
    setResearchProgress(null)

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
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.phase) {
                setResearchProgress(data)
              }

              if (data.output) {
                fetchOutputs()
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
      setResearchQuery('')
    }
  }

  // ============================================================
  // 添加笔记
  // ============================================================

  const handleAddNote = () => {
    const newNote: Note = {
      id: Date.now().toString(),
      title: '新笔记',
      content: '',
      created_at: new Date().toISOString(),
    }
    setNotes([newNote, ...notes])
  }

  // ============================================================
  // 删除笔记
  // ============================================================

  const handleDeleteNote = (noteId: string) => {
    setNotes(notes.filter((n) => n.id !== noteId))
  }

  // ============================================================
  // 渲染
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

  // 设计稿: 3条示例笔记
  const sampleNotes = [
    { id: '1', title: 'Reinforcement Learning Theory ...', meta: '5 个来源 · 2 天前' },
    { id: '2', title: '自动驾驶中的感知与决策前沿技术...', meta: 'Briefing Doc · 14 个来源 · 2 天前' },
    { id: '3', title: '强化学习算法与训练框架深度解析', meta: 'Briefing Doc · 5 个来源 · 2 天前' },
  ]

  return (
    <div className="w-[320px] bg-white border-l border-[#E8E5E0] flex flex-col h-full overflow-hidden">
      {/* Header - 设计稿: "Studio" + 折叠图标 */}
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
        {/* 工具网格 - 设计稿: 2x2 布局 */}
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

        {/* 相关笔记 - 设计稿: 标题 + 笔记列表 */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-[#272735]">相关笔记</h3>
          </div>

          <div className="space-y-0">
            {sampleNotes.map((note, index) => (
              <div
                key={note.id}
                className={`py-3 ${index < sampleNotes.length - 1 ? 'border-b border-[#E8E5E0]' : ''}`}
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
