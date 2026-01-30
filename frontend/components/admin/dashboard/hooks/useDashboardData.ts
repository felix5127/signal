/**
 * [INPUT]: Backend API (/api/admin/stats/*)
 * [OUTPUT]: Dashboard 数据 Hook，提供所有统计数据和刷新逻辑
 * [POS]: dashboard/hooks/，数据获取层
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect, useCallback } from 'react'

// ========== 类型定义 ==========

export interface StatsOverview {
  total: number
  by_status: {
    pending: number
    approved: number
    rejected: number
    published: number
  }
  today: {
    total: number
    published: number
  }
  avg_llm_score: number
  sources: {
    total: number
    whitelist: number
  }
}

export interface PipelineStatus {
  pipeline: {
    is_running: boolean
    current_source: string | null
    started_at: string | null
  }
  last_run: {
    finished_at: string | null
    status: string | null
    saved_count: number
    source_type: string | null
  }
  next_run: {
    scheduled_at: string | null
    countdown_seconds: number | null
  }
  queue: {
    pending_translation: number
    pending_transcription: number
  }
}

export interface TodayFunnel {
  fetched: number
  rule_filtered: number
  dedup_filtered: number
  llm_filtered: number
  saved: number
}

export type DailyStats = Array<{
  date: string
  total: number
  published: number
}>

export type ScoreDistribution = Record<string, number>

export interface DataQualityStats {
  podcast_quality: {
    total: number
    has_audio_url: number
    has_transcript: number
    has_chapters: number
    completeness_rate: number
  }
  video_quality: {
    total: number
    has_transcript: number
    has_chapters: number
    completeness_rate: number
  }
  article_quality: {
    total: number
    has_content: number
    has_summary: number
    completeness_rate: number
  }
  overall_completeness: number
}

export interface SourceHealthStats {
  sources: Array<{
    id: number
    name: string
    type: string
    url: string
    collection_success_rate: number
    field_completeness: Record<string, number>
    health_status: 'healthy' | 'degraded' | 'failing'
    last_collected_at: string | null
    last_error: string | null
  }>
  summary: {
    healthy: number
    degraded: number
    failing: number
  }
}

export interface TranscriptionStats {
  podcast: {
    with_audio: number
    transcribed: number
    success_rate: number
    pending: number
  }
  video: {
    total: number
    transcribed: number
    success_rate: number
    pending: number
  }
  recent_failures: Array<{
    resource_id: number
    title: string
    source_name: string
    created_at: string | null
  }>
}

export interface DashboardData {
  overview: StatsOverview | null
  pipelineStatus: PipelineStatus | null
  todayFunnel: TodayFunnel | null
  daily: DailyStats | null
  scores: ScoreDistribution | null
  dataQuality: DataQualityStats | null
  sourceHealth: SourceHealthStats | null
  transcription: TranscriptionStats | null
}

export interface UseDashboardDataReturn extends DashboardData {
  loading: boolean
  error: string | null
  refreshing: boolean
  refresh: () => Promise<void>
  lastRefreshedAt: Date | null
}

// ========== Hook 实现 ==========

const REFRESH_INTERVAL = 30000 // 30 秒刷新一次

export function useDashboardData(): UseDashboardDataReturn {
  const [data, setData] = useState<DashboardData>({
    overview: null,
    pipelineStatus: null,
    todayFunnel: null,
    daily: null,
    scores: null,
    dataQuality: null,
    sourceHealth: null,
    transcription: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setRefreshing(true)
      setError(null)

      // 并行请求所有 API
      const results = await Promise.allSettled([
        fetch('/api/admin/stats/overview', { cache: 'no-store' }),
        fetch('/api/admin/stats/pipeline-status', { cache: 'no-store' }),
        fetch('/api/admin/stats/today-funnel', { cache: 'no-store' }),
        fetch('/api/admin/stats/daily?days=7', { cache: 'no-store' }),
        fetch('/api/admin/stats/score-distribution', { cache: 'no-store' }),
        fetch('/api/admin/stats/data-quality', { cache: 'no-store' }),
        fetch('/api/admin/stats/source-health', { cache: 'no-store' }),
        fetch('/api/admin/stats/transcription', { cache: 'no-store' }),
      ])

      // 不依赖旧状态，直接构建新对象
      const newData: DashboardData = {
        overview: null,
        pipelineStatus: null,
        todayFunnel: null,
        daily: null,
        scores: null,
        dataQuality: null,
        sourceHealth: null,
        transcription: null,
      }
      const errors: string[] = []

      // 处理各个响应
      const handlers: Array<{
        index: number
        key: keyof DashboardData
        name: string
        critical?: boolean
      }> = [
        { index: 0, key: 'overview', name: '总览数据', critical: true },
        { index: 1, key: 'pipelineStatus', name: 'Pipeline 状态', critical: true },
        { index: 2, key: 'todayFunnel', name: '今日漏斗', critical: true },
        { index: 3, key: 'daily', name: '日趋势数据' },
        { index: 4, key: 'scores', name: '评分分布' },
        { index: 5, key: 'dataQuality', name: '数据质量' },
        { index: 6, key: 'sourceHealth', name: '数据源健康' },
        { index: 7, key: 'transcription', name: '转写统计' },
      ]

      for (const handler of handlers) {
        const result = results[handler.index]
        if (result.status === 'fulfilled') {
          const res = result.value
          if (res.ok) {
            const jsonData = await res.json()
            // 使用类型安全的方式更新数据
            switch (handler.key) {
              case 'overview': newData.overview = jsonData; break
              case 'pipelineStatus': newData.pipelineStatus = jsonData; break
              case 'todayFunnel': newData.todayFunnel = jsonData; break
              case 'daily': newData.daily = jsonData; break
              case 'scores': newData.scores = jsonData; break
              case 'dataQuality': newData.dataQuality = jsonData; break
              case 'sourceHealth': newData.sourceHealth = jsonData; break
              case 'transcription': newData.transcription = jsonData; break
            }
          } else if (handler.critical) {
            errors.push(`${handler.name}加载失败`)
          }
        } else if (handler.critical) {
          errors.push(`${handler.name}请求失败`)
          console.error(`${handler.name} API failed:`, result.reason)
        }
      }

      setData(newData)
      setLastRefreshedAt(new Date())

      // 只有关键 API 全部失败时才显示错误
      const criticalErrors = errors.filter(e =>
        e.includes('总览') || e.includes('Pipeline') || e.includes('漏斗')
      )
      if (criticalErrors.length === 3) {
        setError('无法连接到后端 API')
      } else if (errors.length > 0) {
        console.warn('部分数据加载失败:', errors)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    ...data,
    loading,
    error,
    refreshing,
    refresh: fetchData,
    lastRefreshedAt,
  }
}
