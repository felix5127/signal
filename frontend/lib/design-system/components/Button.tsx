// Input: onClick 回调, 子元素内容, 可选的 variant/size
// Output: 标准化的按钮组件
// Position: 设计系统核心按钮组件，用于所有交互操作
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

// ============ 类型定义 ============
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * 按钮样式变体
   * - primary: 主要操作按钮，使用品牌渐变
   * - secondary: 次要操作按钮，浅色背景
   * - outline: 轮廓按钮，带边框
   * - ghost: 幽灵按钮，只有 hover 效果
   * - link: 链接按钮样式
   */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'link'

  /**
   * 按钮尺寸
   * - xs: 超小按钮 (32px 高)
   * - sm: 小按钮 (36px 高)
   * - md: 中等按钮 (40px 高)
   * - lg: 大按钮 (48px 高)
   * - xl: 超大按钮 (56px 高)
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'

  /**
   * 是否全宽
   */
  fullWidth?: boolean

  /**
   * 加载状态
   */
  loading?: boolean

  /**
   * 左侧图标
   */
  leftIcon?: React.ReactNode

  /**
   * 右侧图标
   */
  rightIcon?: React.ReactNode
}

// ============ 样式配置 ============
const variantStyles = {
  primary: `
    bg-gradient-to-r from-[#6258FF] via-[#E06AB2] to-[#FB8569]
    text-white
    border-transparent
    hover:shadow-lg hover:shadow-brand-md
    active:scale-[0.97]
    disabled:opacity-50 disabled:cursor-not-allowed
  `,

  secondary: `
    bg-gray-50 dark:bg-gray-800
    text-gray-700 dark:text-gray-300
    border-gray-200 dark:border-gray-700
    hover:bg-gray-100 dark:hover:bg-gray-700
    active:bg-gray-200 dark:active:bg-gray-600
    disabled:opacity-50 disabled:cursor-not-allowed
  `,

  outline: `
    bg-transparent
    text-gray-700 dark:text-gray-300
    border-gray-300 dark:border-gray-600
    hover:bg-gray-50 dark:hover:bg-gray-800
    active:bg-gray-100 dark:active:bg-gray-700
    disabled:opacity-50 disabled:cursor-not-allowed
  `,

  ghost: `
    bg-transparent
    text-gray-700 dark:text-gray-300
    border-transparent
    hover:bg-gray-100 dark:hover:bg-gray-800
    active:bg-gray-200 dark:active:bg-gray-700
    disabled:opacity-50 disabled:cursor-not-allowed
  `,

  link: `
    bg-transparent
    text-[#6258FF] dark:text-[#CDCBFF]
    border-transparent
    underline-offset-4
    hover:underline
    disabled:opacity-50 disabled:cursor-not-allowed
    p-0
  `,
}

const sizeStyles = {
  xs: 'h-8 px-3 text-xs',
  sm: 'h-9 px-4 text-sm',
  md: 'h-10 px-5 text-base',
  lg: 'h-12 px-6 text-lg',
  xl: 'h-14 px-8 text-xl',
}

const iconSizes = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-7 h-7',
}

// ============ Loading Spinner 组件 ============
const LoadingSpinner = ({ size = 'md' }: { size?: keyof typeof iconSizes }) => (
  <svg
    className={cn('animate-spin', iconSizes[size])}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

// ============ Button 组件 ============
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          // 基础样式
          'inline-flex items-center justify-center gap-2',
          'font-medium',
          'border',
          'rounded-lg',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-[#CDCBFF] focus:ring-offset-2',
          'disabled:pointer-events-none',
          'whitespace-nowrap',

          // 变体样式
          variantStyles[variant],

          // 尺寸样式
          variant !== 'link' && sizeStyles[size],

          // 全宽
          fullWidth && 'w-full',

          // 自定义类名
          className
        )}
        {...props}
      >
        {/* 左侧图标 */}
        {leftIcon && !loading && (
          <span className={cn('flex-shrink-0', iconSizes[size])}>
            {leftIcon}
          </span>
        )}

        {/* Loading 状态 */}
        {loading && <LoadingSpinner size={size} />}

        {/* 子元素 */}
        {children}

        {/* 右侧图标 */}
        {rightIcon && !loading && (
          <span className={cn('flex-shrink-0', iconSizes[size])}>
            {rightIcon}
          </span>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

// ============ 导出 ============
export default Button
