/**
 * [INPUT]: 依赖 @/lib/utils
 * [OUTPUT]: 对外提供 ContentTabs 组件
 * [POS]: podcast/ 的 Tab 切换组件，4 个 Tab 内容区
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, ReactNode } from 'react'
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
  { key: 'chapters', label: 'Content Overview', icon: <BookOpen className="w-4 h-4" /> },
  { key: 'transcript', label: 'Transcript', icon: <MessageSquare className="w-4 h-4" /> },
  { key: 'qa', label: 'Q&A Recap', icon: <HelpCircle className="w-4 h-4" /> },
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
    <div className={className}>
      {/* Tab 导航 */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl mb-6 overflow-x-auto">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key
          const isAvailable = tabAvailability[tab.key]

          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
                isActive
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : isAvailable
                  ? 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  : 'text-gray-400 dark:text-gray-500 cursor-not-allowed'
              )}
              disabled={!isAvailable}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {!isAvailable && (
                <span className="text-xs text-gray-400 dark:text-gray-500">(N/A)</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab 内容 */}
      <div className="min-h-[300px]">{children}</div>
    </div>
  )
}
