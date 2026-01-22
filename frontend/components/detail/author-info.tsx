/**
 * [INPUT]: 依赖 lucide-react 图标，资源的 author/source 信息
 * [OUTPUT]: 对外提供 AuthorInfo 组件
 * [POS]: detail/ 的作者信息卡组件，用于侧边栏展示
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { User, Globe, Calendar, Clock, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AuthorInfoProps {
  author?: string
  sourceName: string
  sourceIconUrl?: string
  publishedAt?: string
  readTime?: number
  wordCount?: number
  className?: string
}

// 来源名称映射
const SOURCE_NAMES: Record<string, string> = {
  hn: 'Hacker News',
  github: 'GitHub',
  huggingface: 'Hugging Face',
  twitter: 'Twitter / X',
  arxiv: 'ArXiv',
  producthunt: 'Product Hunt',
  blog: '博客',
}

// 格式化阅读时间
function formatReadTime(minutes?: number): string {
  if (!minutes) return ''
  if (minutes < 60) {
    return `${minutes} 分钟`
  }
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

// 验证图片 URL 安全性，防止 javascript: 等危险协议
function isSafeImageUrl(url?: string): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    return ['http:', 'https:', 'data:'].includes(parsed.protocol)
  } catch {
    // 相对路径也是安全的
    return url.startsWith('/') || url.startsWith('./')
  }
}

export function AuthorInfo({
  author,
  sourceName,
  sourceIconUrl,
  publishedAt,
  readTime,
  wordCount,
  className,
}: AuthorInfoProps) {
  const displaySourceName = SOURCE_NAMES[sourceName] || sourceName

  return (
    <div
      className={cn(
        'rounded-xl p-4 space-y-4',
        'bg-gray-50 dark:bg-gray-800/50',
        'border border-gray-200 dark:border-gray-700',
        className
      )}
    >
      <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        来源信息
      </h3>

      {/* 作者 */}
      {author && (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-semibold text-sm">
            {author.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {author}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">作者</p>
          </div>
        </div>
      )}

      {/* 来源 */}
      <div className="flex items-center gap-3">
        {isSafeImageUrl(sourceIconUrl) ? (
          <img
            src={sourceIconUrl}
            alt={displaySourceName}
            className="w-5 h-5 rounded"
            onError={(e) => {
              const target = e.target as HTMLImageElement
              target.style.display = 'none'
            }}
          />
        ) : (
          <Globe className="w-5 h-5 text-gray-400" />
        )}
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {displaySourceName}
        </span>
      </div>

      {/* 发布日期 */}
      {publishedAt && (
        <div className="flex items-center gap-3">
          <Calendar className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            {new Date(publishedAt).toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>
      )}

      {/* 阅读时长 */}
      {readTime && (
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            阅读 {formatReadTime(readTime)}
          </span>
        </div>
      )}

      {/* 字数 */}
      {wordCount && (
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            {wordCount.toLocaleString()} 字
          </span>
        </div>
      )}
    </div>
  )
}
