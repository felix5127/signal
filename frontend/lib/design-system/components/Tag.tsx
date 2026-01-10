// Input: 标签文本, 可选的 onRemove 回调
// Output: 可移除的标签组件
// Position: 设计系统标签组件，用于关键词/分类展示
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { forwardRef, useState, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

// ============ 类型定义 ============
export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  /**
   * 标签内容
   */
  children: React.ReactNode

  /**
   * 是否可移除
   */
  removable?: boolean

  /**
   * 移除回调
   */
  onRemove?: () => void

  /**
   * 标签颜色
   */
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'

  /**
   * 尺寸
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * 是否为链接
   */
  href?: string
}

// ============ 样式配置 ============
const sizeStyles = {
  sm: 'h-6 px-2 text-xs',
  md: 'h-7 px-2.5 text-sm',
  lg: 'h-8 px-3 text-base',
}

const colorStyles = {
  default: 'bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300',
  primary: 'bg-[#CDCBFF]/20 hover:bg-[#CDCBFF]/30 text-[#6258FF] dark:text-[#BDBBFF]',
  success: 'bg-[#CDEED3]/30 hover:bg-[#CDEED3]/50 text-[#1B9A7A]',
  warning: 'bg-amber-100 hover:bg-amber-200 text-amber-700',
  danger: 'bg-red-100 hover:bg-red-200 text-red-700',
  info: 'bg-blue-100 hover:bg-blue-200 text-blue-700',
}

// ============ 关闭图标 ============
const CloseIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </svg>
)

// ============ Tag 组件 ============
export const Tag = forwardRef<HTMLSpanElement, TagProps>(
  (
    {
      children,
      removable = false,
      onRemove,
      color = 'default',
      size = 'md',
      href,
      className,
      ...props
    },
    ref
  ) => {
    const [isRemoving, setIsRemoving] = useState(false)

    const handleRemove = (e: React.MouseEvent) => {
      e.stopPropagation()
      setIsRemoving(true)
      // 等待动画完成
      setTimeout(() => {
        onRemove?.()
      }, 150)
    }

    const content = (
      <>
        <span className="truncate max-w-[150px]">{children}</span>

        {/* 移除按钮 */}
        {removable && (
          <button
            type="button"
            onClick={handleRemove}
            className={cn(
              'flex-shrink-0 ml-1 rounded-full p-0.5',
              'transition-colors duration-150',
              'hover:bg-black/10 dark:hover:bg-white/10',
              'focus:outline-none focus:ring-1 focus:ring-current',
              isRemoving && 'scale-0'
            )}
          >
            <CloseIcon className="w-3 h-3" />
          </button>
        )}
      </>
    )

    const sharedClassName = cn(
      // 基础样式
      'inline-flex items-center gap-1',
      'font-medium',
      'rounded-full',
      'transition-all duration-150',
      'cursor-default',

      // 尺寸
      sizeStyles[size],

      // 颜色
      colorStyles[color],

      // 移除动画
      isRemoving && 'opacity-0 scale-95',

      // 自定义类名
      className
    )

    // 链接模式
    if (href) {
      return (
        <a
          ref={ref as any}
          href={href}
          className={cn(sharedClassName, 'hover:underline')}
          {...(props as any)}
        >
          {content}
        </a>
      )
    }

    // 默认模式
    return (
      <span ref={ref} className={sharedClassName} {...props}>
        {content}
      </span>
    )
  }
)

Tag.displayName = 'Tag'

// ============ 标签组组件 ============
export interface TagGroupProps {
  children: React.ReactNode
  className?: string
  /**
   * 标签之间的间距
   */
  gap?: 'xs' | 'sm' | 'md' | 'lg'
}

const gapStyles = {
  xs: 'gap-1',
  sm: 'gap-1.5',
  md: 'gap-2',
  lg: 'gap-2.5',
}

export const TagGroup = ({ children, className, gap = 'sm' }: TagGroupProps) => {
  return (
    <div className={cn('flex flex-wrap', gapStyles[gap], className)}>
      {children}
    </div>
  )
}

// ============ 导出 ============
export default Tag
