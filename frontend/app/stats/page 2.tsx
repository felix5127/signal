/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/stats)
 * [OUTPUT]: 对外提供统计数据页面，展示系统运行数据
 * [POS]: app/ 的统计页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import { AlertTriangle, BookOpen, TrendingUp, Star, Target, Database, FolderOpen, Settings, Clock } from 'lucide-react'

export default function StatsPage() {
  const [stats, setStats] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`/api/stats`, {
          cache: 'no-store',
        })
        const data = await res.json()
        setStats(data)
      } catch (e) {
        setError('无法连接到后端 API')
        console.error('API Error:', e)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--ds-surface)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-200 dark:border-indigo-800 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[var(--ds-muted)]">加载中...</p>
        </div>
      </div>
    )
  }

  if (error || !stats || !stats.average_scores) {
    return (
      <div className="min-h-screen bg-[var(--ds-surface)] flex items-center justify-center">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-8 max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-[var(--ds-fg)] mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              {error}
            </h2>
            <a href="/" className="text-indigo-600 hover:text-indigo-700 transition-colors">
              返回首页
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--ds-surface)] py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 头部 */}
        <div className="mb-8">
          <a href="/" className="inline-flex items-center gap-2 text-[var(--ds-accent)] hover:text-[var(--ds-accent-2)] transition-colors mb-4">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回首页
          </a>
          <h1 className="text-3xl font-bold text-[var(--ds-fg)] mb-2">数据统计</h1>
          <p className="text-[var(--ds-muted)]">Signal Hunter 系统运行数据概览</p>
        </div>

        {/* 核心指标 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
            <div className="text-sm opacity-90 mb-2 flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              总信号数
            </div>
            <div className="text-4xl font-bold">{stats.total_signals}</div>
          </div>
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
            <div className="text-sm opacity-90 mb-2 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              平均热度
            </div>
            <div className="text-4xl font-bold">{stats.average_scores.heat}/5</div>
          </div>
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
            <div className="text-sm opacity-90 mb-2 flex items-center gap-2">
              <Star className="w-4 h-4" />
              平均质量
            </div>
            <div className="text-4xl font-bold">{stats.average_scores.quality}/5</div>
          </div>
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
            <div className="text-sm opacity-90 mb-2 flex items-center gap-2">
              <Target className="w-4 h-4" />
              平均评分
            </div>
            <div className="text-4xl font-bold">{stats.average_scores.final}/5</div>
          </div>
        </div>

        {/* 数据源分布 */}
        {Object.keys(stats.by_source).length > 0 && (
          <div className="bg-[var(--ds-bg)] rounded-2xl p-6 border border-[var(--ds-border)] mb-6">
            <h2 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">📡 数据源分布</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_source)
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([source, count]) => {
                  const maxCount = Math.max(...Object.values(stats.by_source) as number[])
                  const percentage = ((count as number) / maxCount) * 100
                  return (
                    <div key={source} className="flex items-center gap-3">
                      <div className="min-w-[100px] text-sm font-medium text-[var(--ds-muted)]">
                        {source === 'hn' ? 'Hacker News' : source}
                      </div>
                      <div className="flex-1 h-8 bg-[var(--ds-surface-2)] rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-end pr-3 text-white text-xs font-semibold transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        >
                          {count as number}
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}

        {/* 分类分布 */}
        {Object.keys(stats.by_category).length > 0 && (
          <div className="bg-[var(--ds-bg)] rounded-2xl p-6 border border-[var(--ds-border)] mb-6">
            <h2 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">📂 分类分布</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_category)
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([category, count]) => {
                  const maxCount = Math.max(...Object.values(stats.by_category) as number[])
                  const percentage = ((count as number) / maxCount) * 100
                  return (
                    <div key={category} className="flex items-center gap-3">
                      <div className="min-w-[100px] text-sm font-medium text-[var(--ds-muted)]">
                        {category}
                      </div>
                      <div className="flex-1 h-8 bg-[var(--ds-surface-2)] rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-end pr-3 text-white text-xs font-semibold transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        >
                          {count as number}
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}

        {/* 评分分布 */}
        {Object.keys(stats.by_score).length > 0 && (
          <div className="bg-[var(--ds-bg)] rounded-2xl p-6 border border-[var(--ds-border)] mb-6">
            <h2 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">⭐ 评分分布</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_score)
                .sort((a, b) => Number(b[0]) - Number(a[0]))
                .map(([score, count]) => {
                  const maxCount = Math.max(...Object.values(stats.by_score) as number[])
                  const percentage = ((count as number) / maxCount) * 100
                  return (
                    <div key={score} className="flex items-center gap-3">
                      <div className="min-w-[100px] text-sm font-medium text-[var(--ds-muted)]">
                        {'★'.repeat(Number(score))}{'☆'.repeat(5 - Number(score))}
                      </div>
                      <div className="flex-1 h-8 bg-[var(--ds-surface-2)] rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-end pr-3 text-white text-xs font-semibold transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        >
                          {count as number}
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}

        {/* 系统信息 */}
        <div className="bg-[var(--ds-bg)] rounded-2xl p-6 border border-[var(--ds-border)]">
          <h2 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">⚙️ 系统信息</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[var(--ds-surface-2)] rounded-xl p-4 border border-[var(--ds-border)]">
              <div className="text-xs text-[var(--ds-muted)] mb-1">最新更新时间</div>
              <div className="text-sm font-medium text-[var(--ds-fg)]">
                {stats.latest_update
                  ? new Date(stats.latest_update).toLocaleString('zh-CN')
                  : '暂无数据'}
              </div>
            </div>
            {stats.scheduler.last_run && (
              <div className="bg-[var(--ds-surface-2)] rounded-xl p-4 border border-[var(--ds-border)]">
                <div className="text-xs text-[var(--ds-muted)] mb-1">上次运行时间</div>
                <div className="text-sm font-medium text-[var(--ds-fg)]">
                  {new Date(stats.scheduler.last_run).toLocaleString('zh-CN')}
                </div>
              </div>
            )}
            {stats.scheduler.next_run && (
              <div className="bg-[var(--ds-surface-2)] rounded-xl p-4 border border-[var(--ds-border)]">
                <div className="text-xs text-[var(--ds-muted)] mb-1">下次运行时间</div>
                <div className="text-sm font-medium text-[var(--ds-fg)]">
                  {new Date(stats.scheduler.next_run).toLocaleString('zh-CN')}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
