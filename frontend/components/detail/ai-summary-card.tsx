/**
 * [INPUT]: 依赖 lucide-react 图标
 * [OUTPUT]: 对外提供 AISummaryCard 组件
 * [POS]: detail/ 的 AI 摘要卡片组件，展示 AI 生成的内容摘要
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Sparkles } from 'lucide-react'

interface AISummaryCardProps {
  summary?: string
  oneSentenceSummary?: string
  className?: string
}

export function AISummaryCard({
  summary,
  oneSentenceSummary,
  className,
}: AISummaryCardProps) {
  const displayContent = summary || oneSentenceSummary

  if (!displayContent) return null

  return (
    <div
      className={`rounded-2xl p-5 w-full bg-white border border-[rgba(0,0,0,0.06)] ${className || ''}`}
    >
      {/* 标题行 */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-[15px] font-semibold text-[#272735]">
          AI 摘要
        </h3>
      </div>

      {/* 摘要内容 */}
      <p className="text-[14px] text-[#6B6B6B] leading-[1.7]">
        {displayContent}
      </p>
    </div>
  )
}
