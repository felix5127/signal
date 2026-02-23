/**
 * ResourceCard - Mercury 风格资源卡片
 * 特点: 简洁、大圆角、清晰的信息层级
 */
'use client'

import { cn } from '@/lib/utils'
import { SOURCE_NAMES } from '@/lib/constants'
import { Badge } from '@/components/ui/badge'

export interface Resource {
  id: number
  type?: string
  source?: string
  title: string
  title_translated?: string
  url: string
  one_liner?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  final_score?: number
  score?: number
  is_featured?: boolean
  category?: string
  domain?: string
  tags?: string[]
  source_metadata?: Record<string, unknown>
  created_at?: string
  published_at?: string
  source_name?: string
  source_icon_url?: string
  word_count?: number
  read_time?: number
  duration?: number  // For podcasts/videos (seconds)
  language?: string
}

interface ResourceCardProps {
  resource: Resource
  className?: string
}

// 格式化时间
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

// 评分颜色
function getScoreColor(score: number): string {
  if (score >= 4) return 'bg-[var(--color-primary)] text-white'
  if (score >= 3) return 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
  return 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'
}

// 格式化时长 (秒 -> 可读格式)
function formatDuration(seconds?: number): string {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}小时${minutes > 0 ? ` ${minutes}分钟` : ''}`
  }
  return `${minutes}分钟`
}

export function ResourceCard({ resource, className }: ResourceCardProps) {
  const displayTitle = resource.title_translated || resource.title
  const displaySummary =
    resource.one_sentence_summary_zh ||
    resource.one_sentence_summary ||
    resource.one_liner ||
    ''
  const sourceName = resource.source_name ||
    (resource.source ? SOURCE_NAMES[resource.source] : undefined) ||
    resource.source || 'Unknown'
  const domain = resource.domain || resource.category || ''
  const score = resource.score ?? resource.final_score
  const displayTime = resource.published_at || resource.created_at

  return (
    <a
      href={`/resources/${resource.id}`}
      className={cn(
        "group block p-5",
        "rounded-[var(--radius-xl)]",
        "bg-[var(--bg-card)]",
        "border border-[var(--border-default)]",
        "transition-all duration-200",
        "hover:shadow-[var(--shadow-card-hover)]",
        "hover:-translate-y-0.5",
        "hover:border-[var(--border-strong)]",
        className
      )}
    >
      {/* 标题 */}
      <h3 className="h4 text-[var(--text-primary)] line-clamp-2 mb-2 group-hover:text-[var(--color-primary)] transition-colors">
        {displayTitle}
      </h3>

      {/* 摘要 */}
      {displaySummary && (
        <p className="text-[var(--text-body-sm)] text-[var(--text-secondary)] line-clamp-2 mb-4" style={{ lineHeight: 'var(--leading-relaxed)' }}>
          {displaySummary}
        </p>
      )}

      {/* 元信息 */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          {/* 评分 */}
          {score !== undefined && (
            <span className={cn(
              "inline-flex items-center px-2 py-0.5 rounded-full text-[var(--text-xs)] font-medium",
              getScoreColor(score)
            )}>
              {score.toFixed(1)}
            </span>
          )}

          {/* 来源 */}
          <Badge variant="secondary-soft" className="text-[var(--text-xs)]">
            {sourceName}
          </Badge>

          {/* 分类 */}
          {domain && (
            <Badge variant="outline" className="text-[var(--text-xs)]">
              {domain}
            </Badge>
          )}
        </div>

        {/* 时间 */}
        {displayTime && (
          <span className="text-[var(--text-xs)] text-[var(--text-muted)]">
            {formatRelativeTime(displayTime)}
          </span>
        )}
      </div>

      {/* 阅读/收听时间 */}
      {(resource.word_count || resource.read_time || resource.duration) && (
        <div className="flex items-center gap-3 mt-3 pt-3 border-t border-[var(--border-light)] text-[var(--text-xs)] text-[var(--text-muted)]">
          {resource.duration ? (
            <span>时长 {formatDuration(resource.duration)}</span>
          ) : (
            <>
              {resource.word_count && (
                <span>{resource.word_count.toLocaleString()} 字</span>
              )}
              {resource.read_time && (
                <span>约 {resource.read_time} 分钟</span>
              )}
            </>
          )}
        </div>
      )}
    </a>
  )
}
