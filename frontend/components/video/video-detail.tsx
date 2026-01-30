/**
 * [INPUT]: 依赖 video/ 子组件, @/lib/utils
 * [OUTPUT]: 对外提供 VideoDetail 组件
 * [POS]: video/ 的视频详情页主组件，匹配 Pencil 设计稿
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FileText, BookOpen, MessageSquare, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { VideoPlayer } from './video-player'
import DeepResearchButton from '../deep-research-button'

export interface VideoResource {
  id: number
  type: 'video'
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
  duration?: number
  video_url?: string
  thumbnail_url?: string
  transcript?: string
  chapters?: Array<{ time: number; title: string; summary?: string }>
  qa_pairs?: Array<{ question: string; answer: string }>
  view_count?: number
  published_at?: string
  created_at?: string
  analyzed_at?: string
}

interface VideoDetailProps {
  resource: VideoResource
}

type TabKey = 'overview' | 'chapters' | 'transcript' | 'qa'

interface Tab {
  key: TabKey
  label: string
  icon: React.ReactNode
}

const TABS: Tab[] = [
  { key: 'overview', label: '视频简介', icon: <FileText className="w-4 h-4" /> },
  { key: 'chapters', label: '章节概览', icon: <BookOpen className="w-4 h-4" /> },
  { key: 'transcript', label: '转录文本', icon: <MessageSquare className="w-4 h-4" /> },
  { key: 'qa', label: 'Q&A 回顾', icon: <HelpCircle className="w-4 h-4" /> },
]

// 来源名称映射
const SOURCE_NAMES: Record<string, string> = {
  youtube: 'YouTube',
  bilibili: 'Bilibili',
  openai: 'OpenAI',
  hn: 'Hacker News',
  github: 'GitHub',
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

// 格式化观看数
function formatViewCount(count?: number): string {
  if (!count) return ''
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万 观看`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K 观看`
  }
  return `${count} 观看`
}

export function VideoDetail({ resource }: VideoDetailProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview')

  // 获取显示的内容（中文优先）
  const displayTitle = resource.title_translated || resource.title
  const displaySummary = resource.summary_zh || resource.summary || resource.one_sentence_summary_zh || resource.one_sentence_summary
  const sourceName = SOURCE_NAMES[resource.source_name] || resource.source_name

  // Tab 内容是否可用
  const tabAvailability: Record<TabKey, boolean> = {
    'overview': !!(resource.content_markdown || displaySummary),
    'chapters': !!(resource.chapters && resource.chapters.length > 0),
    'transcript': !!resource.transcript,
    'qa': !!(resource.qa_pairs && resource.qa_pairs.length > 0),
  }

  // 渲染 Tab 内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-5">
            <h3 className="text-[18px] font-semibold text-[#272735]">视频简介</h3>
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
                暂无视频简介
              </div>
            )}
          </div>
        )

      case 'chapters':
        return (
          <div className="space-y-5">
            <h3 className="text-[18px] font-semibold text-[#272735]">章节概览</h3>
            {resource.chapters && resource.chapters.length > 0 ? (
              <div className="space-y-3">
                {resource.chapters.map((chapter, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-4 p-3 rounded-lg hover:bg-[#F5F3F0] transition-colors cursor-pointer"
                  >
                    <span className="text-[13px] font-medium text-[#1E3A5F] whitespace-nowrap">
                      {formatDuration(chapter.time)}
                    </span>
                    <div>
                      <p className="text-[14px] font-medium text-[#272735]">{chapter.title}</p>
                      {chapter.summary && (
                        <p className="text-[13px] text-[#6B6B6B] mt-1">{chapter.summary}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#9A9A9A]">
                暂无章节信息
              </div>
            )}
          </div>
        )

      case 'transcript':
        return (
          <div className="space-y-5">
            <h3 className="text-[18px] font-semibold text-[#272735]">转录文本</h3>
            {resource.transcript ? (
              <div className="text-[15px] text-[#6B6B6B] leading-[1.7] whitespace-pre-line">
                {resource.transcript}
              </div>
            ) : (
              <div className="text-center py-8 text-[#9A9A9A]">
                暂无转录文本
              </div>
            )}
          </div>
        )

      case 'qa':
        return (
          <div className="space-y-5">
            <h3 className="text-[18px] font-semibold text-[#272735]">Q&A 回顾</h3>
            {resource.qa_pairs && resource.qa_pairs.length > 0 ? (
              <div className="space-y-4">
                {resource.qa_pairs.map((qa, index) => (
                  <div key={index} className="border-b border-[#E8E5E0] pb-4 last:border-0">
                    <p className="text-[14px] font-medium text-[#272735] mb-2">
                      Q: {qa.question}
                    </p>
                    <p className="text-[14px] text-[#6B6B6B] leading-[1.6]">
                      A: {qa.answer}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#9A9A9A]">
                暂无 Q&A 内容
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
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
            href="/videos"
            className="text-[#9A9A9A] hover:text-[#1E3A5F] transition-colors duration-200"
          >
            视频
          </Link>
          <span className="text-[#9A9A9A]">/</span>
          <span className="text-[#272735] font-medium">当前视频</span>
        </nav>

        {/* ====== 视频播放器 ====== */}
        <VideoPlayer
          videoUrl={resource.video_url}
          thumbnailUrl={resource.thumbnail_url}
          duration={resource.duration}
          className="mb-8"
        />

        {/* ====== Header 区域 ====== */}
        <header className="mb-8 space-y-4">
          {/* 标签行 */}
          <div className="flex flex-wrap items-center gap-2">
            {resource.domain && (
              <span className="inline-flex items-center px-3 py-1.5 rounded-md text-[12px] font-medium bg-[#DCFCE7] text-[#16A34A]">
                {resource.domain}
              </span>
            )}
            {resource.tags && resource.tags.slice(0, 2).map((tag, index) => (
              <span
                key={index}
                className={cn(
                  "inline-flex items-center px-3 py-1.5 rounded-md text-[12px] font-medium",
                  index === 0 ? "bg-[#EEF2FF] text-[#4F46E5]" : "bg-[#F5F3F0] text-[#6B6B6B]"
                )}
              >
                {tag}
              </span>
            ))}
          </div>

          {/* 大标题 */}
          <h1 className="text-[32px] font-medium text-[#272735] leading-[1.3] tracking-tight">
            {displayTitle}
          </h1>

          {/* Meta 信息 */}
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
            {resource.view_count && (
              <>
                <span className="text-[#9A9A9A]">·</span>
                <span>{formatViewCount(resource.view_count)}</span>
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

        {/* ====== Tab 区域 ====== */}
        <div className="space-y-6">
          {/* Tab 导航 */}
          <div className="flex items-center gap-1 p-1 bg-[#F5F3F0] rounded-xl overflow-x-auto">
            {TABS.map((tab) => {
              const isActive = activeTab === tab.key
              const isAvailable = tabAvailability[tab.key]

              return (
                <button
                  key={tab.key}
                  onClick={() => isAvailable && setActiveTab(tab.key)}
                  className={cn(
                    'flex items-center gap-2 px-5 py-2.5 rounded-lg text-[14px] font-medium whitespace-nowrap transition-all',
                    isActive
                      ? 'bg-white text-[#272735] shadow-sm'
                      : isAvailable
                      ? 'text-[#6B6B6B] hover:text-[#272735]'
                      : 'text-[#9A9A9A] cursor-not-allowed'
                  )}
                  disabled={!isAvailable}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* Tab 内容卡片 */}
          <div className="rounded-2xl bg-white border border-[#E8E5E0] p-6">
            {renderTabContent()}
          </div>
        </div>

        {/* ====== 操作按钮 ====== */}
        <div className="mt-10 pt-8 border-t border-[rgba(0,0,0,0.06)] flex flex-wrap items-center gap-4">
          <a
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-[10px] bg-[#1E3A5F] text-white text-base font-medium transition-all hover:bg-[#152840]"
          >
            <span>观看原视频</span>
          </a>
          <DeepResearchButton
            resourceId={resource.id}
            resourceTitle={displayTitle}
            resourceContent={resource.content_markdown || displaySummary}
            resourceUrl={resource.url}
          />
        </div>
      </main>
    </div>
  )
}
