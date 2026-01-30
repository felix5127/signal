/**
 * TweetCard - Mercury 风格推文卡片
 * 特点: 简洁大气、清晰层级、专业感
 */
'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { MessageCircle, Repeat2, Heart, Bookmark, Share, Star, ChevronDown, ChevronUp } from 'lucide-react'

export interface TweetResource {
  id: number
  source_name?: string
  source_icon_url?: string
  url: string
  title: string
  title_translated?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  content_markdown?: string
  author?: string
  score?: number
  final_score?: number
  tags?: string[]
  published_at?: string
  created_at?: string
}

interface TweetCardProps {
  resource: TweetResource
  className?: string
}

function formatTweetTime(dateString?: string): string {
  if (!dateString) return 'now'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMinutes < 1) return 'now'
  if (diffMinutes < 60) return `${diffMinutes}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// 从 URL 或 author 字段提取用户信息
function extractUserInfo(url?: string, author?: string): { name: string; handle: string } {
  if (author) {
    const handleMatch = author.match(/@(\w+)/)
    if (handleMatch) {
      const nameMatch = author.match(/^(.+?)\s*@\w+/)
      return {
        name: nameMatch ? nameMatch[1].trim() : handleMatch[1],
        handle: handleMatch[1]
      }
    }
    return { name: author, handle: author.toLowerCase().replace(/\s+/g, '') }
  }

  if (url) {
    const match = url.match(/(?:twitter|x)\.com\/([^\/]+)/)
    if (match && match[1] !== 'i' && match[1] !== 'status') {
      const username = match[1]
      const displayName = username
        .split('_')
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ')
      return { name: displayName, handle: username }
    }
  }

  return { name: 'User', handle: 'user' }
}

// 从 HTML 中提取纯文本内容
function extractTextFromHtml(html: string): string {
  if (!html) return ''

  let text = html
    .replace(/<div[^>]*>/gi, '\n')
    .replace(/<\/div>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)))
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))

  return text
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0 && line.length < 500)
    .join('\n')
}

// X Logo SVG
const XIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
)

export function TweetCard({ resource, className }: TweetCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const displayTitle = resource.title_translated || resource.title

  const displayContent =
    resource.summary && !resource.summary.includes('<div') ? resource.summary :
    resource.one_sentence_summary_zh && !resource.one_sentence_summary_zh.includes('<div') ? resource.one_sentence_summary_zh :
    resource.one_sentence_summary ? extractTextFromHtml(resource.one_sentence_summary) :
    displayTitle

  const { name, handle } = extractUserInfo(resource.url, resource.author)
  const timeAgo = formatTweetTime(resource.published_at || resource.created_at)

  const getTwitterAvatarUrl = (username: string): string => {
    return `https://unavatar.io/twitter/${username}`
  }

  const shouldUseRealAvatar = handle && handle !== 'user'
  const avatarUrl = shouldUseRealAvatar ? getTwitterAvatarUrl(handle) : null
  const fullUrl = resource.url

  return (
    <article
      className={cn(
        'group p-4',
        'hover:bg-[#F8F9FA]',
        'transition-colors duration-200 cursor-pointer',
        'border-b border-[#E8E5E0] last:border-b-0',
        className
      )}
      onClick={() => {
        window.open(fullUrl, '_blank')
      }}
    >
      <div className="flex gap-3">
        {/* 头像 */}
        <div className="flex-shrink-0">
          {shouldUseRealAvatar && avatarUrl ? (
            <img
              src={avatarUrl}
              alt={name}
              className="w-10 h-10 rounded-full ring-1 ring-[var(--border-default)]"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const fallback = target.nextElementSibling as HTMLElement
                if (fallback) fallback.style.display = 'flex'
              }}
            />
          ) : null}
          <div className={`w-10 h-10 rounded-full bg-[var(--text-primary)] flex items-center justify-center text-white ring-1 ring-[var(--border-default)] ${shouldUseRealAvatar ? 'hidden' : ''}`}>
            <XIcon />
          </div>
        </div>

        {/* 内容区 */}
        <div className="flex-1 min-w-0">
          {/* 用户信息行 */}
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            <span className="font-semibold text-[var(--text-primary)] text-[var(--text-body-sm)] hover:underline">
              {name}
            </span>
            <span className="text-[var(--text-muted)] text-[var(--text-body-sm)]">@{handle}</span>
            <span className="text-[var(--text-muted)] text-[var(--text-body-sm)]">·</span>
            <span className="text-[var(--text-muted)] text-[var(--text-body-sm)] hover:underline">
              {timeAgo}
            </span>

            {/* 标签 */}
            {resource.tags && resource.tags.length > 0 && (
              <>
                <span className="text-[var(--text-muted)] text-[var(--text-body-sm)]">·</span>
                <div className="flex items-center gap-1">
                  {resource.tags.slice(0, 2).map((tag, i) => (
                    <span
                      key={i}
                      className="text-[var(--text-xs)] px-1.5 py-0.5 bg-[var(--color-primary-light)] text-[var(--color-primary)] rounded-md"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </>
            )}

            {/* 评分 */}
            {resource.score && resource.score > 0 && (
              <>
                <span className="text-[var(--text-muted)] text-[var(--text-body-sm)]">·</span>
                <span className="text-[var(--text-xs)] px-1.5 py-0.5 bg-[var(--color-accent-light)] text-[var(--color-accent)] rounded-md font-medium inline-flex items-center gap-1">
                  {resource.score.toFixed(1)}
                  <Star className="w-3 h-3 fill-current" />
                </span>
              </>
            )}

            <div className="ml-auto">
              <button
                className="text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="5" r="1.5" />
                  <circle cx="12" cy="12" r="1.5" />
                  <circle cx="12" cy="19" r="1.5" />
                </svg>
              </button>
            </div>
          </div>

          {/* 推文内容 */}
          <div
            className={cn(
              'text-[var(--text-primary)] text-[var(--text-body)] whitespace-pre-wrap break-words',
              !isExpanded && 'line-clamp-3'
            )}
            style={{ lineHeight: 'var(--leading-relaxed)' }}
          >
            {displayContent}
          </div>

          {/* 显示全文按钮 - 设计稿: 始终显示 */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
            className="flex items-center gap-1 py-1 mt-2 mb-2"
          >
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" style={{ color: '#1E3A5F' }} />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" style={{ color: '#1E3A5F' }} />
            )}
            <span
              className="text-[13px] font-medium"
              style={{ color: '#1E3A5F' }}
            >
              {isExpanded ? '收起' : '显示全文'}
            </span>
          </button>

          {/* 底部互动按钮 */}
          <div className="flex items-center justify-between max-w-md text-[var(--text-muted)]">
            <button
              className="flex items-center gap-2 group/btn hover:text-[var(--color-primary)] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[var(--color-primary-light)] transition-colors">
                <MessageCircle className="w-4 h-4" />
              </div>
              <span className="text-[var(--text-xs)]">Reply</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[var(--color-success)] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-green-50 transition-colors">
                <Repeat2 className="w-4 h-4" />
              </div>
              <span className="text-[var(--text-xs)]">Repost</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[var(--color-error)] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-red-50 transition-colors">
                <Heart className="w-4 h-4" />
              </div>
              <span className="text-[var(--text-xs)]">Like</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[var(--color-primary)] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[var(--color-primary-light)] transition-colors">
                <Bookmark className="w-4 h-4" />
              </div>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[var(--color-primary)] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[var(--color-primary-light)] transition-colors">
                <Share className="w-4 h-4" />
              </div>
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
