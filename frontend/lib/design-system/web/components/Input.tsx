'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  startAdornment?: React.ReactNode
  endAdornment?: React.ReactNode
  state?: 'default' | 'error'
  variant?: 'default' | 'glass'
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, startAdornment, endAdornment, state = 'default', variant = 'default', ...props }, ref) => {
    return (
      <div className="relative w-full">
        {startAdornment && (
          <div className={cn(
            'absolute top-1/2 -translate-y-1/2',
            variant === 'glass' ? 'left-4 text-slate-500' : 'left-3 text-[var(--ds-muted)]'
          )}>
            {startAdornment}
          </div>
        )}
        <input
          type={type}
          className={cn(
            // 基础样式
            'flex w-full border transition-all',
            // 默认样式
            variant === 'default' && [
              'h-10 rounded-xl border-[var(--ds-border)] bg-[var(--ds-surface)] px-3 py-2 text-sm text-[var(--ds-fg)] placeholder:text-[var(--ds-subtle)]',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ds-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ds-bg)]',
            ],
            // 毛玻璃样式 - True VisionOS Optical Glass (增强边框)
            variant === 'glass' && [
              'h-14 rounded-2xl bg-white/70 backdrop-blur-2xl backdrop-saturate-150 border border-white/40 ring-1 ring-black/5 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.7)] shadow-2xl shadow-black/5 px-5 py-4 text-base text-slate-900 placeholder:text-slate-500',
              'focus:outline-none focus:bg-white/80 focus:shadow-2xl focus:shadow-black/8',
            ],
            'disabled:cursor-not-allowed disabled:opacity-50',
            state === 'error' && 'border-[var(--ds-danger)] focus-visible:ring-[var(--ds-danger)]',
            variant === 'glass' && startAdornment && 'pl-12',
            variant === 'glass' && endAdornment && 'pr-12',
            variant === 'default' && startAdornment && 'pl-10',
            variant === 'default' && endAdornment && 'pr-10',
            className
          )}
          ref={ref}
          {...props}
        />
        {endAdornment && (
          <div className={cn(
            'absolute top-1/2 -translate-y-1/2',
            variant === 'glass' ? 'right-4 text-slate-400 hover:text-slate-600' : 'right-3 text-[var(--ds-muted)]'
          )}>
            {endAdornment}
          </div>
        )}
      </div>
    )
  }
)
Input.displayName = 'Input'

export { Input }
