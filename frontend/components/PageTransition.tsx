/**
 * [INPUT]: 依赖 usePathname 路由能力
 * [OUTPUT]: 对外提供轻量级页面过渡组件（纯CSS）
 * [POS]: components/ 的全局过渡组件，被 app/layout.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

interface PageTransitionProps {
  children: React.ReactNode
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname()
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    setIsAnimating(true)
    const timer = setTimeout(() => setIsAnimating(false), 150)
    return () => clearTimeout(timer)
  }, [pathname])

  return (
    <div
      style={{
        opacity: isAnimating ? 0.8 : 1,
        transition: 'opacity 0.15s ease-out',
      }}
    >
      {children}
    </div>
  )
}
