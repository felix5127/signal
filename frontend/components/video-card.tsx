/**
 * VideoCard - Mercury 风格视频卡片
 * 设计规范:
 * - 缩略图区域: 彩色背景 + 居中播放按钮 + 右下角时长标签
 * - 内容区域: 标签 + 标题 + 描述 + 来源
 * - 圆角: 16px (顶部圆角, 底部方角)
 * - 背景色: #FFFFFF, 边框: #E8E5E0
 */
'use client'

import { cn } from '@/lib/utils'
import { SOURCE_NAMES } from '@/lib/constants'
import { Play } from 'lucide-react'
import type { Resource } from '@/components/resource-list-page'

interface VideoCardProps {
  resource: Resource
  className?: string
}

// 视频缩略图背景色调色板
const THUMBNAIL_COLORS = [
  '#1E3A5F', // Navy
  '#3D6B4F', // Green
  '#8B4049', // Burgundy
  '#6366F1', // Indigo
  '#D97706', // Orange
  '#059669', // Teal
]

// 根据资源 ID 生成稳定的颜色
function getColorForId(id: number): string {
  return THUMBNAIL_COLORS[id % THUMBNAIL_COLORS.length]
}

// 格式化时长 (秒 -> 可读格式)
function formatDuration(seconds?: number): string {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 格式化相对时间
function formatRelativeTime(dateString?: string): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    })
  }
}

export function VideoCard({ resource, className }: VideoCardProps) {
  const displayTitle = resource.title_translated || resource.title
  const displaySummary =
    resource.one_sentence_summary_zh ||
    resource.one_sentence_summary ||
    resource.summary_zh ||
    resource.summary ||
    ''
  const sourceName = SOURCE_NAMES[resource.source_name || ''] || resource.source_name || 'YouTube'
  const domain = resource.domain || ''
  const thumbnailColor = getColorForId(resource.id)
  const displayTime = resource.published_at || resource.created_at

  return (
    <a
      href={`/resources/${resource.id}`}
      className={cn(
        "group block",
        "rounded-2xl overflow-hidden",
        "bg-white",
        "border border-[#E8E5E0]",
        "transition-all duration-200",
        "hover:shadow-lg hover:-translate-y-1",
        className
      )}
    >
      {/* 缩略图区域 */}
      <div
        className="relative aspect-[16/10] flex items-center justify-center overflow-hidden"
        style={{ backgroundColor: thumbnailColor }}
      >
        {/* 缩略图 */}
        {resource.thumbnail_url && (
          <img
            src={resource.thumbnail_url}
            alt={displayTitle}
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
          />
        )}

        {/* 播放按钮 */}
        <div className="relative z-10 w-14 h-14 rounded-full bg-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
          <Play
            className="w-6 h-6 ml-0.5"
            style={{ color: thumbnailColor }}
            fill={thumbnailColor}
          />
        </div>

        {/* 时长标签 */}
        {resource.duration && (
          <div className="absolute bottom-3 right-3 px-2 py-1 bg-black/50 rounded text-white text-xs font-medium z-10">
            {formatDuration(resource.duration)}
          </div>
        )}
      </div>

      {/* 内容区域 */}
      <div className="p-5 space-y-3">
        {/* 标签行 */}
        {domain && (
          <div className="flex items-center gap-2">
            <span
              className="px-2 py-1 rounded text-xs font-medium"
              style={{
                backgroundColor: `${thumbnailColor}15`,
                color: thumbnailColor
              }}
            >
              {domain}
            </span>
          </div>
        )}

        {/* 标题 */}
        <h3 className="text-[18px] font-medium text-[#272735] leading-[1.4] line-clamp-2 group-hover:text-[#1E3A5F] transition-colors">
          {displayTitle}
        </h3>

        {/* 描述 */}
        {displaySummary && (
          <p className="text-sm text-[#6B6B6B] leading-[1.5] line-clamp-2">
            {displaySummary}
          </p>
        )}

        {/* 元信息 */}
        <div className="flex items-center gap-4 text-[13px] text-[#9A9A9A]">
          {displayTime && (
            <span>{formatRelativeTime(displayTime)}</span>
          )}
          <span>{sourceName}</span>
        </div>
      </div>
    </a>
  )
}
