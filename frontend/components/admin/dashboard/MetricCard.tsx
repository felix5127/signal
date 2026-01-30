/**
 * [INPUT]: icon, label, value, subValue, color
 * [OUTPUT]: 通用指标卡片组件
 * [POS]: dashboard/，可复用的指标展示卡片
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

interface MetricCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  subValue?: string
  color?: 'indigo' | 'green' | 'amber' | 'blue' | 'purple'
}

const colorMap = {
  indigo: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
  green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
  amber: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
  blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
}

export function MetricCard({
  icon: Icon,
  label,
  value,
  subValue,
  color = 'indigo',
}: MetricCardProps) {
  return (
    <div className="bg-[var(--ds-bg)] rounded-xl border border-[var(--ds-border)] p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <span className="text-sm text-[var(--ds-muted)]">{label}</span>
      </div>
      <div className="text-2xl font-bold text-[var(--ds-fg)]">{value}</div>
      {subValue && (
        <div className="text-sm text-[var(--ds-muted)] mt-1">{subValue}</div>
      )}
    </div>
  )
}
