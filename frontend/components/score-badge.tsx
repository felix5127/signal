// Input: score (number), is_featured (boolean)
// Output: 评分徽章组件
// Position: 展示资源评分的UI组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { cn } from '@/lib/utils'

interface ScoreBadgeProps {
  score: number // 1-5 或 0-100 的评分
  isFeatured?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ScoreBadge({
  score,
  isFeatured = false,
  size = 'md',
  className
}: ScoreBadgeProps) {
  // 如果是 1-5 评分，转换为百分制
  const normalizedScore = score <= 5 ? score * 20 : score

  // 根据分数确定颜色（Phase 1.5 更新：更细致的梯度）
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    if (score >= 85) return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
    if (score >= 75) return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    if (score >= 60) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }

  // 获取评分标签（Phase 1.5 新增）
  const getScoreLabel = (score: number) => {
    if (score >= 90) return '推荐'
    if (score >= 85) return '值得读'
    if (score >= 75) return '基础'
    return ''
  }

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5'
  }

  const scoreLabel = getScoreLabel(normalizedScore)

  return (
    <div className={cn('inline-flex items-center gap-1.5', className)}>
      <span
        className={cn(
          'font-semibold rounded-md shadow-sm',
          getScoreColor(normalizedScore),
          sizeClasses[size]
        )}
      >
        {scoreLabel ? `${scoreLabel} ${normalizedScore}` : normalizedScore}
      </span>
      {isFeatured && (
        <span
          className={cn(
            'bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-md shadow-sm',
            sizeClasses[size]
          )}
        >
          精选
        </span>
      )}
    </div>
  )
}
