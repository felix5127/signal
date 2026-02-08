/**
 * FeaturedPageContent - Mercury 风格精选页面
 * 特点: 简洁大气、清晰层级、专业感
 */
'use client'

import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Clock, Inbox, TrendingUp, FolderOpen, BarChart3, Trophy, Rocket, Wrench, Lightbulb, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

// ========== 类型定义 ==========

interface Signal {
  id: number
  title: string
  url: string
  source: string
  category?: string
  final_score: number
  created_at: string
}

interface DailyDigest {
  date: string
  total_signals: number
  sources_breakdown: { [key: string]: number }
  top_hn: Signal[]
  top_github: Signal[]
  top_hf: Signal[]
  top_other: Signal[]
  summary: string
  trending_topics: string[]
  created_at: string
}

interface WeeklyDigest {
  week_start: string
  week_end: string
  total_signals: number
  sources_breakdown: { [key: string]: number }
  top_10: Signal[]
  top_breakthroughs: Signal[]
  top_tools: Signal[]
  top_papers: Signal[]
  top_news: Signal[]
  summary: string
  trending_topics: string[]
  hot_keywords: string[]
  created_at: string
}

// ========== Mercury 风格通用组件 ==========

function ReportHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="text-center py-10 border-b border-[var(--border-default)] mb-10">
      <h2 className="h1 text-[var(--text-primary)] mb-3">{title}</h2>
      <p className="text-[var(--text-muted)] text-[var(--text-body-sm)]">{subtitle}</p>
    </div>
  )
}

function StatsGrid({ stats }: { stats: { label: string; value: string | number }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-[var(--color-primary)] text-white p-5 rounded-[var(--radius-xl)] text-center"
        >
          <div className="text-[var(--text-h1)] font-bold mb-1">{stat.value}</div>
          <div className="text-[var(--text-xs)] opacity-90">{stat.label}</div>
        </div>
      ))}
    </div>
  )
}

function SignalList({
  signals,
  startIndex = 0,
  showRank = true,
}: {
  signals: Signal[]
  startIndex?: number
  showRank?: boolean
}) {
  // 评分颜色
  function getScoreStars(score: number): string {
    return '★'.repeat(Math.min(score, 5)) + '☆'.repeat(Math.max(0, 5 - score))
  }

  return (
    <ul className="space-y-3">
      {signals.map((signal, index) => (
        <li
          key={signal.id}
          className="p-4 border border-[var(--border-default)] rounded-[var(--radius-lg)] hover:border-[var(--color-primary)] hover:shadow-[var(--shadow-sm)] transition-all duration-200"
        >
          <div className="h4 text-[var(--text-primary)] mb-2 flex items-start gap-2">
            {showRank && (
              <span className="text-[var(--color-primary)] font-bold shrink-0">#{startIndex + index + 1}</span>
            )}
            <a
              href={signal.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--color-primary)] transition-colors"
            >
              {signal.title}
            </a>
          </div>
          <div className="flex flex-wrap gap-3 text-[var(--text-body-sm)] text-[var(--text-muted)]">
            <span className="text-[var(--color-accent)]">
              {getScoreStars(signal.final_score)}
            </span>
            {signal.category && (
              <span className="flex items-center gap-1">
                <FolderOpen className="w-3 h-3" />
                {signal.category}
              </span>
            )}
            <Badge variant="secondary-soft" className="text-[var(--text-xs)] uppercase">
              {signal.source}
            </Badge>
          </div>
        </li>
      ))}
    </ul>
  )
}

function TagList({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, index) => (
        <Badge key={index} variant="primary-soft">
          {tag}
        </Badge>
      ))}
    </div>
  )
}

function SummarySection({ summary }: { summary: string }) {
  return (
    <div className="prose prose-gray max-w-none text-[var(--text-secondary)]">
      <ReactMarkdown>{summary}</ReactMarkdown>
    </div>
  )
}

function SectionHeader({ icon: Icon, title }: { icon: React.ComponentType<{ className?: string }>; title: string }) {
  return (
    <h3 className="h3 text-[var(--text-primary)] mb-4 pb-3 border-b border-[var(--border-default)] flex items-center gap-2">
      <Icon className="w-5 h-5 text-[var(--color-primary)]" />
      {title}
    </h3>
  )
}

// ========== 日报组件 ==========

function DailyReport({ digest }: { digest: DailyDigest }) {
  const stats = [
    { label: '今日信号总数', value: digest.total_signals },
    { label: '人工智能', value: digest.top_hn.length },
    { label: '软件编程', value: digest.top_github.length },
    { label: '商业科技', value: digest.top_hf.length },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <ReportHeader
        title="日报"
        subtitle={`生成时间: ${new Date(digest.created_at).toLocaleString('zh-CN')}`}
      />

      <StatsGrid stats={stats} />

      {digest.top_hn.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={TrendingUp} title="人工智能 Top" />
          <SignalList signals={digest.top_hn} showRank={false} />
        </section>
      )}

      {digest.top_github.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={BarChart3} title="软件编程 精选" />
          <SignalList signals={digest.top_github} showRank={false} />
        </section>
      )}

      {digest.top_hf.length > 0 && (
        <section className="mb-10">
          <h3 className="h3 text-[var(--text-primary)] mb-4 pb-3 border-b border-[var(--border-default)] flex items-center gap-2">
            <span className="text-[var(--color-primary)]">💼</span>
            商业科技 热门
          </h3>
          <SignalList signals={digest.top_hf} showRank={false} />
        </section>
      )}

      {digest.top_other.length > 0 && (
        <section className="mb-10">
          <h3 className="h3 text-[var(--text-primary)] mb-4 pb-3 border-b border-[var(--border-default)] flex items-center gap-2">
            <span className="text-[var(--color-primary)]">📰</span>
            其他来源
          </h3>
          <SignalList signals={digest.top_other} showRank={false} />
        </section>
      )}

      {digest.trending_topics.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={TrendingUp} title="热门话题" />
          <TagList tags={digest.trending_topics} />
        </section>
      )}

      {digest.summary && (
        <section className="mb-10">
          <SectionHeader icon={FileText} title="今日概览" />
          <SummarySection summary={digest.summary} />
        </section>
      )}
    </div>
  )
}

// ========== 周报组件 ==========

function WeeklyReport({ digest }: { digest: WeeklyDigest }) {
  const stats = [
    { label: '本周信号总数', value: digest.total_signals },
    { label: 'Top 10 精选', value: digest.top_10.length },
    { label: '技术突破', value: digest.top_breakthroughs.length },
    { label: '数据源数量', value: Object.keys(digest.sources_breakdown).length },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <ReportHeader
        title="周报"
        subtitle={`${new Date(digest.week_start).toLocaleDateString('zh-CN')} - ${new Date(digest.week_end).toLocaleDateString('zh-CN')} | 生成: ${new Date(digest.created_at).toLocaleString('zh-CN')}`}
      />

      <StatsGrid stats={stats} />

      {digest.top_10.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={Trophy} title="本周 Top 10" />
          <SignalList signals={digest.top_10} />
        </section>
      )}

      {digest.top_breakthroughs.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={Rocket} title="技术突破 Top 3" />
          <SignalList signals={digest.top_breakthroughs} showRank={false} />
        </section>
      )}

      {digest.top_tools.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={Wrench} title="开源工具 Top 3" />
          <SignalList signals={digest.top_tools} showRank={false} />
        </section>
      )}

      {digest.trending_topics.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={TrendingUp} title="热门话题" />
          <TagList tags={digest.trending_topics} />
        </section>
      )}

      {digest.hot_keywords.length > 0 && (
        <section className="mb-10">
          <SectionHeader icon={Lightbulb} title="高频关键词" />
          <TagList tags={digest.hot_keywords} />
        </section>
      )}

      {digest.summary && (
        <section className="mb-10">
          <SectionHeader icon={FileText} title="本周概览" />
          <SummarySection summary={digest.summary} />
        </section>
      )}
    </div>
  )
}

// ========== 加载/错误状态 ==========

function LoadingState() {
  return (
    <div className="text-center py-20 text-[var(--text-muted)]">
      <Clock className="w-12 h-12 mx-auto mb-4 animate-pulse" />
      <p className="text-[var(--text-body-lg)] font-medium">加载中...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-20">
      <Inbox className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
      <p className="text-[var(--text-body-lg)] font-medium text-[var(--color-error)] mb-2">{message}</p>
    </div>
  )
}

// ========== 主页面 ==========

export default function FeaturedPage() {
  const [dailyDigest, setDailyDigest] = useState<DailyDigest | null>(null)
  const [weeklyDigest, setWeeklyDigest] = useState<WeeklyDigest | null>(null)
  const [dailyLoading, setDailyLoading] = useState(true)
  const [weeklyLoading, setWeeklyLoading] = useState(true)
  const [dailyError, setDailyError] = useState('')
  const [weeklyError, setWeeklyError] = useState('')

  useEffect(() => {
    // 获取日报
    fetch(`/api/digest/today`)
      .then((res) => {
        if (res.status === 404) {
          setDailyError('昨日精选尚未生成，请等待每日 07:00 自动生成')
          return null
        }
        if (!res.ok) throw new Error('Failed to fetch daily digest')
        return res.json()
      })
      .then((data) => {
        if (data) setDailyDigest(data)
      })
      .catch((err) => {
        setDailyError(err.message || '加载失败')
      })
      .finally(() => {
        setDailyLoading(false)
      })

    // 获取周报
    fetch(`/api/digest/week`)
      .then((res) => {
        if (res.status === 404) {
          setWeeklyError('上周精选尚未生成，请等待每周一 08:00 自动生成')
          return null
        }
        if (!res.ok) throw new Error('Failed to fetch weekly digest')
        return res.json()
      })
      .then((data) => {
        if (data) setWeeklyDigest(data)
      })
      .catch((err) => {
        setWeeklyError(err.message || '加载失败')
      })
      .finally(() => {
        setWeeklyLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* 日报区 */}
        <section className="mb-20">
          <h2 className="h2 mb-6 flex items-center gap-3 text-[var(--text-primary)]">
            <span className="w-1.5 h-8 bg-[var(--color-primary)] rounded-full"></span>
            日报
          </h2>
          {dailyLoading ? (
            <LoadingState />
          ) : dailyError ? (
            <ErrorState message={dailyError} />
          ) : dailyDigest ? (
            <DailyReport digest={dailyDigest} />
          ) : null}
        </section>

        {/* 分隔线 */}
        <hr className="border-[var(--border-default)] my-16" />

        {/* 周报区 */}
        <section>
          <h2 className="h2 mb-6 flex items-center gap-3 text-[var(--text-primary)]">
            <span className="w-1.5 h-8 bg-[var(--color-accent)] rounded-full"></span>
            周报
          </h2>
          {weeklyLoading ? (
            <LoadingState />
          ) : weeklyError ? (
            <ErrorState message={weeklyError} />
          ) : weeklyDigest ? (
            <WeeklyReport digest={weeklyDigest} />
          ) : null}
        </section>
      </div>
    </div>
  )
}
