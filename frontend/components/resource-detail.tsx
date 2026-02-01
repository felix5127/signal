/**
 * ResourceDetail - Mercury 风格资源详情页组件
 * 设计规范:
 * - 背景色: #FBFCFD
 * - 主色调: #1E3A5F
 * - 文字色: #272735, #6B6B6B, #9A9A9A
 * - 圆角: 16px
 * - 布局: Header 全宽 + Content Row 两栏 (70% + 380px)
 */
'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ExternalLink, Star } from 'lucide-react'
import { AISummaryCard, AIAssistantCard } from './detail'
import MarkdownRenderer from './markdown-renderer'
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

// 类型路由映射
const TYPE_ROUTES: Record<string, { label: string; href: string }> = {
  article: { label: '文章', href: '/articles' },
  podcast: { label: '播客', href: '/podcasts' },
  tweet: { label: '推文', href: '/tweets' },
  video: { label: '视频', href: '/videos' },
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
    return `${minutes} 分钟阅读`
  }
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟阅读` : `${hours}小时阅读`
}

// 清理 Markdown 内容中的重复头部信息和冗余链接
// 移除: [See all posts], Published on, # 标题, 原文链接, 作者等冗余元数据
function stripMarkdownHeader(content: string): string {
  if (!content) return ''

  let cleaned = content

  // 移除所有 [See all posts] 链接（开头和结尾都可能出现）
  cleaned = cleaned.replace(/\[See all posts\]\([^)]*\)\s*\n*/gi, '')

  // 移除 Published on 日期行
  cleaned = cleaned.replace(/^\s*Published on[^\n]*\n*/im, '')

  // 移除第一个 H1 标题（重复的文章标题）
  cleaned = cleaned.replace(/^\s*#\s+[^\n]+\n*/m, '')

  // 移除 原文/原文链接 行
  cleaned = cleaned.replace(/^\s*原文[：:]\s*\[[^\]]*\]\([^)]*\)\s*\n*/i, '')

  // 移除 作者 行
  cleaned = cleaned.replace(/^\s*作者[：:]\s*\n*[^\n]*\n*/i, '')

  // 清理开头和结尾的多余空行
  cleaned = cleaned.replace(/^\n+/, '').replace(/\n+$/, '')

  return cleaned
}

export default function ResourceDetail({ resource }: ResourceDetailProps) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsLoading(false)
  }, [resource])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FBFCFD]">
        <div className="w-8 h-8 border-4 border-[#E5E5E4] border-t-[#1E3A5F] rounded-full animate-spin" />
      </div>
    )
  }

  // 获取显示的内容（中文优先）
  const displayTitle = resource.title_translated || resource.title
  const displayOneSentence = resource.one_sentence_summary_zh || resource.one_sentence_summary
  const displaySummary = resource.summary_zh || resource.summary
  const displayMainPoints = resource.main_points_zh || resource.main_points
  const typeName = TYPE_NAMES[resource.type] || resource.type
  const typeRoute = TYPE_ROUTES[resource.type] || { label: typeName, href: '/' }
  const displaySourceName = SOURCE_NAMES[resource.source_name] || resource.source_name

  // 处理 AI 助手问题
  const handleAskQuestion = (question: string) => {
    // TODO: 实现 AI 问答功能
    console.log('Ask question:', question)
  }

  return (
    <div className="min-h-screen bg-[#FBFCFD]">
      {/* 主要内容容器 */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            href={typeRoute.href}
            className="text-[#9A9A9A] hover:text-[#1E3A5F] transition-colors duration-200"
          >
            {typeRoute.label}
          </Link>
          <span className="text-[#9A9A9A]">/</span>
          <span className="text-[#272735] font-medium truncate max-w-[300px]">
            当前{typeRoute.label}
          </span>
        </nav>

        {/* ====== Header 区域 (全宽) ====== */}
        <header className="mb-10">
          {/* 标签行 - 匹配设计: 72px x 28px, cornerRadius 6px */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="inline-flex items-center justify-center h-7 px-2.5 rounded-md text-[12px] font-medium bg-[#1E3A5F15] text-[#1E3A5F]">
              {typeName}
            </span>
            {resource.domain && (
              <span className="inline-flex items-center justify-center h-7 px-2.5 rounded-md text-[12px] font-medium bg-[#3D6B4F15] text-[#3D6B4F]">
                {resource.domain}
              </span>
            )}
            {resource.tags && resource.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center justify-center h-7 px-2.5 rounded-md text-[12px] font-medium bg-[#F5F3F0] text-[#6B6B6B]"
              >
                #{tag}
              </span>
            ))}
          </div>

          {/* 大标题 - 匹配设计: 36px, 500 weight, -0.5 letterSpacing, 1.3 lineHeight */}
          <h1 className="text-[28px] sm:text-[32px] lg:text-[36px] font-medium text-[#272735] leading-[1.3] tracking-tight mb-4">
            {displayTitle}
          </h1>

          {/* Meta 信息 - 匹配设计: 评分徽章 + 日期 + 来源 (纯文本，无图标) */}
          <div className="flex flex-wrap items-center gap-6 text-[14px] text-[#9A9A9A]">
            {/* 评分徽章 */}
            {resource.score !== undefined && resource.score > 0 && (
              <div className="flex items-center gap-1.5 bg-[#3D6B4F15] text-[#3D6B4F] px-3 py-1.5 rounded-lg">
                <Star className="w-4 h-4 fill-current" />
                <span className="font-medium">{resource.score}</span>
              </div>
            )}
            {/* 日期 */}
            {resource.published_at && (
              <span>{formatDate(resource.published_at)}</span>
            )}
            {/* 来源 */}
            <span>来源: {displaySourceName}</span>
          </div>
        </header>

        {/* ====== Content Row 两栏布局 - 匹配设计: gap 48px ====== */}
        <div className="flex flex-col lg:flex-row gap-12">
          {/* 左侧 Article Body */}
          <article className="flex-1 min-w-0">
            {/* 正文内容 - 匹配设计: 直接展示文章内容，无摘要框 */}
            {resource.content_markdown ? (
              <div className="prose prose-lg max-w-none">
                <style jsx global>{`
                  .prose {
                    --tw-prose-body: #272735;
                    --tw-prose-headings: #272735;
                    --tw-prose-links: #1E3A5F;
                    --tw-prose-bold: #272735;
                    --tw-prose-quotes: #6B6B6B;
                    --tw-prose-quote-borders: #E5E5E4;
                    --tw-prose-code: #272735;
                    --tw-prose-pre-code: #E5E5E4;
                    --tw-prose-pre-bg: #272735;
                  }
                  .prose p {
                    font-size: 16px;
                    line-height: 1.8;
                    margin-bottom: 20px;
                  }
                  .prose h2, .prose h3, .prose h4 {
                    font-size: 22px;
                    font-weight: 500;
                    margin-top: 32px;
                    margin-bottom: 16px;
                  }
                  .prose ul, .prose ol {
                    margin-top: 1em;
                    margin-bottom: 1em;
                  }
                  .prose li {
                    margin-top: 0.5em;
                    margin-bottom: 0.5em;
                  }
                  .prose blockquote {
                    font-style: italic;
                    border-left-width: 3px;
                    padding-left: 1em;
                    margin-left: 0;
                  }
                  .prose a {
                    text-decoration: underline;
                    text-underline-offset: 2px;
                  }
                  .prose a:hover {
                    color: #2A4A6F;
                  }
                  .prose code {
                    background: #F6F5F2;
                    padding: 0.125em 0.375em;
                    border-radius: 0.25em;
                    font-size: 0.875em;
                  }
                  .prose pre {
                    border-radius: 16px;
                    padding: 1.25em;
                  }
                `}</style>
                <MarkdownRenderer content={stripMarkdownHeader(resource.content_markdown)} />
              </div>
            ) : displaySummary ? (
              <div className="text-[16px] text-[#272735] leading-[1.8] whitespace-pre-line">
                {displaySummary}
              </div>
            ) : (
              <p className="text-[15px] text-[#9A9A9A]">
                暂无内容详情
              </p>
            )}

            {/* 操作按钮 - 与首页 Hero 按钮样式一致 */}
            <div className="mt-10 pt-8 border-t border-[rgba(0,0,0,0.06)] flex flex-wrap items-center gap-4">
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-[10px] bg-[#1E3A5F] text-white text-base font-medium transition-all hover:bg-[#152840]"
              >
                <span>阅读原文</span>
                <ExternalLink className="w-[18px] h-[18px] transition-transform group-hover:translate-x-0.5" />
              </a>
              <DeepResearchButton
                resourceId={resource.id}
                resourceTitle={displayTitle}
                resourceContent={resource.content_markdown || displaySummary}
                resourceUrl={resource.url}
              />
            </div>
          </article>

          {/* 右侧 AI Sidebar (380px) - 匹配设计: gap 24px between cards */}
          <aside className="w-full lg:w-[380px] flex-shrink-0 lg:self-start">
            <div className="lg:sticky lg:top-24 lg:max-h-[calc(100vh-120px)] lg:overflow-y-auto space-y-6 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
              {/* AI 摘要卡片 */}
              <AISummaryCard
                summary={displaySummary}
                oneSentenceSummary={displayOneSentence}
              />

              {/* AI 研究助手卡片 */}
              <AIAssistantCard
                mainPoints={displayMainPoints}
                onAskQuestion={handleAskQuestion}
              />
            </div>
          </aside>
        </div>

        {/* ====== 移动端补充信息 ====== */}
        <div className="lg:hidden mt-10 pt-8 border-t border-[rgba(0,0,0,0.06)]">
          <div className="text-[13px] text-[#9A9A9A] space-y-1">
            <p>ID: {resource.id}</p>
            {resource.analyzed_at && (
              <p>分析时间: {formatDate(resource.analyzed_at)}</p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
