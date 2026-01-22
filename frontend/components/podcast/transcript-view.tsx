/**
 * [INPUT]: 依赖 @/lib/utils
 * [OUTPUT]: 对外提供 TranscriptView 组件
 * [POS]: podcast/ 的转录文本展示组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { Search, Copy, Check, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TranscriptViewProps {
  transcript?: string
  className?: string
}

// 转义正则表达式特殊字符，防止 ReDoS 攻击
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function TranscriptView({ transcript, className }: TranscriptViewProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [copied, setCopied] = useState(false)

  if (!transcript) {
    return (
      <div className={cn('text-center py-12', className)}>
        <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">暂无转录文本</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          转录功能需要处理音频，请稍后查看
        </p>
      </div>
    )
  }

  // 搜索高亮
  const highlightText = (text: string) => {
    if (!searchQuery.trim()) return text

    // 转义用户输入，防止 ReDoS
    const escapedQuery = escapeRegExp(searchQuery)
    const regex = new RegExp(`(${escapedQuery})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark
          key={index}
          className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded"
        >
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  // 复制全文
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(transcript)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // 按段落分割
  const paragraphs = transcript.split('\n\n').filter((p) => p.trim())

  return (
    <div className={className}>
      {/* 工具栏 */}
      <div className="flex items-center gap-3 mb-4">
        {/* 搜索框 */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索转录内容..."
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        {/* 复制按钮 */}
        <button
          onClick={handleCopy}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg transition-all',
            copied
              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          )}
        >
          {copied ? (
            <>
              <Check className="w-4 h-4" />
              <span>已复制</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              <span>复制全文</span>
            </>
          )}
        </button>
      </div>

      {/* 转录内容 */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 max-h-[600px] overflow-y-auto">
        <div className="prose prose-gray dark:prose-invert max-w-none">
          {paragraphs.map((paragraph, index) => (
            <p key={index} className="mb-4 last:mb-0 leading-relaxed">
              {highlightText(paragraph)}
            </p>
          ))}
        </div>
      </div>

      {/* 字数统计 */}
      <div className="mt-3 text-sm text-gray-500 dark:text-gray-400">
        共 {transcript.length.toLocaleString()} 字符
        {searchQuery && (
          <span className="ml-2">
            · 找到 {(transcript.match(new RegExp(escapeRegExp(searchQuery), 'gi')) || []).length} 处匹配
          </span>
        )}
      </div>
    </div>
  )
}
