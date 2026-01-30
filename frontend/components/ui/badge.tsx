/**
 * Badge - Mercury 风格标签组件
 * 特点: 简洁、圆润、多种语义变体
 */
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  [
    "inline-flex items-center",
    "rounded-full",
    "px-3 py-1",
    "text-[var(--text-xs)] font-medium",
    "transition-colors duration-200",
  ].join(" "),
  {
    variants: {
      variant: {
        // 默认 - 墨绿实心
        default: [
          "bg-[var(--color-primary)]",
          "text-white",
        ].join(" "),
        // 次要 - 浅色背景
        secondary: [
          "bg-[var(--bg-secondary)]",
          "text-[var(--text-primary)]",
          "border border-[var(--border-default)]",
        ].join(" "),
        // 边框
        outline: [
          "bg-transparent",
          "text-[var(--text-primary)]",
          "border border-[var(--border-strong)]",
        ].join(" "),
        // 危险
        destructive: [
          "bg-[var(--color-error)]",
          "text-white",
        ].join(" "),
        // 成功
        success: [
          "bg-[var(--color-success)]",
          "text-white",
        ].join(" "),
        // 警告
        warning: [
          "bg-[var(--color-warning)]",
          "text-white",
        ].join(" "),
        // 强调 - 琥珀金
        accent: [
          "bg-[var(--color-accent)]",
          "text-white",
        ].join(" "),
        // 柔和主色
        "primary-soft": [
          "bg-[var(--color-primary-light)]",
          "text-[var(--color-primary)]",
        ].join(" "),
        // 柔和次要
        "secondary-soft": [
          "bg-[var(--bg-input)]",
          "text-[var(--text-secondary)]",
        ].join(" "),
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
