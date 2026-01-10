/**
 * [INPUT]: 依赖 @/lib/utils 的 cn 工具函数，依赖 CSS 变量的渐变系统
 * [OUTPUT]: 对外提供 Badge 组件，支持微拟物渐变背景的标签组件
 * [POS]: ui/ 视觉反馈组件，被需要高亮标签的界面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/* ========================================
   Badge 样式配置 - 渐变 + 立体效果
   ======================================== */

const BADGE_STYLES = {
  default: {
    background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
    boxShadow: '0 2px 6px color-mix(in srgb, var(--primary) 30%, transparent), inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.08)',
    hoverBoxShadow: '0 3px 8px color-mix(in srgb, var(--primary) 40%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
  secondary: {
    background: 'linear-gradient(135deg, var(--secondary) 0%, color-mix(in srgb, var(--secondary) 90%, black) 50%, color-mix(in srgb, var(--secondary) 80%, black) 100%)',
    boxShadow: '0 2px 6px color-mix(in srgb, var(--secondary) 25%, transparent), inset 0 1px 0 rgba(255,255,255,0.1), inset 0 -1px 0 rgba(0,0,0,0.05)',
    hoverBoxShadow: '0 3px 8px color-mix(in srgb, var(--secondary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.08)',
  },
  destructive: {
    background: 'linear-gradient(135deg, var(--destructive) 0%, color-mix(in srgb, var(--destructive) 85%, black) 50%, color-mix(in srgb, var(--destructive) 70%, black) 100%)',
    boxShadow: '0 2px 6px color-mix(in srgb, var(--destructive) 30%, transparent), inset 0 1px 0 rgba(255,255,255,0.15), inset 0 -1px 0 rgba(0,0,0,0.08)',
    hoverBoxShadow: '0 3px 8px color-mix(in srgb, var(--destructive) 40%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
  outline: {
    background: 'transparent',
    boxShadow: '0 1px 2px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.05)',
    hoverBoxShadow: '0 2px 4px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.08)',
  },
}

const badgeVariants = cva(
  [
    "inline-flex items-center rounded-2xl border px-3 py-1 text-xs font-semibold",
    "transition-all duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "hover:scale-[1.02] active:scale-[0.97]",
  ],
  {
    variants: {
      variant: {
        default: "text-primary-foreground",
        secondary: "text-secondary-foreground",
        destructive: "text-destructive-foreground",
        outline: "text-foreground border border-input",
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
  const [isHovered, setIsHovered] = React.useState(false)

  const styleConfig = BADGE_STYLES[variant as keyof typeof BADGE_STYLES] || BADGE_STYLES.default
  const needsCustomStyle = variant !== 'outline'

  const combinedStyle = needsCustomStyle ? {
    background: styleConfig.background,
    boxShadow: isHovered ? styleConfig.hoverBoxShadow : styleConfig.boxShadow,
  } : variant === 'outline' ? {
    boxShadow: isHovered ? styleConfig.hoverBoxShadow : styleConfig.boxShadow,
  } : undefined

  return (
    <div
      className={cn(badgeVariants({ variant }), className)}
      style={combinedStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
