/**
 * [INPUT]: 依赖 projectId, sources 数组, onSourcesChange 回调
 * [OUTPUT]: 对外提供 SourcesPanel 组件 (NotebookLM 风格左侧来源面板)
 * [POS]: components/research/panels 的左侧来源面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Trash2,
  Link as LinkIcon,
  FileText,
  Loader2,
  X,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronLeft,
  Search,
  Globe,
  Zap,
  Check,
} from 'lucide-react'

// ============================================================
// Types
// ============================================================

export interface Source {
  id: string
  project_id: string
  source_type: 'url' | 'pdf' | 'audio' | 'video' | 'text'
  title: string | null
  original_url: string | null
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

interface SourcesPanelProps {
  projectId: string
  sources: Source[]
  onSourcesChange: (sources: Source[]) => void
  selectedSources: string[]
  onSelectedSourcesChange: (ids: string[]) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

// ============================================================
// Constants
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Mercury 风格颜色
const COLORS = {
  background: '#FBFCFD',
  primary: '#1E3A5F',
  purple: '#8B5CF6',
  border: 'rgba(0, 0, 0, 0.06)',
}

// ============================================================
// Status Icon Component
// ============================================================

function StatusIcon({ status }: { status: Source['processing_status'] }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
    case 'processing':
    case 'pending':
      return <Clock className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
    case 'failed':
      return <AlertCircle className="w-3.5 h-3.5 text-red-500" />
    default:
      return <Clock className="w-3.5 h-3.5 text-gray-400" />
  }
}

// ============================================================
// Source Item Component
// ============================================================

function SourceItem({
  source,
  selected,
  onToggle,
  onDelete,
}: {
  source: Source
  selected: boolean
  onToggle: () => void
  onDelete: (id: string) => void
}) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (deleting) return
    setDeleting(true)
    await onDelete(source.id)
    setDeleting(false)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      onClick={onToggle}
      className={`
        group flex items-start gap-3 p-3 rounded-xl cursor-pointer
        transition-all duration-200 border
        ${selected
          ? 'bg-[#1E3A5F]/5 border-[#1E3A5F]/20'
          : 'bg-white border-transparent hover:bg-gray-50 hover:border-gray-200'
        }
      `}
    >
      {/* Checkbox */}
      <div className={`
        w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 mt-0.5
        transition-colors duration-200
        ${selected
          ? 'bg-[#1E3A5F] border-[#1E3A5F]'
          : 'border-gray-300 group-hover:border-gray-400'
        }
      `}>
        {selected && <Check className="w-3 h-3 text-white" />}
      </div>

      {/* Icon */}
      <div className={`
        w-8 h-8 rounded-lg flex items-center justify-center shrink-0
        ${source.source_type === 'url' ? 'bg-blue-50' : 'bg-amber-50'}
      `}>
        {source.source_type === 'url' ? (
          <LinkIcon className="w-4 h-4 text-blue-600" />
        ) : (
          <FileText className="w-4 h-4 text-amber-600" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <h4 className="font-medium text-[#1E3A5F] text-sm truncate leading-tight">
            {source.title || '未命名'}
          </h4>
          <StatusIcon status={source.processing_status} />
        </div>
        <p className="text-xs text-gray-500 mt-0.5 truncate">
          {source.source_type === 'url' && source.original_url
            ? new URL(source.original_url).hostname
            : source.source_type}
        </p>
      </div>

      {/* Delete Button */}
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-50 transition-all shrink-0"
        title="删除来源"
      >
        {deleting ? (
          <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
        ) : (
          <Trash2 className="w-4 h-4 text-red-500" />
        )}
      </button>
    </motion.div>
  )
}

// ============================================================
// Add Source Modal
// ============================================================

function AddSourceModal({
  projectId,
  onClose,
  onAdd,
}: {
  projectId: string
  onClose: () => void
  onAdd: (source: Source) => void
}) {
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url && !text) return

    setAdding(true)
    setError(null)

    try {
      const body: {
        source_type: string
        original_url?: string
        content?: string
        title?: string
      } = {
        source_type: url ? 'url' : 'text',
      }

      if (url) {
        body.original_url = url
        try {
          body.title = new URL(url).hostname
        } catch {
          body.title = url.substring(0, 50)
        }
      } else if (text) {
        body.content = text
        body.title = text.substring(0, 50) + (text.length > 50 ? '...' : '')
      }

      const res = await fetch(
        `${API_URL}/api/research/projects/${projectId}/sources`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }
      )

      if (!res.ok) {
        throw new Error('添加失败')
      }

      const source = await res.json()
      onAdd(source)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : '添加失败')
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl mx-4"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-semibold text-[#1E3A5F]">添加来源</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* URL Input */}
            <div>
              <label className="block text-sm font-medium text-[#1E3A5F] mb-2">
                URL 链接
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value)
                  if (e.target.value) setText('')
                }}
                placeholder="https://example.com/article"
                className="w-full px-4 py-3 bg-[#FBFCFD] border border-gray-200 rounded-xl
                  focus:ring-2 focus:ring-[#1E3A5F]/20 focus:border-[#1E3A5F]
                  transition-all outline-none text-[#1E3A5F]"
                disabled={adding}
              />
            </div>

            <div className="text-center text-gray-400 text-sm font-medium">或</div>

            {/* Text Input */}
            <div>
              <label className="block text-sm font-medium text-[#1E3A5F] mb-2">
                文本内容
              </label>
              <textarea
                value={text}
                onChange={(e) => {
                  setText(e.target.value)
                  if (e.target.value) setUrl('')
                }}
                placeholder="粘贴文本内容..."
                rows={4}
                className="w-full px-4 py-3 bg-[#FBFCFD] border border-gray-200 rounded-xl
                  focus:ring-2 focus:ring-[#1E3A5F]/20 focus:border-[#1E3A5F]
                  transition-all resize-none outline-none text-[#1E3A5F]"
                disabled={adding}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl
                hover:bg-gray-50 transition-colors font-medium text-gray-600"
              disabled={adding}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={adding || (!url && !text)}
              className="flex-1 px-4 py-3 bg-[#1E3A5F] text-white rounded-xl
                hover:bg-[#1E3A5F]/90 transition-colors
                disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {adding ? (
                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
              ) : (
                '添加'
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

// ============================================================
// Main Component
// ============================================================

export default function SourcesPanel({
  projectId,
  sources,
  onSourcesChange,
  selectedSources,
  onSelectedSourcesChange,
  isCollapsed = false,
  onToggleCollapse,
}: SourcesPanelProps) {
  const [showAddModal, setShowAddModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // --------------------------------------------------------
  // Handlers
  // --------------------------------------------------------

  const handleAddSource = (source: Source) => {
    onSourcesChange([source, ...sources])
  }

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm('确定要删除这个来源吗？')) return

    try {
      const res = await fetch(`${API_URL}/api/research/sources/${sourceId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        onSourcesChange(sources.filter((s) => s.id !== sourceId))
        onSelectedSourcesChange(selectedSources.filter((id) => id !== sourceId))
      }
    } catch (err) {
      console.error('Failed to delete source:', err)
    }
  }

  const handleToggleSource = (sourceId: string) => {
    if (selectedSources.includes(sourceId)) {
      onSelectedSourcesChange(selectedSources.filter((id) => id !== sourceId))
    } else {
      onSelectedSourcesChange([...selectedSources, sourceId])
    }
  }

  const handleSelectAll = () => {
    if (selectedSources.length === sources.length) {
      onSelectedSourcesChange([])
    } else {
      onSelectedSourcesChange(sources.map((s) => s.id))
    }
  }

  // 过滤来源
  const filteredSources = sources.filter((source) =>
    source.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    source.original_url?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // --------------------------------------------------------
  // Render
  // --------------------------------------------------------

  if (isCollapsed) {
    return (
      <div className="w-12 bg-white border-r border-gray-200 flex flex-col items-center py-4">
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600 rotate-180" />
        </button>
      </div>
    )
  }

  return (
    <div className="w-[300px] bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-[#272735] text-base">来源</h2>
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-[#6B6B6B]" />
            </button>
          )}
        </div>

        {/* Add Source Button - 设计稿: 边框按钮 */}
        <button
          onClick={() => setShowAddModal(true)}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-3
            text-sm border border-[#E8E5E0] rounded-[10px]
            hover:bg-gray-50 transition-colors font-medium text-[#6B6B6B]"
        >
          <Plus className="w-[18px] h-[18px]" />
          添加来源
        </button>
      </div>

      {/* Search */}
      <div className="px-5 py-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9A9A9A]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="在网络中搜索新来源"
            className="w-full pl-10 pr-4 py-2.5 bg-[#F5F3F0] rounded-[10px]
              text-sm focus:ring-2 focus:ring-[#1E3A5F]/20
              transition-all outline-none placeholder:text-[#9A9A9A] text-[#272735]"
          />
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-2 mt-3">
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E8E5E0]
            rounded-full text-xs font-medium text-[#6B6B6B] hover:bg-gray-50 transition-colors">
            <Globe className="w-3.5 h-3.5" />
            Web
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E8E5E0]
            rounded-full text-xs font-medium text-[#6B6B6B] hover:bg-gray-50 transition-colors">
            <Zap className="w-3.5 h-3.5" />
            Fast Research
          </button>
        </div>
      </div>

      {/* Select All */}
      {sources.length > 0 && (
        <div className="px-5 py-3">
          <button
            onClick={handleSelectAll}
            className="flex items-center gap-2 text-sm text-[#272735] hover:text-[#1E3A5F] transition-colors"
          >
            <div className={`
              w-[18px] h-[18px] rounded border-2 flex items-center justify-center
              transition-colors duration-200
              ${selectedSources.length === sources.length
                ? 'bg-[#1E3A5F] border-[#1E3A5F]'
                : 'border-[#1E3A5F]'
              }
            `}>
              {selectedSources.length === sources.length && (
                <Check className="w-3 h-3 text-white" />
              )}
            </div>
            <span>选择所有来源</span>
            <span className="text-[#9A9A9A]">({sources.length})</span>
          </button>
        </div>
      )}

      {/* Source List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <AnimatePresence mode="popLayout">
          {filteredSources.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 text-gray-500"
            >
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-sm font-medium">还没有来源</p>
              <p className="text-xs mt-1 text-gray-400">点击上方按钮添加</p>
            </motion.div>
          ) : (
            filteredSources.map((source) => (
              <SourceItem
                key={source.id}
                source={source}
                selected={selectedSources.includes(source.id)}
                onToggle={() => handleToggleSource(source.id)}
                onDelete={handleDeleteSource}
              />
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Add Source Modal */}
      <AnimatePresence>
        {showAddModal && (
          <AddSourceModal
            projectId={projectId}
            onClose={() => setShowAddModal(false)}
            onAdd={handleAddSource}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
