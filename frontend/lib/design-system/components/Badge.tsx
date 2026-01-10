// Input: 子元素内容, 可选的 variant/size/color
// Output: 标准化徽章/标签组件
// Position: 设计系统徽章组件，用于状态标识和分类
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

// ============ 类型定义 ============
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /**
   * 徽章样式变体
   * - solid: 实心背景
   * - outline: 轮廓样式
   * - soft: 柔和背景
   */
  variant?: 'solid' | 'outline' | 'soft'

  /**
   * 预设颜色
   * - default: 灰色
   * - primary: 品牌紫色
   * - success: 绿色
   * - warning: 黄色
   * - danger: 红色
   * - info: 蓝色
   */
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'

  /**
   * 尺寸
   */
  size?: 'xs' | 'sm' | 'md' | 'lg'

  /**
   * 是否为圆点
   */
  dot?: boolean
}

// ============ 样式配置 ============
const sizeStyles = {
  xs: 'px-1.5 py-0.5 text-xs',
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}

const dotSizes = {
  xs: 'w-1.5 h-1.5',
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
}

const colorStyles = {
  default: {
    solid: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    outline: 'bg-transparent border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300',
    soft: 'bg-gray-50 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400',
  },
  primary: {
    solid: 'bg-[#CDCBFF] text-[#544A2E]',
    outline: 'bg-transparent border border-[#CDCBFF] text-[#6258FF] dark:text-[#CDCBFF]',
    soft: 'bg-[#CDCBFF]/20 text-[#6258FF] dark:text-[#BDBBFF]',
  },
  success: {
    solid: 'bg-[#CDEED3] text-[#064C3F]',
    outline: 'bg-transparent border border-[#CDEED3] text-[#138069]',
    soft: 'bg-[#CDEED3]/30 text-[#1B9A7A]',
  },
  warning: {
    solid: 'bg-amber-100 text-amber-800',
    outline: 'bg-transparent border border-amber-300 text-amber-700',
    soft: 'bg-amber-50 text-amber-600',
  },
  danger: {
    solid: 'bg-red-100 text-red-700',
    outline: 'bg-transparent border border-red-300 text-red-600',
    soft: 'bg-red-50 text-red-600',
  },
  info: {
    solid: 'bg-blue-100 text-blue-700',
    outline: 'bg-transparent border border-blue-300 text-blue-600',
    soft: 'bg-blue-50 text-blue-600',
  },
}

// ============ Badge 组件 ============
export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      variant = 'soft',
      color = 'default',
      size = 'sm',
      dot = false,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={cn(
          // 基础样式
          'inline-flex items-center justify-center',
          'font-medium',
          'rounded-md',
          'transition-colors duration-150',

          // 尺寸
          sizeStyles[size],

          // 颜色和变体
          colorStyles[color][variant],

          // 自定义类名
          className
        )}
        {...props}
      >
        {/* 圆点 */}
        {dot && (
          <span
            className={cn(
              'rounded-full bg-current mr-1.5',
              dotSizes[size]
            )}
          />
        )}

        {/* 子元素 */}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

// ============ 辅助组件: 状态徽章 ============
export const StatusBadge = forwardRef<
  HTMLSpanElement,
  Omit<BadgeProps, 'color'> & { status: 'online' | 'offline' | 'busy' | 'away' }
>(({ status, ...props }, ref) => {
  const statusColors: Record<typeof status, BadgeProps['color']> = {
    online: 'success',
    offline: 'default',
    busy: 'danger',
    away: 'warning',
  }

  const statusLabels: Record<typeof status, string> = {
    online: '在线',
    offline: '离线',
    busy: '忙碌',
    away: '离开',
  }

  return (
    <Badge ref={ref} color={statusColors[status]} {...props}>
      {props.children || statusLabels[status]}
    </Badge>
  )
})

StatusBadge.displayName = 'StatusBadge'

// ============ 辅助组件: 评分徽章 ============
export const ScoreBadge = forwardRef<
  HTMLSpanElement,
  {
    score: number
    maxScore?: number
    size?: 'xs' | 'sm' | 'md' | 'lg'
    showLabel?: boolean
  } & Omit<BadgeProps, 'color' | 'children'>
>(({ score, maxScore = 5, size = 'sm', showLabel = false, className, ...props }, ref) => {
  // 计算分数百分比
  const percentage = Math.min((score / maxScore) * 100, 100)

  // 根据分数确定颜色
  let color: BadgeProps['color'] = 'default'
  if (percentage >= 80) color = 'success'
  else if (percentage >= 60) color = 'primary'
  else if (percentage >= 40) color = 'warning'
  else color = 'danger'

  return (
    <Badge
      ref={ref}
      color={color}
      variant="soft"
      size={size}
      className={cn('gap-1', className)}
      {...props}
    >
      <span className="font-semibold">{score.toFixed(1)}</span>
      {showLabel && (
        <>
          <span className="text-muted">/</span>
          <span className="text-muted">{maxScore}</span>
        </>
      )}
    </Badge>
  )
})

ScoreBadge.displayName = 'ScoreBadge'

// ============ 导出 ============
export default Badge
