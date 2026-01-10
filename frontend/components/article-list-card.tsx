// Input: article 文章类型资源数据
// Output: Newsletter 风格的文章列表卡片（单栏布局，使用设计系统）
// Position: 首页文章列表，类似 Morning Brew / Newsletter 风格
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { cn } from '@/lib/utils'
import { Badge, ScoreBadge } from '@/lib/design-system/components/Badge'
import { ArrowUpRight } from 'lucide-react'

export interface ArticleResource {
  id: number
  source?: string
  source_name?: string
  source_icon_url?: string
  url: string
  title: string
  title_translated?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  summary_zh?: string
  content_markdown?: string
  score?: number
  final_score?: number
  is_featured?: boolean
  domain?: string
  subdomain?: string
  tags?: string[]
  published_at?: string
  created_at?: string
  word_count?: number
  read_time?: number
}

interface ArticleListCardProps {
  resource: ArticleResource
  className?: string
}

const SOURCE_NAMES: Record<string, string> = {
  hn: 'Hacker News',
  github: 'GitHub Trending',
  huggingface: 'Hugging Face',
  twitter: 'Twitter',
  arxiv: 'ArXiv',
  producthunt: 'Product Hunt',
  blog: 'Blog',
}

// 使用设计系统颜色
const DOMAIN_COLORS: Record<string, string> = {
  '软件编程': 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  '人工智能': 'bg-[#F3F2FF] text-[#6258FF] dark:bg-[#6258FF]/10 dark:text-[#CDCBFF] border-[#CDCBFF] dark:border-[#6258FF]',
  '产品设计': 'bg-pink-50 text-pink-700 dark:bg-pink-950/30 dark:text-pink-400 border-pink-200 dark:border-pink-800',
  '商业科技': 'bg-[#CDEED3]/30 text-[#1B9A7A] dark:bg-[#1B9A7A]/10 dark:text-[#CDEED3] border-[#CDEED3] dark:border-[#1B9A7A]',
}

const DOMAIN_TEXT_COLORS: Record<string, string> = {
  '软件编程': 'text-blue-600 dark:text-blue-400',
  '人工智能': 'text-[#6258FF] dark:text-[#CDCBFF]',
  '产品设计': 'text-pink-600 dark:text-pink-400',
  '商业科技': 'text-[#1B9A7A] dark:text-[#CDEED3]',
}

function getWeekDay(dateString?: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[date.getDay()]
}

function formatMonthDay(dateString?: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function formatRelativeTime(dateString?: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return formatMonthDay(dateString)
}

// 提取摘要内容的前三句
function getSummaryPreview(summary?: string): string {
  if (!summary) return ''

  // 按句号分割（中文句号.、英文句号.、问号?、感叹号!）
  const sentences = summary
    .replace(/([。！？\.!?])\s*/g, '$1|||')
    .split('|||')

  // 提取前三句
  const contentLines: string[] = []
  for (const sentence of sentences) {
    const trimmed = sentence.trim()
    if (trimmed && trimmed.length > 2) {
      contentLines.push(trimmed)
      if (contentLines.length >= 3) break
    }
  }

  return contentLines.join('')
}

export function ArticleListCard({ resource, className }: ArticleListCardProps) {
  const displayTitle = resource.title_translated || resource.title

  // 优先显示内容摘要前三行（summary_zh），其次显示一句话摘要
  const summaryText = resource.summary_zh || resource.summary || ''
  const displaySummary = getSummaryPreview(summaryText) ||
    resource.one_sentence_summary_zh ||
    resource.one_sentence_summary ||
    ''
  const sourceName = resource.source_name || SOURCE_NAMES[resource.source] || resource.source
  const domain = resource.domain
  const subdomain = resource.subdomain
  const score = resource.score ?? resource.final_score
  const displayTime = resource.published_at || resource.created_at

  return (
    <a
      href={`/resources/${resource.id}`}
      className={cn(
        'group relative flex gap-5 py-5',
        'border-b border-[var(--ds-border)]',
        'hover:bg-[var(--ds-surface-2)]',
        'transition-colors duration-200',
        '-mx-5 px-5',
        className
      )}
    >
      {/* 左侧：日期显示 */}
      <div className="flex-shrink-0 w-14 pt-0.5">
        <div className="text-right">
          <div className="text-2xl font-semibold text-[var(--ds-muted)] leading-none">
            {new Date(displayTime || '').getDate()}
          </div>
          <div className="text-xs text-[var(--ds-muted)] mt-0.5">
            {getWeekDay(displayTime)}
          </div>
        </div>
      </div>

      {/* 中间：主要内容 */}
      <div className="flex-1 min-w-0">
        {/* 标题 - 使用深色确保对比度 */}
        <h3
          className={cn(
            'font-semibold text-slate-900 text-base leading-snug mb-2',
            'group-hover:text-violet-600',
            'transition-colors flex items-start justify-between gap-3'
          )}
        >
          <span className="line-clamp-2">{displayTitle}</span>
          <ArrowUpRight className="w-4 h-4 text-[var(--ds-muted)] group-hover:text-[var(--ds-accent)] flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-all" />
        </h3>

        {/* 摘要 - 显示前三行 */}
        {displaySummary && (
          <p className="text-sm text-[var(--ds-muted)] line-clamp-3 leading-relaxed mb-3">
            {displaySummary}
          </p>
        )}

        {/* 元信息标签行 */}
        <div className="flex items-center flex-wrap gap-2">
          {/* 来源 */}
          <span className="text-sm font-medium text-slate-700">
            {sourceName}
          </span>

          {/* 分类标签 */}
          {domain && (
            <>
              <span className="text-[var(--ds-subtle)]">·</span>
              <Badge
                variant="soft"
                color="default"
                size="xs"
                className={cn(
                  DOMAIN_COLORS[domain] || 'bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                )}
              >
                {domain}
                {subdomain && ` / ${subdomain}`}
              </Badge>
            </>
          )}

          {/* 标签 */}
          {resource.tags && resource.tags.length > 0 && (
            <>
              <span className="text-gray-300 dark:text-gray-700">·</span>
              <div className="flex items-center gap-1.5">
                {resource.tags.slice(0, 3).map((tag, i) => (
                  <span
                    key={i}
                    className="text-xs text-[var(--ds-subtle)]"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </>
          )}

          {/* 字数和时间 */}
          <span className="text-[var(--ds-subtle)]">·</span>
          <span className="text-xs text-[var(--ds-subtle)]">
            {resource.word_count ? `${resource.word_count} 字` : ''}
            {resource.word_count && resource.read_time && ' · '}
            {resource.read_time ? `${resource.read_time} 分钟` : ''}
          </span>

          {/* 评分 */}
          {score !== undefined && score > 0 && (
            <>
              <span className="text-[var(--ds-subtle)]">·</span>
              <ScoreBadge score={score} maxScore={5} size="xs" />
            </>
          )}
        </div>
      </div>

      {/* 右侧：来源图标 */}
      <div className="flex-shrink-0">
        {resource.source_icon_url ? (
          <img
            src={resource.source_icon_url}
            alt={sourceName}
            className="w-10 h-10 rounded-2xl p-1.5 bg-[var(--ds-bg)] border border-[var(--ds-border)]"
            onError={(e) => {
              const target = e.target as HTMLImageElement
              target.style.display = 'none'
            }}
          />
        ) : (
          <div className="w-10 h-10 rounded-2xl bg-brand-gradient flex items-center justify-center shadow-brand-md">
            <span className="text-white text-sm font-medium">
              {(sourceName || 'S').charAt(0).toUpperCase()}
            </span>
          </div>
        )}
      </div>
    </a>
  )
}
