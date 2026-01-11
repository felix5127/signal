// Input: 子元素内容, 可选的 variant/size/hoverable
// Output: 标准化的卡片组件
// Position: 设计系统核心卡片组件，用于内容分组
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

// ============ 类型定义 ============
export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * 卡片样式变体
   * - default: 默认样式，带边框
   * - elevated: 浮起样式，带阴影
   * - outlined: 轮廓样式，强调边框
   * - flat: 扁平样式，无边框
   */
  variant?: 'default' | 'elevated' | 'outlined' | 'flat'

  /**
   * 卡片内边距
   */
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'

  /**
   * 是否可悬停交互
   */
  hoverable?: boolean

  /**
   * 是否可点击
   */
  clickable?: boolean
}

// ============ 样式配置 ============
const variantStyles = {
  default: `
    bg-white dark:bg-gray-900
    border border-gray-200 dark:border-gray-800
  `,

  elevated: `
    bg-white dark:bg-gray-900
    border border-gray-100 dark:border-gray-800
    shadow-md
  `,

  outlined: `
    bg-white dark:bg-gray-900
    border-2 border-gray-300 dark:border-gray-700
  `,

  flat: `
    bg-gray-50 dark:bg-gray-800/50
    border-0
  `,
}

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
  xl: 'p-8',
}

const hoverStyles = {
  hoverable: `
    transition-all duration-200
    hover:border-[#CDCBFF] dark:hover:border-[#6258FF]
    hover:shadow-lg hover:shadow-[#6258FF]/10
  `,

  clickable: `
    cursor-pointer
    transition-all duration-200
    hover:border-[#CDCBFF] dark:hover:border-[#6258FF]
    hover:shadow-lg hover:shadow-[#6258FF]/10
    hover:-translate-y-0.5
    active:scale-[0.97]
  `,
}

// ============ Card 组件 ============
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      padding = 'md',
      hoverable = false,
      clickable = false,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          // 基础样式
          'rounded-xl',
          'overflow-hidden',

          // 变体样式
          variantStyles[variant],

          // 内边距
          paddingStyles[padding],

          // 交互样式
          (hoverable || clickable) && hoverStyles[clickable ? 'clickable' : 'hoverable'],

          // 自定义类名
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

// ============ Card 子组件 ============

/**
 * Card 头部
 */
export const CardHeader = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5', className)}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

/**
 * Card 标题
 */
export const CardTitle = forwardRef<
  HTMLHeadingElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-lg font-semibold leading-none tracking-tight',
      'text-gray-900 dark:text-gray-100',
      className
    )}
    {...props}
  />
))
CardTitle.displayName = 'CardTitle'

/**
 * Card 描述
 */
export const CardDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      'text-sm',
      'text-gray-500 dark:text-gray-400',
      className
    )}
    {...props}
  />
))
CardDescription.displayName = 'CardDescription'

/**
 * Card 内容区
 */
export const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('pt-0', className)}
    {...props}
  />
))
CardContent.displayName = 'CardContent'

/**
 * Card 底部
 */
export const CardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center pt-4 mt-4 border-t border-gray-100 dark:border-gray-800',
      className
    )}
    {...props}
  />
))
CardFooter.displayName = 'CardFooter'

// ============ 导出 ============
export default Card
