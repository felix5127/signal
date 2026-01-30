/**
 * [INPUT]: 依赖 @/lib/utils
 * [OUTPUT]: 对外提供 ContentTabs 组件
 * [POS]: podcast/ 的 Tab 切换组件，匹配 Pencil 设计稿
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { ReactNode } from 'react'
import { FileText, BookOpen, MessageSquare, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type TabKey = 'show-notes' | 'chapters' | 'transcript' | 'qa'

interface Tab {
  key: TabKey
  label: string
  icon: ReactNode
}

const TABS: Tab[] = [
  { key: 'show-notes', label: 'Show Notes', icon: <FileText className="w-4 h-4" /> },
  { key: 'chapters', label: '章节概览', icon: <BookOpen className="w-4 h-4" /> },
  { key: 'transcript', label: 'Transcript', icon: <MessageSquare className="w-4 h-4" /> },
  { key: 'qa', label: 'Q&A 回顾', icon: <HelpCircle className="w-4 h-4" /> },
]

interface ContentTabsProps {
  activeTab: TabKey
  onTabChange: (tab: TabKey) => void
  children: ReactNode
  className?: string
  // 各 Tab 内容是否可用
  hasShowNotes?: boolean
  hasChapters?: boolean
  hasTranscript?: boolean
  hasQA?: boolean
}

export function ContentTabs({
  activeTab,
  onTabChange,
  children,
  className,
  hasShowNotes = true,
  hasChapters = false,
  hasTranscript = false,
  hasQA = false,
}: ContentTabsProps) {
  // 判断 Tab 是否有内容
  const tabAvailability: Record<TabKey, boolean> = {
    'show-notes': hasShowNotes,
    'chapters': hasChapters,
    'transcript': hasTranscript,
    'qa': hasQA,
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Tab 导航 - 匹配设计: 圆角容器 + pill 样式 */}
      <div className="flex items-center gap-1 p-1 bg-[#F5F3F0] rounded-xl overflow-x-auto">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key
          const isAvailable = tabAvailability[tab.key]

          return (
            <button
              key={tab.key}
              onClick={() => isAvailable && onTabChange(tab.key)}
              className={cn(
                'flex items-center gap-2 px-5 py-2.5 rounded-lg text-[14px] font-medium whitespace-nowrap transition-all',
                isActive
                  ? 'bg-white text-[#272735] shadow-sm'
                  : isAvailable
                  ? 'text-[#6B6B6B] hover:text-[#272735]'
                  : 'text-[#9A9A9A] cursor-not-allowed'
              )}
              disabled={!isAvailable}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Tab 内容卡片 - 匹配设计: 白色卡片 + 边框 */}
      <div className="rounded-2xl bg-white border border-[#E8E5E0] p-6">
        {children}
      </div>
    </div>
  )
}
