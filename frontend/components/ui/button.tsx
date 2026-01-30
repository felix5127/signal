/**
 * Button - Mercury 风格按钮组件
 * 特点: 大圆角 (2rem)、简洁样式、微妙交互
 */
'use client'

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  [
    // 基础样式
    "inline-flex items-center justify-center gap-2",
    "whitespace-nowrap font-medium",
    "rounded-[var(--radius-xl)]",
    "transition-all duration-200",
    // 焦点样式
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2",
    // 禁用状态
    "disabled:pointer-events-none disabled:opacity-50",
    // SVG 图标
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
    // 微交互
    "active:scale-[0.98]",
  ].join(" "),
  {
    variants: {
      variant: {
        // 主按钮 - 墨绿实心
        default: [
          "bg-[var(--color-primary)] text-white",
          "hover:bg-[var(--color-primary-dark)]",
          "hover:shadow-[var(--shadow-brand-sm)]",
        ].join(" "),
        // 主按钮别名
        primary: [
          "bg-[var(--color-primary)] text-white",
          "hover:bg-[var(--color-primary-dark)]",
          "hover:shadow-[var(--shadow-brand-sm)]",
        ].join(" "),
        // 次按钮 - 浅色背景
        secondary: [
          "bg-[var(--bg-secondary)] text-[var(--text-primary)]",
          "border border-[var(--border-default)]",
          "hover:bg-[var(--bg-input)] hover:border-[var(--border-strong)]",
        ].join(" "),
        // 危险按钮
        destructive: [
          "bg-[var(--color-error)] text-white",
          "hover:bg-red-600",
          "hover:shadow-[0_2px_8px_rgba(239,68,68,0.2)]",
        ].join(" "),
        // 边框按钮
        outline: [
          "bg-transparent text-[var(--text-primary)]",
          "border border-[var(--border-strong)]",
          "hover:bg-[var(--bg-secondary)]",
        ].join(" "),
        // 幽灵按钮
        ghost: [
          "bg-transparent text-[var(--text-primary)]",
          "hover:bg-[var(--bg-secondary)]",
        ].join(" "),
        // 链接按钮
        link: [
          "bg-transparent text-[var(--color-primary)]",
          "underline-offset-4 hover:underline",
          "active:scale-100",
        ].join(" "),
        // 强调按钮 - 琥珀金
        accent: [
          "bg-[var(--color-accent)] text-white",
          "hover:brightness-110",
          "hover:shadow-[0_2px_8px_rgba(138,117,60,0.2)]",
        ].join(" "),
      },
      size: {
        sm: "h-8 px-4 text-[var(--text-body-sm)] rounded-[var(--radius-lg)]",
        default: "h-10 px-5 py-2 text-[var(--text-body-sm)]",
        md: "h-11 px-6 py-2.5 text-[var(--text-body)]",
        lg: "h-12 px-8 text-[var(--text-body)]",
        xl: "h-14 px-10 text-[var(--text-body-lg)]",
        icon: "h-10 w-10 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
