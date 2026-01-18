/**
 * [INPUT]: 依赖 React useState/useEffect/useCallback、lucide-react 图标、framer-motion 动画
 * [OUTPUT]: 对外提供全局搜索组件 (Cmd+K 搜索框)
 * [POS]: components/ 的全局搜索组件，被 layout 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  X,
  FileText,
  Folder,
  BookOpen,
  Loader2,
  ArrowRight,
  Command,
} from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

interface SearchResult {
  id: string
  type: 'source' | 'output' | 'resource' | 'project'
  title: string
  content_preview: string
  score: number
  metadata: Record<string, any>
}

interface SearchResponse {
  success: boolean
  query: string
  total: number
  scope: string
  results: SearchResult[]
}

// ============================================================
// 常量配置
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const TYPE_ICONS = {
  source: FileText,
  output: BookOpen,
  resource: FileText,
  project: Folder,
}

const TYPE_LABELS = {
  source: '源材料',
  output: '研究输出',
  resource: '资源',
  project: '项目',
}

const TYPE_COLORS = {
  source: 'bg-blue-100 text-blue-700',
  output: 'bg-green-100 text-green-700',
  resource: 'bg-purple-100 text-purple-700',
  project: 'bg-orange-100 text-orange-700',
}

// ============================================================
// 全局搜索组件
// ============================================================

export default function GlobalSearch() {
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)

  const inputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  // ============================================================
  // 键盘快捷键
  // ============================================================

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K 或 Ctrl+K 打开搜索
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }

      // Escape 关闭搜索
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  // ============================================================
  // 搜索逻辑
  // ============================================================

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    setLoading(true)

    try {
      const response = await fetch(
        `${API_URL}/api/search?q=${encodeURIComponent(searchQuery)}&limit=10`
      )

      if (response.ok) {
        const data: SearchResponse = await response.json()
        setResults(data.results)
        setSelectedIndex(0)
      }
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  // 防抖搜索
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      performSearch(query)
    }, 300)

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [query, performSearch])

  // 聚焦输入框
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // ============================================================
  // 导航逻辑
  // ============================================================

  const handleSelect = (result: SearchResult) => {
    setIsOpen(false)
    setQuery('')
    setResults([])

    // 根据类型导航到不同页面
    switch (result.type) {
      case 'source':
        if (result.metadata.project_id) {
          router.push(`/research/${result.metadata.project_id}?source=${result.id}`)
        }
        break
      case 'output':
        if (result.metadata.project_id) {
          router.push(`/research/${result.metadata.project_id}?output=${result.id}`)
        }
        break
      case 'resource':
        router.push(`/resources/${result.id}`)
        break
      case 'project':
        router.push(`/research/${result.id}`)
        break
    }
  }

  // 键盘导航
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      e.preventDefault()
      handleSelect(results[selectedIndex])
    }
  }

  // ============================================================
  // 渲染
  // ============================================================

  return (
    <>
      {/* 搜索触发按钮 */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        <Search className="w-4 h-4" />
        <span className="hidden sm:inline">搜索...</span>
        <kbd className="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-gray-200 rounded">
          <Command className="w-3 h-3" />K
        </kbd>
      </button>

      {/* 搜索弹窗 */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* 遮罩层 */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-50"
              onClick={() => setIsOpen(false)}
            />

            {/* 搜索面板 */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
            >
              <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
                {/* 搜索输入 */}
                <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
                  <Search className="w-5 h-5 text-gray-400" />
                  <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="搜索项目、源材料、研究输出..."
                    className="flex-1 text-base outline-none placeholder:text-gray-400"
                  />
                  {loading && <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>

                {/* 搜索结果 */}
                <div className="max-h-[400px] overflow-y-auto">
                  {results.length === 0 && query && !loading && (
                    <div className="px-4 py-8 text-center text-gray-500">
                      未找到相关结果
                    </div>
                  )}

                  {results.length === 0 && !query && (
                    <div className="px-4 py-8 text-center text-gray-500">
                      <p className="mb-2">输入关键词开始搜索</p>
                      <p className="text-sm">支持搜索项目、源材料、研究输出</p>
                    </div>
                  )}

                  {results.map((result, index) => {
                    const Icon = TYPE_ICONS[result.type] || FileText
                    const isSelected = index === selectedIndex

                    return (
                      <button
                        key={`${result.type}-${result.id}`}
                        onClick={() => handleSelect(result)}
                        onMouseEnter={() => setSelectedIndex(index)}
                        className={`w-full flex items-start gap-3 px-4 py-3 text-left transition-colors ${
                          isSelected ? 'bg-purple-50' : 'hover:bg-gray-50'
                        }`}
                      >
                        {/* 图标 */}
                        <div className={`p-2 rounded-lg ${TYPE_COLORS[result.type]}`}>
                          <Icon className="w-4 h-4" />
                        </div>

                        {/* 内容 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 truncate">
                              {result.title}
                            </span>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${TYPE_COLORS[result.type]}`}>
                              {TYPE_LABELS[result.type]}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 line-clamp-1 mt-0.5">
                            {result.content_preview}
                          </p>
                        </div>

                        {/* 箭头 */}
                        {isSelected && (
                          <ArrowRight className="w-4 h-4 text-purple-600 mt-1" />
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* 底部提示 */}
                <div className="flex items-center justify-between px-4 py-2 bg-gray-50 text-xs text-gray-500 border-t border-gray-200">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-white rounded border">↑</kbd>
                      <kbd className="px-1.5 py-0.5 bg-white rounded border">↓</kbd>
                      导航
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-white rounded border">Enter</kbd>
                      选择
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-white rounded border">Esc</kbd>
                      关闭
                    </span>
                  </div>
                  {results.length > 0 && (
                    <span>{results.length} 条结果</span>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
