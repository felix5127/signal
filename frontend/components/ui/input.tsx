/**
 * Input - Mercury 风格输入框组件
 * 特点: 大圆角、简洁边框、清晰聚焦状态
 */
import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // 基础样式
          "flex h-11 w-full",
          "rounded-[var(--radius-lg)]",
          "bg-[var(--bg-card)]",
          "border border-[var(--border-default)]",
          "px-4 py-2",
          "text-[var(--text-primary)]",
          "text-base md:text-sm",
          // 占位符
          "placeholder:text-[var(--text-muted)]",
          // 过渡
          "transition-all duration-200",
          // 悬浮
          "hover:border-[var(--border-strong)]",
          // 聚焦
          "focus:outline-none",
          "focus:border-[var(--color-primary)]",
          "focus:ring-2",
          "focus:ring-[var(--color-primary)]/20",
          // 禁用
          "disabled:cursor-not-allowed",
          "disabled:opacity-50",
          "disabled:bg-[var(--bg-secondary)]",
          // 文件输入特殊样式
          "file:border-0",
          "file:bg-transparent",
          "file:text-sm",
          "file:font-medium",
          "file:text-[var(--text-primary)]",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
