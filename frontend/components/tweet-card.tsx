/**
 * [INPUT]: 依赖 @/lib/utils 的 cn, lucide-react 图标组件
 * [OUTPUT]: 对外提供 TweetCard 组件, TweetResource 类型
 * [POS]: components/ 的推文卡片，被 /tweets 页面消费，Twitter 原生风格
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { cn } from '@/lib/utils'
import { MessageCircle, Repeat2, Heart, Bookmark, Share, Star } from 'lucide-react'

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
    .filter(line => line.length > 0 && line.length < 500) // 过滤掉过长的行（可能是图片链接等）
    .join('\n')
}

// X Logo SVG
const XIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
)

export function TweetCard({ resource, className }: TweetCardProps) {
  const displayTitle = resource.title_translated || resource.title

  // 从 HTML 中提取纯文本
  const displayContent =
    resource.summary && !resource.summary.includes('<div') ? resource.summary :
    resource.one_sentence_summary_zh && !resource.one_sentence_summary_zh.includes('<div') ? resource.one_sentence_summary_zh :
    resource.one_sentence_summary ? extractTextFromHtml(resource.one_sentence_summary) :
    displayTitle

  const { name, handle } = extractUserInfo(resource.url, resource.author)
  const timeAgo = formatTweetTime(resource.published_at || resource.created_at)

  // 使用 unavatar.io 获取 Twitter 头像
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
        'hover:bg-slate-50',
        'transition-colors duration-150 cursor-pointer',
        'border-b border-slate-100',
        '-mx-4',
        className
      )}
      onClick={(e) => {
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
              className="w-10 h-10 rounded-full ring-1 ring-slate-200"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const fallback = target.nextElementSibling as HTMLElement
                if (fallback) fallback.style.display = 'flex'
              }}
            />
          ) : null}
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center ring-1 ring-slate-200 ${shouldUseRealAvatar ? 'hidden' : ''}`}>
            <XIcon />
          </div>
        </div>

        {/* 内容区 */}
        <div className="flex-1 min-w-0">
          {/* 用户信息行 */}
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            <span className="font-bold text-slate-900 text-sm hover:underline">
              {name}
            </span>
            <span className="text-slate-500 text-sm">@{handle}</span>
            <span className="text-slate-400 text-sm">·</span>
            <span className="text-slate-400 text-sm hover:underline">
              {timeAgo}
            </span>

            {/* 标签 */}
            {resource.tags && resource.tags.length > 0 && (
              <>
                <span className="text-slate-400 text-sm">·</span>
                <div className="flex items-center gap-1">
                  {resource.tags.slice(0, 2).map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-1.5 py-0.5 bg-violet-50 text-violet-600 rounded-md"
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
                <span className="text-slate-400 text-sm">·</span>
                <span className="text-xs px-1.5 py-0.5 bg-amber-50 text-amber-600 rounded-md font-medium inline-flex items-center gap-1">
                  {resource.score.toFixed(1)}
                  <Star className="w-3 h-3 fill-current" />
                </span>
              </>
            )}

            <div className="ml-auto">
              <button
                className="text-slate-400 hover:text-slate-600 transition-colors"
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
              'text-slate-800 text-[15px] leading-relaxed',
              'whitespace-pre-wrap break-words mb-3'
            )}
          >
            {displayContent}
          </div>

          {/* 底部互动按钮 */}
          <div className="flex items-center justify-between max-w-md text-slate-400">
            <button
              className="flex items-center gap-2 group/btn hover:text-[#1DA1F2] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[#1DA1F2]/10 transition-colors">
                <MessageCircle className="w-4 h-4" />
              </div>
              <span className="text-xs">Reply</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[#00BA7C] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[#00BA7C]/10 transition-colors">
                <Repeat2 className="w-4 h-4" />
              </div>
              <span className="text-xs">Repost</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[#F91880] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[#F91880]/10 transition-colors">
                <Heart className="w-4 h-4" />
              </div>
              <span className="text-xs">Like</span>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[#1DA1F2] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[#1DA1F2]/10 transition-colors">
                <Bookmark className="w-4 h-4" />
              </div>
            </button>

            <button
              className="flex items-center gap-2 group/btn hover:text-[#1DA1F2] transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-1.5 rounded-full group-hover/btn:bg-[#1DA1F2]/10 transition-colors">
                <Share className="w-4 h-4" />
              </div>
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
