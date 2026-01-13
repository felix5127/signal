/**
 * [INPUT]: 依赖 @/lib/utils 的 cn, @/lib/design-system 的 Badge/ScoreBadge
 * [OUTPUT]: 对外提供 ResourceCard 组件, Resource 类型
 * [POS]: components/ 的通用资源卡片，被 /podcasts, /videos 页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { cn } from '@/lib/utils'
import { Badge, ScoreBadge as DesignScoreBadge } from '@/lib/design-system/components/Badge'

export interface Resource {
  id: number
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
  language?: string
}

interface ResourceCardProps {
  resource: Resource
  className?: string
}

// 来源名称映射
const SOURCE_NAMES: Record<string, string> = {
  hn: 'Hacker News',
  github: 'GitHub',
  huggingface: 'Hugging Face',
  twitter: 'Twitter',
  arxiv: 'ArXiv',
  producthunt: 'Product Hunt',
  blog: 'Blog',
}

// 来源颜色（Web 风格）
const SOURCE_COLORS: Record<string, string> = {
  hn: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400 border-orange-200 dark:border-orange-800',
  github: 'bg-gray-50 text-gray-700 dark:bg-gray-800/50 dark:text-gray-300 border-gray-200 dark:border-gray-700',
  huggingface: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800',
  twitter: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  arxiv: 'bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 border-red-200 dark:border-red-800',
  producthunt: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400 border-orange-200 dark:border-orange-800',
  blog: 'bg-[var(--ds-accent-2)]/20 text-[var(--ds-accent)] dark:bg-[var(--ds-accent)]/10 dark:text-[var(--ds-accent-2)] border-[var(--ds-accent-2)] dark:border-[var(--ds-accent)]',
}

// 分类颜色（Web 风格）
const DOMAIN_COLORS: Record<string, string> = {
  '软件编程': 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  '人工智能': 'bg-[var(--ds-accent-2)]/20 text-[var(--ds-accent)] dark:bg-[var(--ds-accent)]/10 dark:text-[var(--ds-accent-2)] border-[var(--ds-accent-2)] dark:border-[var(--ds-accent)]',
  '产品设计': 'bg-pink-50 text-pink-700 dark:bg-pink-950/30 dark:text-pink-400 border-pink-200 dark:border-pink-800',
  '商业科技': 'bg-[var(--ds-accent-2)]/20 text-[var(--ds-accent)] dark:bg-[var(--ds-accent)]/10 dark:text-[var(--ds-accent-2)] border-[var(--ds-accent-2)] dark:border-[var(--ds-accent)]',
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

export function ResourceCard({ resource, className }: ResourceCardProps) {
  // 获取显示的标题
  const displayTitle = resource.title_translated || resource.title

  // 获取一句话总结
  const displaySummary =
    resource.one_sentence_summary_zh ||
    resource.one_sentence_summary ||
    resource.one_liner ||
    ''

  // 获取来源名称
  const sourceName = resource.source_name || (resource.source ? SOURCE_NAMES[resource.source] : undefined) || resource.source || 'Unknown'

  // 获取分类
  const domain = resource.domain || resource.category || ''

  // 获取评分
  const score = resource.score ?? resource.final_score

  // 获取时间
  const displayTime = resource.published_at || resource.created_at

  return (
    <a
      href={`/resources/${resource.id}`}
      className={cn(
        'group block p-5 rounded-2xl border transition-all duration-200',
        'bg-[var(--ds-surface)]',
        'border-[var(--ds-border)]',
        'hover:border-[var(--ds-accent)]',
        'hover:shadow-card-hover',
        'hover:-translate-y-0.5',
        className
      )}
    >
      {/* 标题 */}
      <h3
        className={cn(
          'font-semibold text-[var(--ds-fg)]',
          'line-clamp-2 leading-snug mb-2',
          'group-hover:text-[var(--ds-accent)]',
          'transition-colors'
        )}
      >
        {displayTitle}
      </h3>

      {/* 一句话总结 */}
      {displaySummary && (
        <p className="text-sm text-[var(--ds-muted)] line-clamp-2 mb-3 leading-relaxed">
          {displaySummary}
        </p>
      )}

      {/* 底部元信息 */}
      <div className="space-y-2">
        {/* 第一行：评分 + 来源 + 分类 */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            {/* 评分徽章 */}
            {score !== undefined && (
              <DesignScoreBadge
                score={score}
                maxScore={5}
                size="xs"
              />
            )}

            {/* 来源标签 + 图标 */}
            <div className="flex items-center gap-1">
              {resource.source_icon_url && (
                <img
                  src={resource.source_icon_url}
                  className="w-4 h-4 rounded-sm"
                  alt=""
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.style.display = 'none'
                  }}
                />
              )}
              <Badge
                variant="soft"
                color="default"
                size="xs"
                className={cn(
                  (resource.source ? SOURCE_COLORS[resource.source] : '') || 'bg-[var(--ds-surface-2)] text-[var(--ds-muted)]'
                )}
              >
                {sourceName}
              </Badge>
            </div>

            {/* 分类标签 */}
            {domain && (
              <Badge
                variant="soft"
                color="default"
                size="xs"
                className={cn(
                  DOMAIN_COLORS[domain] || 'bg-[var(--ds-surface-2)] text-[var(--ds-muted)]'
                )}
              >
                {domain}
              </Badge>
            )}
          </div>

          {/* 时间 */}
          {displayTime && (
            <span className="text-xs text-[var(--ds-subtle)]">
              {formatRelativeTime(displayTime)}
            </span>
          )}
        </div>

        {/* 第二行：字数和阅读时间 */}
        {(resource.word_count || resource.read_time) && (
          <div className="flex items-center gap-3 text-xs text-[var(--ds-subtle)]">
            {resource.word_count && (
              <span>{resource.word_count.toLocaleString()} 字</span>
            )}
            {resource.read_time && (
              <>
                <span className="w-px h-3 bg-[var(--ds-border)]" />
                <span>约 {resource.read_time} 分钟</span>
              </>
            )}
          </div>
        )}
      </div>
    </a>
  )
}
