/**
 * [INPUT]: 依赖 lucide-react, @/lib/utils
 * [OUTPUT]: 对外提供 QARecap 组件
 * [POS]: podcast/ 的 Q&A 回顾组件，展示提取的问答对
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { ChevronDown, MessageCircle, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface QAPair {
  question: string
  answer: string
  timestamp?: number // 对应的时间戳（秒）
}

interface QARecapProps {
  qaPairs: QAPair[]
  className?: string
}

export function QARecap({ qaPairs, className }: QARecapProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0) // 默认展开第一个

  if (!qaPairs || qaPairs.length === 0) {
    return (
      <div className={cn('text-center py-12', className)}>
        <HelpCircle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">暂无 Q&A 内容</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          AI 正在分析播客内容，请稍后查看
        </p>
      </div>
    )
  }

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index)
  }

  return (
    <div className={cn('space-y-4', className)}>
      {qaPairs.map((qa, index) => {
        const isExpanded = expandedIndex === index

        return (
          <div
            key={index}
            className={cn(
              'rounded-xl border transition-all',
              isExpanded
                ? 'border-indigo-200 dark:border-indigo-700 bg-indigo-50/50 dark:bg-indigo-900/20'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900'
            )}
          >
            {/* 问题 */}
            <button
              onClick={() => toggleExpand(index)}
              className="w-full flex items-start gap-3 p-4 text-left"
            >
              <div
                className={cn(
                  'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
                  isExpanded
                    ? 'bg-indigo-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                )}
              >
                <MessageCircle className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0">
                <h4
                  className={cn(
                    'font-medium leading-snug',
                    isExpanded
                      ? 'text-indigo-900 dark:text-indigo-100'
                      : 'text-gray-900 dark:text-white'
                  )}
                >
                  {qa.question}
                </h4>
              </div>

              <ChevronDown
                className={cn(
                  'flex-shrink-0 w-5 h-5 text-gray-400 transition-transform',
                  isExpanded && 'rotate-180'
                )}
              />
            </button>

            {/* 答案 */}
            {isExpanded && (
              <div className="px-4 pb-4 pt-0">
                <div className="ml-11 pl-4 border-l-2 border-indigo-300 dark:border-indigo-600">
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {qa.answer}
                  </p>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
