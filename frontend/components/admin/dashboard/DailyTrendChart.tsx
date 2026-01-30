/**
 * [INPUT]: daily stats array
 * [OUTPUT]: 近 7 日趋势图表组件
 * [POS]: dashboard/，采集趋势可视化
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import type { DailyStats } from './hooks/useDashboardData'

interface DailyTrendChartProps {
  data: DailyStats | null
}

export function DailyTrendChart({ data }: DailyTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
        <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">近 7 日趋势</h3>
        <div className="h-40 flex items-center justify-center text-[var(--ds-muted)]">暂无数据</div>
      </div>
    )
  }

  const maxTotal = Math.max(...data.map((d) => d.total), 1)

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-6">
      <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
        近 7 日趋势
      </h3>
      <div className="flex items-end gap-2 h-40">
        {data.map((day) => {
          const totalHeight = (day.total / maxTotal) * 100
          const publishedHeight = day.total > 0 ? (day.published / day.total) * totalHeight : 0

          return (
            <div
              key={day.date}
              className="flex-1 flex flex-col items-center gap-1"
            >
              {/* 柱状图 */}
              <div className="w-full flex flex-col items-center justify-end h-32 relative">
                {/* 总数柱 */}
                <div
                  className="w-full max-w-8 bg-indigo-200 dark:bg-indigo-900/50 rounded-t transition-all duration-500"
                  style={{ height: `${totalHeight}%` }}
                >
                  {/* 已发布部分（覆盖在底部） */}
                  <div
                    className="absolute bottom-0 left-0 right-0 mx-auto w-full max-w-8 bg-indigo-500 rounded-t transition-all duration-500"
                    style={{ height: `${publishedHeight}%` }}
                  />
                </div>
              </div>
              {/* 日期标签 */}
              <div className="text-xs text-[var(--ds-muted)] whitespace-nowrap">
                {new Date(day.date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
              </div>
            </div>
          )
        })}
      </div>
      {/* 图例 */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-[var(--ds-border)]">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-200 dark:bg-indigo-900/50" />
          <span className="text-xs text-[var(--ds-muted)]">采集总数</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-indigo-500" />
          <span className="text-xs text-[var(--ds-muted)]">已发布</span>
        </div>
      </div>
    </div>
  )
}
