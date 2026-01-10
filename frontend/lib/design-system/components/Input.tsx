// Input: name, value, onChange, 可选的 label/error/disabled
// Output: 标准化的输入框组件
// Position: 设计系统核心输入组件，用于所有表单输入
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { forwardRef, useState } from 'react'
import { cn } from '@/lib/utils'

// ============ 类型定义 ============
export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /**
   * 输入框标签
   */
  label?: string

  /**
   * 错误信息
   */
  error?: string

  /**
   * 帮助文本
   */
  helperText?: string

  /**
   * 输入框尺寸
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * 左侧图标
   */
  leftIcon?: React.ReactNode

  /**
   * 右侧图标
   */
  rightIcon?: React.ReactNode

  /**
   * 容器类名
   */
  containerClassName?: string
}

// ============ 尺寸样式 ============
const sizeStyles = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-base',
  lg: 'h-12 px-5 text-lg',
}

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
}

// ============ Input 组件 ============
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      size = 'md',
      leftIcon,
      rightIcon,
      disabled,
      required,
      containerClassName,
      className,
      type = 'text',
      ...props
    },
    ref
  ) => {
    const [focused, setFocused] = useState(false)

    const hasError = !!error
    const isDisabled = disabled

    return (
      <div className={cn('w-full', containerClassName)}>
        {/* 标签 */}
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        {/* 输入框容器 */}
        <div className="relative">
          {/* 左侧图标 */}
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
              <span className={cn(iconSizes[size])}>{leftIcon}</span>
            </div>
          )}

          {/* 输入框 */}
          <input
            ref={ref}
            type={type}
            disabled={isDisabled}
            onFocus={(e) => {
              setFocused(true)
              props.onFocus?.(e)
            }}
            onBlur={(e) => {
              setFocused(false)
              props.onBlur?.(e)
            }}
            className={cn(
              // 基础样式
              'w-full',
              'border',
              'rounded-lg',
              'bg-white dark:bg-gray-900',
              'text-gray-900 dark:text-gray-100',
              'placeholder:text-gray-400 dark:placeholder:text-gray-500',
              'transition-all duration-200',
              'focus:outline-none',

              // 尺寸
              sizeStyles[size],

              // 左右内边距（根据是否有图标）
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',

              // 边框颜色
              hasError
                ? 'border-red-300 dark:border-red-700 focus:border-red-500 focus:ring-red-500/20'
                : focused
                  ? 'border-[#CDCBFF] ring-4 ring-[#CDCBFF]/10'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500',

              // 禁用状态
              isDisabled && 'opacity-50 cursor-not-allowed bg-gray-50 dark:bg-gray-800',

              // 自定义类名
              className
            )}
            {...props}
          />

          {/* 右侧图标 */}
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
              <span className={cn(iconSizes[size])}>{rightIcon}</span>
            </div>
          )}
        </div>

        {/* 帮助文本 / 错误信息 */}
        {(helperText || hasError) && (
          <p
            className={cn(
              'mt-1.5 text-sm',
              hasError ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'
            )}
          >
            {hasError ? error : helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

// ============ 导出 ============
export default Input
