/**
 * [INPUT]: 依赖 @/lib/utils, lucide-react, 本地组件 (ScoreBadge/MainPoints/KeyQuotes/TagList)
 * [OUTPUT]: 对外提供 ResourceDetail 组件
 * [POS]: components/ 的资源详情组件，被 /resources/[id] 页面消费，展示 AI 分析结果
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Clock, User, ExternalLink, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ScoreBadge } from './score-badge'
import { MainPoints } from './main-points'
import { KeyQuotes } from './key-quotes'
import { TagList } from './tag-list'
import MarkdownRenderer from './markdown-renderer'
import { FlickeringGrid } from './effects/flickering-grid'
import DeepResearchButton from './deep-research-button'

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

// 格式化阅读时间
function formatReadTime(minutes?: number): string {
  if (!minutes) return ''
  if (minutes < 60) {
    return `${minutes}分钟`
  }
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
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

  // 获取显示的标题
  const displayTitle = resource.title_translated || resource.title

  // 获取一句话总结
  const displayOneSentence =
    resource.one_sentence_summary_zh || resource.one_sentence_summary

  // 获取详细摘要
  const displaySummary = resource.summary_zh || resource.summary

  // 获取主要观点
  const displayMainPoints = resource.main_points_zh || resource.main_points

  // 获取金句
  const displayKeyQuotes = resource.key_quotes_zh || resource.key_quotes

  // 获取来源名称
  const sourceName = SOURCE_NAMES[resource.source_name] || resource.source_name

  const typeName = TYPE_NAMES[resource.type] || resource.type

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 relative">
      {/* Flickering Grid 闪烁网格背景 - 微妙的科技感 */}
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

      {/* 主要内容 */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* 标题区域 */}
        <div className="mb-8">
          {/* 来源信息 */}
          <div className="flex items-center gap-3 mb-4">
            {resource.source_icon_url ? (
              <img
                src={resource.source_icon_url}
                alt={sourceName}
                className="w-6 h-6 rounded"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            ) : (
              <div className="w-6 h-6 rounded bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-600 dark:text-gray-400">
                {sourceName.charAt(0).toUpperCase()}
              </div>
            )}
            <span className="text-sm text-gray-600 dark:text-gray-400">{sourceName}</span>
            {resource.published_at && (
              <>
                <span className="text-gray-400">·</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(resource.published_at).toLocaleDateString('zh-CN', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </span>
              </>
            )}
          </div>

          <div className="flex items-start justify-between gap-4 mb-4">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white leading-tight">
              {displayTitle}
            </h1>
            {resource.score !== undefined && resource.score > 0 && (
              <ScoreBadge score={resource.score} />
            )}
          </div>

          {/* 元信息 */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
            {resource.author && (
              <div className="flex items-center gap-1">
                <User className="w-4 h-4" />
                <span>{resource.author}</span>
              </div>
            )}
            {resource.read_time && (
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>阅读时长 {formatReadTime(resource.read_time)}</span>
              </div>
            )}
            {resource.word_count && (
              <div className="flex items-center gap-1">
                <BookOpen className="w-4 h-4" />
                <span>{resource.word_count} 字</span>
              </div>
            )}
          </div>

          {/* 标签 */}
          {resource.tags && resource.tags.length > 0 && (
            <div className="mt-4">
              <TagList tags={resource.tags} />
            </div>
          )}
        </div>

        {/* 一句话总结 */}
        {displayOneSentence && (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 mb-8 border border-indigo-100 dark:border-indigo-800">
            <p className="text-gray-900 dark:text-white leading-relaxed">
              {displayOneSentence}
            </p>
          </div>
        )}

        {/* 详细摘要 */}
        {displaySummary && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              内容摘要
            </h2>
            <div className="prose prose-gray dark:prose-invert max-w-none">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                {displaySummary}
              </p>
            </div>
          </section>
        )}

        {/* 主要观点 */}
        {displayMainPoints && displayMainPoints.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              主要观点
            </h2>
            <MainPoints points={displayMainPoints} />
          </section>
        )}

        {/* 金句 */}
        {displayKeyQuotes && displayKeyQuotes.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              金句摘录
            </h2>
            <KeyQuotes quotes={displayKeyQuotes} />
          </section>
        )}

        {/* 完整内容 */}
        {resource.content_markdown && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              完整内容
            </h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <MarkdownRenderer content={resource.content_markdown} />
            </div>
          </section>
        )}

        {/* 操作按钮：原文链接 + 深度研究 */}
        <section className="mb-8 flex items-center gap-4 flex-wrap">
          <a
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 text-white rounded-xl font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"
            style={{
              background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
              boxShadow: '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 6px 20px color-mix(in srgb, var(--primary) 45%, transparent), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.15)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)'
            }}
          >
            <span>阅读原文</span>
            <ExternalLink className="w-4 h-4" />
          </a>
          <DeepResearchButton resourceId={resource.id} resourceType="resource" inline={true} />
        </section>

        {/* 深度研究报告（单独section） */}
        <DeepResearchButton resourceId={resource.id} resourceType="resource" reportOnly={true} />

        {/* 元数据信息 */}
        <footer className="pt-8 border-t border-gray-200 dark:border-gray-800">
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
  )
}
