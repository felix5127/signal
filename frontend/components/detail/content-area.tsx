/**
 * [INPUT]: 依赖 MarkdownRenderer, MainPoints, KeyQuotes 组件
 * [OUTPUT]: 对外提供 ContentArea 组件
 * [POS]: detail/ 的主内容区组件，展示原文内容
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { cn } from '@/lib/utils'
import MarkdownRenderer from '../markdown-renderer'
import { MainPoints } from '../main-points'
import { KeyQuotes } from '../key-quotes'

interface MainPoint {
  point: string
  explanation: string
}

interface ContentAreaProps {
  oneSentenceSummary?: string
  summary?: string
  contentMarkdown?: string
  mainPoints?: MainPoint[]
  keyQuotes?: string[]
  className?: string
  showFullAnalysis?: boolean // 移动端展示完整 AI 分析
}

export function ContentArea({
  oneSentenceSummary,
  summary,
  contentMarkdown,
  mainPoints,
  keyQuotes,
  className,
  showFullAnalysis = false,
}: ContentAreaProps) {
  return (
    <div className={cn('space-y-8', className)}>
      {/* 一句话总结 */}
      {oneSentenceSummary && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-indigo-100 dark:border-indigo-800">
          <p className="text-gray-900 dark:text-white leading-relaxed text-lg">
            {oneSentenceSummary}
          </p>
        </div>
      )}

      {/* 移动端：展示完整 AI 分析内容 */}
      {showFullAnalysis && (
        <>
          {/* 详细摘要 */}
          {summary && (
            <section>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                内容摘要
              </h2>
              <div className="prose prose-gray dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {summary}
                </p>
              </div>
            </section>
          )}

          {/* 主要观点 */}
          {mainPoints && mainPoints.length > 0 && (
            <section>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                主要观点
              </h2>
              <MainPoints points={mainPoints} />
            </section>
          )}

          {/* 金句 */}
          {keyQuotes && keyQuotes.length > 0 && (
            <section>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                金句摘录
              </h2>
              <KeyQuotes quotes={keyQuotes} />
            </section>
          )}
        </>
      )}

      {/* 完整内容 */}
      {contentMarkdown && (
        <section>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            完整内容
          </h2>
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
            <MarkdownRenderer content={contentMarkdown} />
          </div>
        </section>
      )}
    </div>
  )
}
