/**
 * [INPUT]: 依赖 projectId, sources 数组, onSourcesChange 回调
 * [OUTPUT]: 对外提供 SourcesPanel 组件
 * [POS]: components/research/panels 的左侧源材料面板
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
}

// ============================================================
// Constants
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// Status Icon Component
// ============================================================

function StatusIcon({ status }: { status: Source['processing_status'] }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'processing':
    case 'pending':
      return <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-500" />
    default:
      return <Clock className="w-4 h-4 text-gray-400" />
  }
}

// ============================================================
// Source Item Component
// ============================================================

function SourceItem({
  source,
  onDelete,
}: {
  source: Source
  onDelete: (id: string) => void
}) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
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
      className="bg-white rounded-lg border border-gray-200 p-3 group"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
          {source.source_type === 'url' ? (
            <LinkIcon className="w-4 h-4 text-purple-600" />
          ) : (
            <FileText className="w-4 h-4 text-purple-600" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <StatusIcon status={source.processing_status} />
            <h4 className="font-medium text-gray-900 text-sm truncate">
              {source.title || '未命名'}
            </h4>
          </div>
          <p className="text-xs text-gray-500 mt-0.5 truncate">
            {source.source_type === 'url' && source.original_url
              ? source.original_url
              : source.source_type}
          </p>
        </div>

        {/* Delete Button */}
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-50 transition-all"
          title="删除源材料"
        >
          {deleting ? (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
          ) : (
            <Trash2 className="w-4 h-4 text-red-500" />
          )}
        </button>
      </div>
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl mx-4"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">添加源材料</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* URL Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
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
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-shadow"
                disabled={adding}
              />
            </div>

            <div className="text-center text-gray-500 text-sm">或</div>

            {/* Text Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
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
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none transition-shadow"
                disabled={adding}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              disabled={adding}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={adding || (!url && !text)}
              className="flex-1 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
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
}: SourcesPanelProps) {
  const [showAddModal, setShowAddModal] = useState(false)

  // --------------------------------------------------------
  // Handlers
  // --------------------------------------------------------

  const handleAddSource = (source: Source) => {
    onSourcesChange([source, ...sources])
  }

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm('确定要删除这个源材料吗？')) return

    try {
      const res = await fetch(`${API_URL}/api/research/sources/${sourceId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        onSourcesChange(sources.filter((s) => s.id !== sourceId))
      }
    } catch (err) {
      console.error('Failed to delete source:', err)
    }
  }

  // --------------------------------------------------------
  // Render
  // --------------------------------------------------------

  return (
    <div className="w-72 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">源材料</h2>
          <span className="text-sm text-gray-500">{sources.length}</span>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="mt-3 w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          添加源材料
        </button>
      </div>

      {/* Source List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <AnimatePresence mode="popLayout">
          {sources.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8 text-gray-500 text-sm"
            >
              <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300" />
              <p>还没有源材料</p>
              <p className="text-xs mt-1">点击上方按钮添加</p>
            </motion.div>
          ) : (
            sources.map((source) => (
              <SourceItem
                key={source.id}
                source={source}
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
