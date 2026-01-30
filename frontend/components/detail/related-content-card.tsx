/**
 * [INPUT]: 依赖 lucide-react 图标, Next.js Link
 * [OUTPUT]: 对外提供 RelatedContentCard 组件
 * [POS]: detail/ 的相关内容卡片，展示相关文章列表
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import Link from 'next/link'
import { FileText, ChevronRight } from 'lucide-react'

interface RelatedItem {
  id: number
  title: string
  source_name?: string
  type?: string
}

interface RelatedContentCardProps {
  items?: RelatedItem[]
  className?: string
}

export function RelatedContentCard({
  items = [],
  className,
}: RelatedContentCardProps) {
  // 如果没有相关内容，显示占位
  const displayItems = items.length > 0 ? items.slice(0, 4) : []

  return (
    <div
      className={`rounded-2xl p-5 w-full bg-white border border-[rgba(0,0,0,0.06)] ${className || ''}`}
    >
      {/* 标题行 */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
          <FileText className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-[15px] font-semibold text-[#272735]">
          相关内容
        </h3>
      </div>

      {/* 文章列表 */}
      {displayItems.length > 0 ? (
        <div className="space-y-3">
          {displayItems.map((item) => (
            <Link
              key={item.id}
              href={`/resources/${item.id}`}
              className="block p-3 rounded-xl bg-[#FBFCFD] border border-[rgba(0,0,0,0.04)] hover:bg-[#F6F5F2] hover:border-[rgba(0,0,0,0.08)] transition-all duration-200 group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-[13px] font-medium text-[#272735] line-clamp-2 leading-[1.5] group-hover:text-[#1E3A5F] transition-colors">
                    {item.title}
                  </h4>
                  {item.source_name && (
                    <p className="text-[12px] text-[#9A9A9A] mt-1">
                      {item.source_name}
                    </p>
                  )}
                </div>
                <ChevronRight className="w-4 h-4 flex-shrink-0 text-[#9A9A9A] group-hover:text-[#1E3A5F] transition-colors mt-0.5" />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <p className="text-[13px] text-[#9A9A9A] text-center py-4">
          暂无相关内容
        </p>
      )}
    </div>
  )
}
