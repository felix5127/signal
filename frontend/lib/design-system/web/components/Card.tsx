'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-[var(--ds-border)] bg-[var(--ds-surface)] backdrop-blur',
        className
      )}
      {...props}
    />
  )
)
Card.displayName = 'Card'

export { Card }
