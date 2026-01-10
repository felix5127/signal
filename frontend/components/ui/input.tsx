/**
 * [INPUT]: 依赖 @/lib/utils 的 cn 工具函数，依赖 CSS 变量的 --shadow-inset
 * [OUTPUT]: 对外提供 Input 组件，支持微拟物内凹效果的多态输入框
 * [POS]: ui/ 基础表单组件，被所有需要用户输入的表单场景消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // 基础样式 - 使用大圆角 + 内凹阴影
          [
            "flex h-10 w-full rounded-2xl border-0 bg-background px-5 py-2.5",
            "text-base shadow-[var(--shadow-inset)]",
            "transition-all duration-200",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:shadow-[var(--shadow-inset-lg)] focus-visible:scale-[1.01]",
            "hover:shadow-[var(--shadow-inset-md)]",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "md:text-sm",
          ],
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
