/**
 * [INPUT]: 依赖 lucide-react 图标, ScoreBadge 组件
 * [OUTPUT]: 对外提供 AISidebar 组件
 * [POS]: detail/ 的 AI 分析侧边栏组件，展示评分/摘要/观点/金句
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Brain, Lightbulb, Quote, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScoreBadge } from '../score-badge'

interface MainPoint {
  point: string
  explanation: string
}

interface AISidebarProps {
  score?: number
  isFeatured?: boolean
  summary?: string
  mainPoints?: MainPoint[]
  keyQuotes?: string[]
  className?: string
}

export function AISidebar({
  score,
  isFeatured,
  summary,
  mainPoints,
  keyQuotes,
  className,
}: AISidebarProps) {
  return (
    <div className={cn('space-y-5', className)}>
      {/* AI 评分 */}
      {score !== undefined && score > 0 && (
        <div className="rounded-xl p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-200/60 dark:border-indigo-700/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <span className="text-sm font-semibold text-indigo-900 dark:text-indigo-300">
                AI 评分
              </span>
            </div>
            <ScoreBadge score={score} isFeatured={isFeatured} size="lg" />
          </div>
        </div>
      )}

      {/* AI 摘要 */}
      {summary && (
        <div className="rounded-xl p-4 bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              AI 摘要
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed line-clamp-6">
            {summary}
          </p>
        </div>
      )}

      {/* 主要观点 */}
      {mainPoints && mainPoints.length > 0 && (
        <div className="rounded-xl p-4 bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              主要观点
            </h3>
          </div>
          <ul className="space-y-2">
            {mainPoints.slice(0, 5).map((item, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300"
              >
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-white text-xs flex items-center justify-center mt-0.5">
                  {index + 1}
                </span>
                <span className="leading-relaxed line-clamp-2">{item.point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 金句摘录 */}
      {keyQuotes && keyQuotes.length > 0 && (
        <div className="rounded-xl p-4 bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-3">
            <Quote className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              金句摘录
            </h3>
          </div>
          <div className="space-y-3">
            {keyQuotes.slice(0, 3).map((quote, index) => (
              <blockquote
                key={index}
                className="pl-3 border-l-2 border-amber-400 text-sm text-gray-600 dark:text-gray-300 italic leading-relaxed line-clamp-3"
              >
                &ldquo;{quote}&rdquo;
              </blockquote>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
