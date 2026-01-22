/**
 * [INPUT]: 依赖 lucide-react 的 Sparkles 图标
 * [OUTPUT]: 对外提供 FeaturedReason 组件
 * [POS]: detail/ 的精选理由组件，展示"为什么值得看"
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FeaturedReasonProps {
  reason?: string
  className?: string
}

export function FeaturedReason({ reason, className }: FeaturedReasonProps) {
  if (!reason) return null

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl p-5',
        'bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50',
        'dark:from-amber-900/20 dark:via-orange-900/20 dark:to-yellow-900/20',
        'border border-amber-200/60 dark:border-amber-700/40',
        className
      )}
    >
      {/* 装饰性背景 */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-amber-200/30 to-transparent rounded-bl-full" />

      {/* 内容 */}
      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-sm">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-1">
            Featured Reason
          </h3>
          <p className="text-sm text-amber-900/80 dark:text-amber-100/80 leading-relaxed">
            {reason}
          </p>
        </div>
      </div>
    </div>
  )
}
