'use client'
/**
 * [INPUT]: 依赖 useState/useEffect, /api/digest/today, /api/digest/week
 * [OUTPUT]: 精选页面（日报 + 周报，同格式展示）
 * [POS]: app/ 的内容页面，替代原 newsletters
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */



// 强制动态渲染，禁用静态生成


import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Clock, Inbox, TrendingUp, FolderOpen, BarChart3, Trophy, Rocket, Wrench, Lightbulb, FileText } from 'lucide-react'

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

// ========== 通用报告组件 ==========

function ReportHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="text-center py-10 border-b-2 border-gray-100 mb-10">
      <h2 className="text-3xl font-bold text-gray-900 mb-3">{title}</h2>
      <p className="text-gray-500 text-sm">{subtitle}</p>
    </div>
  )
}

function StatsGrid({ stats }: { stats: { label: string; value: string | number }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-gradient-to-br from-blue-600 to-purple-600 text-white p-5 rounded-xl text-center"
        >
          <div className="text-3xl font-bold mb-1">{stat.value}</div>
          <div className="text-xs opacity-90">{stat.label}</div>
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
  return (
    <ul className="space-y-3">
      {signals.map((signal, index) => (
        <li
          key={signal.id}
          className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-sm transition-all"
        >
          <div className="font-semibold text-gray-900 mb-2 flex items-start gap-2">
            {showRank && (
              <span className="text-blue-600 font-bold shrink-0">#{startIndex + index + 1}</span>
            )}
            <a
              href={signal.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600"
            >
              {signal.title}
            </a>
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-gray-500">
            <span className="text-yellow-500">
              {'★'.repeat(signal.final_score)}
              {'☆'.repeat(5 - signal.final_score)}
            </span>
            {signal.category && <span className="flex items-center gap-1"><FolderOpen className="w-3 h-3" />{signal.category}</span>}
            <span className="uppercase">{signal.source}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}

function TagList({ tags, icon = '' }: { tags: string[]; icon?: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, index) => (
        <span
          key={index}
          className="bg-indigo-100 text-indigo-700 px-3 py-1.5 rounded-md text-sm font-medium"
        >
          {icon}{tag}
        </span>
      ))}
    </div>
  )
}

function SummarySection({ summary }: { summary: string }) {
  return (
    <div className="prose prose-gray max-w-none">
      <ReactMarkdown>{summary}</ReactMarkdown>
    </div>
  )
}

// ========== 日报组件 ==========

function DailyReport({ digest }: { digest: DailyDigest }) {
  const stats = [
    { label: '今日信号总数', value: digest.total_signals },
    { label: 'HackerNews', value: digest.top_hn.length },
    { label: 'GitHub', value: digest.top_github.length },
    { label: 'HuggingFace', value: digest.top_hf.length },
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
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            HackerNews Top
          </h3>
          <SignalList signals={digest.top_hn} showRank={false} />
        </section>
      )}

      {digest.top_github.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            GitHub 精选
          </h3>
          <SignalList signals={digest.top_github} showRank={false} />
        </section>
      )}

      {digest.top_hf.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            🤗 HuggingFace 热门
          </h3>
          <SignalList signals={digest.top_hf} showRank={false} />
        </section>
      )}

      {digest.top_other.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            📰 其他来源
          </h3>
          <SignalList signals={digest.top_other} showRank={false} />
        </section>
      )}

      {digest.trending_topics.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            热门话题
          </h3>
          <TagList tags={digest.trending_topics} />
        </section>
      )}

      {digest.summary && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            今日概览
          </h3>
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
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <Trophy className="w-5 h-5" />
            本周 Top 10
          </h3>
          <SignalList signals={digest.top_10} />
        </section>
      )}

      {digest.top_breakthroughs.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <Rocket className="w-5 h-5" />
            技术突破 Top 3
          </h3>
          <SignalList signals={digest.top_breakthroughs} showRank={false} />
        </section>
      )}

      {digest.top_tools.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <Wrench className="w-5 h-5" />
            开源工具 Top 3
          </h3>
          <SignalList signals={digest.top_tools} showRank={false} />
        </section>
      )}

      {digest.trending_topics.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            热门话题
          </h3>
          <TagList tags={digest.trending_topics} />
        </section>
      )}

      {digest.hot_keywords.length > 0 && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            高频关键词
          </h3>
          <TagList tags={digest.hot_keywords} />
        </section>
      )}

      {digest.summary && (
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-3 border-b-2 border-gray-100 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            本周概览
          </h3>
          <SummarySection summary={digest.summary} />
        </section>
      )}
    </div>
  )
}

// ========== 加载/错误状态 ==========

function LoadingState() {
  return (
    <div className="text-center py-20 text-gray-400">
      <Clock className="w-12 h-12 mx-auto mb-4 animate-pulse" />
      <p className="text-lg font-medium">加载中...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-20">
      <Inbox className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <p className="text-lg font-medium text-red-500 mb-2">{message}</p>
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
    // 使用相对路径，通过 Next.js API 代理访问后端

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
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-2">精选内容</h1>
          <p className="text-gray-600">AI 精选的每日信号与周度报告</p>
        </div>

        {/* 日报区 */}
        <section className="mb-20">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span className="w-2 h-8 bg-blue-600 rounded"></span>
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
        <hr className="border-gray-200 my-16" />

        {/* 周报区 */}
        <section>
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span className="w-2 h-8 bg-purple-600 rounded"></span>
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
