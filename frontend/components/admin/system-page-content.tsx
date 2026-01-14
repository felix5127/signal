/**
 * [INPUT]: 依赖 React useState/useEffect、Backend API (/api/stats/system)
 * [OUTPUT]: 对外提供系统健康状态页面
 * [POS]: admin/ 的系统监控页面，展示数据库/Redis/存储状态
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import {
  RefreshCw,
  AlertTriangle,
  Database,
  Server,
  HardDrive,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react'

// ========== 类型定义 ==========

interface DatabaseHealth {
  status: string
  message: string
  size_mb?: number
  active_connections?: number
}

interface RedisHealth {
  status: string
  message: string
  used_memory_mb?: number
  keys_count?: number
  connected_clients?: number
}

interface StorageStats {
  resources_total: number
  source_runs_total: number
  new_resources_7d: number
  by_type: Record<string, number>
  error?: string
}

interface SystemHealth {
  database: DatabaseHealth
  redis: RedisHealth
  storage: StorageStats
}

// ========== 组件 ==========

function StatusBadge({ status }: { status: string }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          icon: CheckCircle,
          color: 'text-green-500',
          bg: 'bg-green-100 dark:bg-green-900/30',
          label: '正常',
        }
      case 'disabled':
        return {
          icon: AlertCircle,
          color: 'text-yellow-500',
          bg: 'bg-yellow-100 dark:bg-yellow-900/30',
          label: '已禁用',
        }
      case 'error':
        return {
          icon: XCircle,
          color: 'text-red-500',
          bg: 'bg-red-100 dark:bg-red-900/30',
          label: '错误',
        }
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-500',
          bg: 'bg-gray-100 dark:bg-gray-800',
          label: '未知',
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${config.bg}`}>
      <Icon className={`w-4 h-4 ${config.color}`} />
      <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
    </div>
  )
}

function StatCard({
  icon: Icon,
  title,
  children,
}: {
  icon: any
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
          <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h3 className="text-lg font-semibold text-[var(--ds-fg)]">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function MetricRow({
  label,
  value,
  unit,
}: {
  label: string
  value: string | number | null | undefined
  unit?: string
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[var(--ds-border)] last:border-0">
      <span className="text-sm text-[var(--ds-muted)]">{label}</span>
      <span className="font-mono text-sm text-[var(--ds-fg)]">
        {value ?? '-'}
        {unit && <span className="text-[var(--ds-muted)] ml-1">{unit}</span>}
      </span>
    </div>
  )
}

// ========== 主页面 ==========

export default function SystemPage() {
  const [system, setSystem] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      setRefreshing(true)
      const res = await fetch('/api/stats/system', { cache: 'no-store' })
      const data = await res.json()

      if (data.success) {
        setSystem(data.data)
        setError(null)
      } else {
        setError(data.error || '获取系统状态失败')
      }
    } catch (e) {
      setError('无法连接到后端 API')
      console.error('API Error:', e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
    // 每 60 秒自动刷新
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-200 dark:border-indigo-800 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[var(--ds-muted)]">加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-8 max-w-md">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--ds-fg)] mb-2">
              {error}
            </h2>
            <button
              onClick={fetchData}
              className="text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--ds-fg)]">系统状态</h1>
            <p className="text-[var(--ds-muted)] mt-1">
              监控数据库、缓存和存储的健康状态
            </p>
          </div>
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--ds-bg)] border border-[var(--ds-border)] rounded-lg text-[var(--ds-fg)] hover:bg-[var(--ds-surface)] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>

        {/* 状态卡片网格 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 数据库状态 */}
          <StatCard icon={Database} title="数据库 (PostgreSQL)">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-[var(--ds-muted)]">状态</span>
              <StatusBadge status={system?.database.status || 'unknown'} />
            </div>
            <p className="text-sm text-[var(--ds-muted)] mb-4">
              {system?.database.message}
            </p>
            <div className="space-y-0">
              <MetricRow
                label="数据库大小"
                value={system?.database.size_mb}
                unit="MB"
              />
              <MetricRow
                label="活跃连接数"
                value={system?.database.active_connections}
              />
            </div>
          </StatCard>

          {/* Redis 状态 */}
          <StatCard icon={Server} title="缓存 (Redis)">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-[var(--ds-muted)]">状态</span>
              <StatusBadge status={system?.redis.status || 'unknown'} />
            </div>
            <p className="text-sm text-[var(--ds-muted)] mb-4">
              {system?.redis.message}
            </p>
            <div className="space-y-0">
              <MetricRow
                label="内存使用"
                value={system?.redis.used_memory_mb}
                unit="MB"
              />
              <MetricRow
                label="键数量"
                value={system?.redis.keys_count}
              />
              <MetricRow
                label="连接客户端"
                value={system?.redis.connected_clients}
              />
            </div>
          </StatCard>

          {/* 存储统计 */}
          <StatCard icon={HardDrive} title="存储统计">
            <div className="space-y-0">
              <MetricRow
                label="资源总数"
                value={system?.storage.resources_total?.toLocaleString()}
              />
              <MetricRow
                label="采集记录"
                value={system?.storage.source_runs_total?.toLocaleString()}
              />
              <MetricRow
                label="7天新增"
                value={system?.storage.new_resources_7d?.toLocaleString()}
              />
            </div>
          </StatCard>

          {/* 按类型统计 */}
          <StatCard icon={Database} title="资源类型分布">
            <div className="space-y-0">
              {system?.storage.by_type &&
                Object.entries(system.storage.by_type).map(([type, count]) => (
                  <MetricRow
                    key={type}
                    label={
                      {
                        article: '文章',
                        tweet: '推文',
                        podcast: '播客',
                        video: '视频',
                      }[type] || type
                    }
                    value={count.toLocaleString()}
                  />
                ))}
            </div>
          </StatCard>
        </div>
      </div>
    </div>
  )
}
