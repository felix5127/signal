/**
 * [INPUT]: todayFunnel
 * [OUTPUT]: 采集漏斗可视化组件
 * [POS]: dashboard/，今日数据流转一目了然
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Filter, Copy, Bot, Save, ArrowRight } from 'lucide-react'
import type { TodayFunnel } from './hooks/useDashboardData'

interface CollectionFunnelProps {
  todayFunnel: TodayFunnel | null
}

export function CollectionFunnel({ todayFunnel }: CollectionFunnelProps) {
  if (!todayFunnel) {
    return (
      <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-4">
        <div className="h-16 flex items-center justify-center text-[var(--ds-muted)]">
          加载中...
        </div>
      </div>
    )
  }

  const steps = [
    { label: '抓取', value: todayFunnel.fetched, icon: null, color: 'bg-gray-500' },
    { label: '规则过滤', value: todayFunnel.rule_filtered, icon: Filter, color: 'bg-amber-500' },
    { label: '去重', value: todayFunnel.dedup_filtered, icon: Copy, color: 'bg-blue-500' },
    { label: 'LLM过滤', value: todayFunnel.llm_filtered, icon: Bot, color: 'bg-purple-500' },
    { label: '保存', value: todayFunnel.saved, icon: Save, color: 'bg-green-500' },
  ]

  // 计算转化率
  const getConversionRate = (current: number, previous: number): string => {
    if (previous === 0) return '-'
    const rate = (current / previous) * 100
    return `${rate.toFixed(0)}%`
  }

  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-sm font-medium text-[var(--ds-fg)]">采集漏斗概览</div>
        <span className="text-xs text-[var(--ds-muted)]">(今日)</span>
      </div>

      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isLast = index === steps.length - 1

          return (
            <div key={step.label} className="flex items-center">
              {/* 步骤卡片 */}
              <div className="flex flex-col items-center">
                <div className={`
                  w-14 h-14 rounded-xl flex flex-col items-center justify-center
                  ${step.color} bg-opacity-10 dark:bg-opacity-20
                `}>
                  {Icon && (
                    <Icon className={`w-4 h-4 mb-0.5 ${step.color.replace('bg-', 'text-')}`} />
                  )}
                  <span className={`text-lg font-bold ${step.color.replace('bg-', 'text-')}`}>
                    {step.value.toLocaleString()}
                  </span>
                </div>
                <span className="text-xs text-[var(--ds-muted)] mt-1.5">{step.label}</span>
              </div>

              {/* 箭头和转化率 */}
              {!isLast && (
                <div className="flex flex-col items-center mx-2">
                  <ArrowRight className="w-4 h-4 text-[var(--ds-muted)]" />
                  <span className="text-[10px] text-[var(--ds-muted)]">
                    {getConversionRate(steps[index + 1].value, step.value)}
                  </span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* 整体转化率 */}
      <div className="mt-3 pt-3 border-t border-[var(--ds-border)] text-center">
        <span className="text-xs text-[var(--ds-muted)]">
          整体转化率:
          <span className="ml-1 font-medium text-green-600 dark:text-green-400">
            {todayFunnel.fetched > 0
              ? `${((todayFunnel.saved / todayFunnel.fetched) * 100).toFixed(1)}%`
              : '-'}
          </span>
        </span>
      </div>
    </div>
  )
}
