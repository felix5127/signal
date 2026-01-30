/**
 * Card - Mercury 风格卡片组件
 * 特点: 大圆角 (2rem)、极淡阴影、简洁边框
 */
'use client'

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const cardVariants = cva(
  [
    "rounded-[var(--radius-xl)]",
    "bg-[var(--bg-card)]",
    "border border-[var(--border-default)]",
    "transition-all duration-200",
  ].join(" "),
  {
    variants: {
      variant: {
        // 默认卡片
        default: "",
        // 可交互卡片 - 带悬浮效果
        interactive: [
          "cursor-pointer",
          "hover:shadow-[var(--shadow-card-hover)]",
          "hover:-translate-y-0.5",
          "hover:border-[var(--border-strong)]",
        ].join(" "),
        // 凸起卡片 - 带阴影
        raised: [
          "shadow-[var(--shadow-md)]",
          "hover:shadow-[var(--shadow-lg)]",
          "hover:-translate-y-0.5",
        ].join(" "),
        // 边框卡片
        outline: [
          "border-[var(--border-strong)]",
          "bg-transparent",
        ].join(" "),
        // 玻璃卡片
        glass: [
          "bg-[var(--glass-bg-light)]",
          "backdrop-blur-[var(--glass-blur-light)]",
          "border-[var(--border-light)]",
        ].join(" "),
        // 强调卡片 - 带品牌色边框
        elevated: [
          "shadow-[var(--shadow-md)]",
          "hover:shadow-[var(--shadow-lg)]",
        ].join(" "),
        // 内嵌卡片 - 用于表单区域
        inset: [
          "bg-[var(--bg-secondary)]",
          "border-transparent",
        ].join(" "),
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, className }))}
      {...props}
    />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight text-[var(--text-primary)]",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-[var(--text-secondary)]", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  cardVariants,
}
