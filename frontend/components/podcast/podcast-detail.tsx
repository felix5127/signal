/**
 * [INPUT]: 依赖 detail/ 组件, podcast/ 子组件, @/lib/utils, @/lib/constants
 * [OUTPUT]: 对外提供 PodcastDetail 组件
 * [POS]: podcast/ 的播客详情页主组件，匹配 Pencil 设计稿
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
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

// 格式化时长
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

export function PodcastDetail({ resource }: PodcastDetailProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('show-notes')
  const [currentTime, setCurrentTime] = useState(0)

  // 获取显示的内容（中文优先）
  const displayTitle = resource.title_translated || resource.title
  const displaySummary = resource.summary_zh || resource.summary || resource.one_sentence_summary_zh || resource.one_sentence_summary
  const sourceName = SOURCE_NAMES[resource.source_name] || resource.source_name

  // 处理时间更新
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time)
  }, [])

  // 渲染 Tab 内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'show-notes':
        return (
          <div className="space-y-4">
            <h3 className="text-[18px] font-semibold text-[#272735]">节目简介</h3>
            {resource.content_markdown ? (
              <div className="text-[15px] text-[#6B6B6B] leading-[1.7] whitespace-pre-line">
                {resource.content_markdown}
              </div>
            ) : displaySummary ? (
              <div className="text-[15px] text-[#6B6B6B] leading-[1.7] whitespace-pre-line">
                {displaySummary}
              </div>
            ) : (
              <div className="text-center py-8 text-[#9A9A9A]">
                暂无节目简介
              </div>
            )}
          </div>
        )

      case 'chapters':
        return (
          <div className="space-y-4">
            <h3 className="text-[18px] font-semibold text-[#272735]">章节概览</h3>
            <ChapterOverview
              chapters={resource.chapters || []}
              currentTime={currentTime}
            />
          </div>
        )

      case 'transcript':
        return (
          <div className="space-y-4">
            <h3 className="text-[18px] font-semibold text-[#272735]">完整文字稿</h3>
            <TranscriptView transcript={resource.transcript} />
          </div>
        )

      case 'qa':
        return (
          <div className="space-y-4">
            <h3 className="text-[18px] font-semibold text-[#272735]">问答回顾</h3>
            <QARecap qaPairs={resource.qa_pairs || []} />
          </div>
        )

      default:
        return null
    }
  }

  return (
    <AudioPlayerProvider>
      <div className="min-h-screen bg-[#FBFCFD]">
        {/* 主要内容 */}
        <main className="max-w-[1280px] mx-auto px-20 py-10">
          {/* ====== Breadcrumb 面包屑 ====== */}
          <nav className="flex items-center gap-2 text-[13px] mb-8">
            <Link
              href="/"
              className="text-[#9A9A9A] hover:text-[#1E3A5F] transition-colors duration-200"
            >
              首页
            </Link>
            <span className="text-[#9A9A9A]">/</span>
            <Link
              href="/podcasts"
              className="text-[#9A9A9A] hover:text-[#1E3A5F] transition-colors duration-200"
            >
              播客
            </Link>
            <span className="text-[#9A9A9A]">/</span>
            <span className="text-[#272735] font-medium">当前播客</span>
          </nav>

          {/* ====== Header 区域 ====== */}
          <header className="mb-8 space-y-4">
            {/* 标签行 - 匹配设计: 多个彩色标签 */}
            <div className="flex flex-wrap items-center gap-2">
              {resource.domain && (
                <span className="inline-flex items-center px-3 py-1.5 rounded-md text-[13px] font-medium bg-[#EEF2FF] text-[#4F46E5]">
                  {resource.domain}
                </span>
              )}
              {resource.tags && resource.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className={cn(
                    "inline-flex items-center px-3 py-1.5 rounded-md text-[13px] font-medium",
                    index === 0 ? "bg-[#FEF3C7] text-[#B45309]" : "bg-[#F5F3F0] text-[#6B6B6B]"
                  )}
                >
                  {tag}
                </span>
              ))}
            </div>

            {/* 大标题 - 匹配设计: 32px, 500 weight */}
            <h1 className="text-[32px] font-medium text-[#272735] leading-[1.3] tracking-tight">
              {displayTitle}
            </h1>

            {/* Meta 信息 - 匹配设计: 日期 · 时长 · 来源 (点分隔) */}
            <div className="flex items-center gap-6 text-[14px] text-[#6B6B6B]">
              {resource.published_at && (
                <span>{formatDate(resource.published_at)}</span>
              )}
              {resource.duration && (
                <>
                  <span className="text-[#9A9A9A]">·</span>
                  <span>{formatDuration(resource.duration)}</span>
                </>
              )}
              {sourceName && (
                <>
                  <span className="text-[#9A9A9A]">·</span>
                  <span>{sourceName}</span>
                </>
              )}
            </div>
          </header>

          {/* ====== 音频播放器 ====== */}
          {resource.audio_url && (
            <AudioPlayer
              audioUrl={resource.audio_url}
              title={displayTitle}
              description={displaySummary || ''}
              duration={resource.duration}
              onTimeUpdate={handleTimeUpdate}
              className="mb-8"
            />
          )}

          {/* ====== 4 Tab 内容区 ====== */}
          <ContentTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            hasShowNotes={!!(resource.content_markdown || displaySummary)}
            hasChapters={!!(resource.chapters && resource.chapters.length > 0)}
            hasTranscript={!!resource.transcript}
            hasQA={!!(resource.qa_pairs && resource.qa_pairs.length > 0)}
          >
            {renderTabContent()}
          </ContentTabs>
        </main>
      </div>
    </AudioPlayerProvider>
  )
}
