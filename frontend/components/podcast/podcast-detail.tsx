/**
 * [INPUT]: 依赖 detail/ 组件, podcast/ 子组件, @/lib/utils, @/lib/constants
 * [OUTPUT]: 对外提供 PodcastDetail 组件
 * [POS]: podcast/ 的播客详情页主组件，4 Tab 结构
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { ArrowLeft, ExternalLink, Podcast, Clock, Star, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FlickeringGrid } from '../effects/flickering-grid'
import { FeaturedReason } from '../detail/featured-reason'
import { ScoreBadge } from '../score-badge'
import { TagList } from '../tag-list'
import DeepResearchButton from '../deep-research-button'
import { AudioPlayer } from './audio-player'
import { AudioPlayerProvider } from './audio-player-context'
import { ContentTabs, TabKey } from './content-tabs'
import { ChapterOverview, Chapter } from './chapter-overview'
import { TranscriptView } from './transcript-view'
import { QARecap, QAPair } from './qa-recap'
import { formatTime } from './utils'

export interface PodcastResource {
  id: number
  type: 'podcast'
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
  content_markdown?: string // Show Notes
  domain?: string
  subdomain?: string
  tags?: string[]
  score?: number
  is_featured?: boolean
  featured_reason?: string
  featured_reason_zh?: string
  language?: string
  duration?: number // 时长（秒）
  audio_url?: string
  transcript?: string
  chapters?: Chapter[] // 章节列表
  qa_pairs?: QAPair[] // Q&A 对
  published_at?: string
  created_at?: string
  analyzed_at?: string
}

interface PodcastDetailProps {
  resource: PodcastResource
}

// 来源名称映射
const SOURCE_NAMES: Record<string, string> = {
  hn: 'Hacker News',
  github: 'GitHub',
  huggingface: 'Hugging Face',
  twitter: 'Twitter / X',
  arxiv: 'ArXiv',
  producthunt: 'Product Hunt',
  blog: '博客',
}

// 格式化时长（使用共享的 formatTime）
function formatDuration(seconds?: number): string {
  if (!seconds) return ''
  return formatTime(seconds)
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

export function PodcastDetail({ resource }: PodcastDetailProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('show-notes')
  const [currentTime, setCurrentTime] = useState(0)

  // 获取显示的内容（中文优先）
  const displayTitle = resource.title_translated || resource.title
  const displayOneSentence = resource.one_sentence_summary_zh || resource.one_sentence_summary
  const displayFeaturedReason = resource.featured_reason_zh || resource.featured_reason
  const sourceName = SOURCE_NAMES[resource.source_name] || resource.source_name

  // 处理时间更新
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time)
  }, [])

  // 渲染 Tab 内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'show-notes':
        return resource.content_markdown ? (
          <div className="prose prose-gray dark:prose-invert max-w-none">
            <div className="whitespace-pre-line text-gray-700 dark:text-gray-300 leading-relaxed">
              {resource.content_markdown}
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            暂无 Show Notes
          </div>
        )

      case 'chapters':
        return (
          <ChapterOverview
            chapters={resource.chapters || []}
            currentTime={currentTime}
          />
        )

      case 'transcript':
        return <TranscriptView transcript={resource.transcript} />

      case 'qa':
        return <QARecap qaPairs={resource.qa_pairs || []} />

      default:
        return null
    }
  }

  return (
    <AudioPlayerProvider>
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
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>返回</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Podcast className="w-4 h-4" />
            <span>播客</span>
            {resource.domain && (
              <>
                <span>·</span>
                <span>{resource.domain}</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Featured Reason */}
        {displayFeaturedReason && (
          <FeaturedReason reason={displayFeaturedReason} className="mb-6" />
        )}

        {/* 一句话总结 */}
        {displayOneSentence && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-5 mb-6 border border-blue-100 dark:border-blue-800">
            <p className="text-gray-900 dark:text-white leading-relaxed text-lg">
              {displayOneSentence}
            </p>
          </div>
        )}

        {/* 播客信息卡片 */}
        <div className="flex flex-wrap items-center gap-6 mb-6 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
          {/* 来源 */}
          <div className="flex items-center gap-2">
            {isSafeImageUrl(resource.source_icon_url) ? (
              <img
                src={resource.source_icon_url}
                alt={sourceName}
                className="w-5 h-5 rounded"
              />
            ) : (
              <Podcast className="w-5 h-5 text-gray-400" />
            )}
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {sourceName}
            </span>
          </div>

          {/* 发布日期 */}
          {resource.published_at && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(resource.published_at)}</span>
            </div>
          )}

          {/* 时长 */}
          {resource.duration && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Clock className="w-4 h-4" />
              <span>{formatDuration(resource.duration)}</span>
            </div>
          )}

          {/* 评分 */}
          {resource.score !== undefined && resource.score > 0 && (
            <ScoreBadge score={resource.score} isFeatured={resource.is_featured} />
          )}
        </div>

        {/* 标题 */}
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white leading-tight mb-4">
          {displayTitle}
        </h1>

        {/* 标签 */}
        {resource.tags && resource.tags.length > 0 && (
          <div className="mb-6">
            <TagList tags={resource.tags} />
          </div>
        )}

        {/* 音频播放器 */}
        {resource.audio_url && (
          <AudioPlayer
            audioUrl={resource.audio_url}
            duration={resource.duration}
            onTimeUpdate={handleTimeUpdate}
            className="mb-8"
          />
        )}

        {/* 4 Tab 内容区 */}
        <ContentTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          hasShowNotes={!!resource.content_markdown}
          hasChapters={!!(resource.chapters && resource.chapters.length > 0)}
          hasTranscript={!!resource.transcript}
          hasQA={!!(resource.qa_pairs && resource.qa_pairs.length > 0)}
        >
          {renderTabContent()}
        </ContentTabs>

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
            <span>访问原链接</span>
            <ExternalLink className="w-4 h-4" />
          </a>
          <DeepResearchButton
            resourceId={resource.id}
            resourceTitle={displayTitle}
            resourceContent={resource.transcript || resource.content_markdown}
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
      </main>
    </div>
    </AudioPlayerProvider>
  )
}
