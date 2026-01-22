/**
 * [INPUT]: 依赖 @/lib/utils, lucide-react, detail/ 子组件, 本地组件 (ScoreBadge/MainPoints/KeyQuotes/TagList)
 * [OUTPUT]: 对外提供 ResourceDetail 组件
 * [POS]: components/ 的资源详情组件，被 /resources/[id] 页面消费，展示 AI 分析结果
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScoreBadge } from './score-badge'
import { TagList } from './tag-list'
import { FlickeringGrid } from './effects/flickering-grid'
import DeepResearchButton from './deep-research-button'
import { FeaturedReason, AuthorInfo, AISidebar, ContentArea } from './detail'

export interface ResourceDetailProps {
  resource: {
    id: number
    type: string
    source_name: string
    source_icon_url?: string
    url: string
    title: string
    title_translated?: string
    author?: string
    one_sentence_summary?: string
    one_sentence_summary_zh?: string
    summary?: string
    summary_zh?: string
    content_markdown?: string
    domain?: string
    subdomain?: string
    tags?: string[]
    score?: number
    is_featured?: boolean
    featured_reason?: string
    featured_reason_zh?: string
    language?: string
    word_count?: number
    read_time?: number
    published_at?: string
    created_at?: string
    analyzed_at?: string
    main_points?: Array<{ point: string; explanation: string }>
    main_points_zh?: Array<{ point: string; explanation: string }>
    key_quotes?: string[]
    key_quotes_zh?: string[]
  }
}

// 类型名称映射
const TYPE_NAMES: Record<string, string> = {
  article: '文章',
  podcast: '播客',
  tweet: '推文',
  video: '视频',
}

// 格式化日期
function formatDate(dateString?: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// 验证图片 URL 安全性，防止 javascript: 等危险协议
function isSafeImageUrl(url?: string): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    return ['http:', 'https:', 'data:'].includes(parsed.protocol)
  } catch {
    return url.startsWith('/') || url.startsWith('./')
  }
}

export default function ResourceDetail({ resource }: ResourceDetailProps) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsLoading(false)
  }, [resource])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    )
  }

  // 获取显示的内容（中文优先）
  const displayTitle = resource.title_translated || resource.title
  const displayOneSentence = resource.one_sentence_summary_zh || resource.one_sentence_summary
  const displaySummary = resource.summary_zh || resource.summary
  const displayMainPoints = resource.main_points_zh || resource.main_points
  const displayKeyQuotes = resource.key_quotes_zh || resource.key_quotes
  const displayFeaturedReason = resource.featured_reason_zh || resource.featured_reason
  const typeName = TYPE_NAMES[resource.type] || resource.type

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 relative">
      {/* Flickering Grid 背景 */}
      <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
        <FlickeringGrid
          squareSize={2}
          gridGap={20}
          color="#6B21A8"
          maxOpacity={0.12}
          flickerChance={0.08}
        />
      </div>

      {/* 头部导航 */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>返回</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <span>{typeName}</span>
            {resource.domain && (
              <>
                <span>·</span>
                <span>{resource.domain}</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 主要内容 - 响应式布局 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* ====== 桌面端：左右布局 ====== */}
        <div className="hidden lg:flex gap-8">
          {/* 左侧主内容区 */}
          <div className="flex-1 max-w-3xl">
            {/* 标题区域 */}
            <div className="mb-6">
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white leading-tight mb-4">
                {displayTitle}
              </h1>

              {/* 标签 */}
              {resource.tags && resource.tags.length > 0 && (
                <TagList tags={resource.tags} />
              )}
            </div>

            {/* Featured Reason */}
            {displayFeaturedReason && (
              <FeaturedReason reason={displayFeaturedReason} className="mb-6" />
            )}

            {/* 主内容区 */}
            <ContentArea
              oneSentenceSummary={displayOneSentence}
              contentMarkdown={resource.content_markdown}
              showFullAnalysis={false}
            />

            {/* 操作按钮 */}
            <section className="mt-8 flex items-center gap-4 flex-wrap">
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 text-white rounded-xl font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
                style={{
                  background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
                  boxShadow: '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)'
                }}
              >
                <span>阅读原文</span>
                <ExternalLink className="w-4 h-4" />
              </a>
              <DeepResearchButton
                resourceId={resource.id}
                resourceTitle={displayTitle}
                resourceContent={resource.content_markdown || displaySummary}
                resourceUrl={resource.url}
              />
            </section>

            {/* 元数据信息 */}
            <footer className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-800">
              <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                <p>ID: {resource.id}</p>
                {resource.analyzed_at && (
                  <p>分析时间: {formatDate(resource.analyzed_at)}</p>
                )}
                {resource.created_at && (
                  <p>创建时间: {formatDate(resource.created_at)}</p>
                )}
              </div>
            </footer>
          </div>

          {/* 右侧 AI 分析侧边栏 (sticky) */}
          <aside className="w-80 flex-shrink-0">
            <div className="sticky top-20 space-y-5">
              {/* 作者信息 */}
              <AuthorInfo
                author={resource.author}
                sourceName={resource.source_name}
                sourceIconUrl={resource.source_icon_url}
                publishedAt={resource.published_at}
                readTime={resource.read_time}
                wordCount={resource.word_count}
              />

              {/* AI 分析 */}
              <AISidebar
                score={resource.score}
                isFeatured={resource.is_featured}
                summary={displaySummary}
                mainPoints={displayMainPoints}
                keyQuotes={displayKeyQuotes}
              />
            </div>
          </aside>
        </div>

        {/* ====== 移动端/平板：上下布局 ====== */}
        <div className="lg:hidden">
          {/* 标题区域 */}
          <div className="mb-6">
            {/* 来源信息 */}
            <div className="flex items-center gap-3 mb-4">
              {isSafeImageUrl(resource.source_icon_url) ? (
                <img
                  src={resource.source_icon_url}
                  alt={resource.source_name}
                  className="w-6 h-6 rounded"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.style.display = 'none'
                  }}
                />
              ) : (
                <div className="w-6 h-6 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-600 dark:text-gray-400">
                  {resource.source_name.charAt(0).toUpperCase()}
                </div>
              )}
              <span className="text-sm text-gray-600 dark:text-gray-400">{resource.source_name}</span>
              {resource.published_at && (
                <>
                  <span className="text-gray-400">·</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(resource.published_at)}
                  </span>
                </>
              )}
            </div>

            <div className="flex items-start justify-between gap-4 mb-4">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
                {displayTitle}
              </h1>
              {resource.score !== undefined && resource.score > 0 && (
                <ScoreBadge score={resource.score} />
              )}
            </div>

            {/* 标签 */}
            {resource.tags && resource.tags.length > 0 && (
              <TagList tags={resource.tags} />
            )}
          </div>

          {/* Featured Reason */}
          {displayFeaturedReason && (
            <FeaturedReason reason={displayFeaturedReason} className="mb-6" />
          )}

          {/* 主内容区 - 包含完整 AI 分析 */}
          <ContentArea
            oneSentenceSummary={displayOneSentence}
            summary={displaySummary}
            contentMarkdown={resource.content_markdown}
            mainPoints={displayMainPoints}
            keyQuotes={displayKeyQuotes}
            showFullAnalysis={true}
          />

          {/* 操作按钮 */}
          <section className="mt-8 flex items-center gap-4 flex-wrap">
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 text-white rounded-xl font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
                boxShadow: '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)'
              }}
            >
              <span>阅读原文</span>
              <ExternalLink className="w-4 h-4" />
            </a>
            <DeepResearchButton
              resourceId={resource.id}
              resourceTitle={displayTitle}
              resourceContent={resource.content_markdown || displaySummary}
              resourceUrl={resource.url}
            />
          </section>

          {/* 元数据信息 */}
          <footer className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-800">
            <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
              <p>ID: {resource.id}</p>
              {resource.analyzed_at && (
                <p>分析时间: {formatDate(resource.analyzed_at)}</p>
              )}
              {resource.created_at && (
                <p>创建时间: {formatDate(resource.created_at)}</p>
              )}
            </div>
          </footer>
        </div>
      </main>
    </div>
  )
}
