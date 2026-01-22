/**
 * [INPUT]: 依赖 lucide-react, @/lib/utils, ./utils, ./audio-player-context
 * [OUTPUT]: 对外提供 ChapterOverview 组件
 * [POS]: podcast/ 的章节概览组件，支持时间戳跳转
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Play, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatTime } from './utils'
import { useAudioPlayer } from './audio-player-context'

export interface Chapter {
  time: number // 时间戳（秒）
  title: string
  summary?: string
}

interface ChapterOverviewProps {
  chapters: Chapter[]
  currentTime?: number
  className?: string
}

export function ChapterOverview({
  chapters,
  currentTime: propCurrentTime,
  className,
}: ChapterOverviewProps) {
  const { seekTo, currentTime: contextTime } = useAudioPlayer()
  // 优先使用 Context 中的时间，回退到 props
  const currentTime = contextTime || propCurrentTime || 0

  if (!chapters || chapters.length === 0) {
    return (
      <div className={cn('text-center py-8 text-gray-500 dark:text-gray-400', className)}>
        暂无章节信息
      </div>
    )
  }

  // 确定当前播放的章节
  const getCurrentChapterIndex = () => {
    for (let i = chapters.length - 1; i >= 0; i--) {
      if (currentTime >= chapters[i].time) {
        return i
      }
    }
    return -1
  }

  const currentChapterIndex = getCurrentChapterIndex()

  return (
    <div className={cn('space-y-3', className)}>
      {chapters.map((chapter, index) => {
        const isActive = index === currentChapterIndex
        const isPast = index < currentChapterIndex

        return (
          <div
            key={index}
            className={cn(
              'group flex items-start gap-4 p-4 rounded-xl transition-all cursor-pointer',
              'hover:bg-gray-100 dark:hover:bg-gray-800',
              isActive && 'bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700',
              !isActive && 'border border-transparent'
            )}
            onClick={() => seekTo(chapter.time)}
          >
            {/* 时间戳 */}
            <div className="flex-shrink-0 flex items-center gap-2">
              <div
                className={cn(
                  'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-sm font-mono',
                  isActive
                    ? 'bg-indigo-500 text-white'
                    : isPast
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                )}
              >
                <Clock className="w-3.5 h-3.5" />
                {formatTime(chapter.time)}
              </div>
            </div>

            {/* 内容 */}
            <div className="flex-1 min-w-0">
              <h4
                className={cn(
                  'font-medium leading-snug',
                  isActive
                    ? 'text-indigo-900 dark:text-indigo-100'
                    : 'text-gray-900 dark:text-white'
                )}
              >
                {chapter.title}
              </h4>
              {chapter.summary && (
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                  {chapter.summary}
                </p>
              )}
            </div>

            {/* 跳转按钮 */}
            <button
              className={cn(
                'flex-shrink-0 p-2 rounded-full transition-all',
                'opacity-0 group-hover:opacity-100',
                'bg-indigo-500 text-white hover:bg-indigo-600',
                isActive && 'opacity-100'
              )}
              onClick={(e) => {
                e.stopPropagation()
                seekTo(chapter.time)
              }}
              title="跳转到此处"
            >
              <Play className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
