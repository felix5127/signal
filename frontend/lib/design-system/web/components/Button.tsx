'use client'

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ds-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ds-bg)] disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-[var(--ds-accent)] text-white hover:brightness-95 active:brightness-90',
        secondary: 'border border-[var(--ds-border)] bg-[var(--ds-surface)] text-[var(--ds-fg)] hover:bg-[var(--ds-surface-2)]',
        outline: 'border border-[var(--ds-border)] bg-transparent text-[var(--ds-fg)] hover:bg-[var(--ds-surface-2)]',
        ghost: 'bg-transparent text-[var(--ds-fg)] hover:bg-[var(--ds-surface-2)]',
        danger: 'bg-[var(--ds-danger)] text-white hover:brightness-95 active:brightness-90',
      },
      size: {
        sm: 'h-9 px-3 text-xs',
        md: 'h-10 px-4',
        lg: 'h-11 px-5 text-base',
        icon: 'h-10 w-10 p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  href?: string
}

const Button = React.forwardRef<HTMLButtonElement & HTMLAnchorElement, ButtonProps>(
  ({ className, variant, size, asChild, href, disabled, type, ...props }, ref) => {
    const classes = cn(buttonVariants({ variant, size }), className)

    if (asChild && href) {
      // Extract only anchor-compatible props
      const {
        onToggle,
        formAction,
        formEncType,
        formMethod,
        formNoValidate,
        formTarget,
        name,
        value,
        ...anchorProps
      } = props as any

      return (
        <a
          href={href}
          className={classes}
          ref={ref as React.Ref<HTMLAnchorElement>}
          {...anchorProps}
        />
      )
    }

    return (
      <button
        className={classes}
        ref={ref as React.Ref<HTMLButtonElement>}
        disabled={disabled}
        type={type}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
