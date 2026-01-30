/**
 * [INPUT]: 依赖 framer-motion MotionConfig, sonner Toaster, Navbar, Footer, usePathname
 * [OUTPUT]: 对外提供客户端布局包装器，包含所有客户端组件
 * [POS]: components/ 的布局组件，被 app/layout.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { MotionConfig } from 'framer-motion'
import { Toaster } from 'sonner'
import { usePathname } from 'next/navigation'
import Navbar from '@/components/navbar'
import { Footer } from '@/components/Footer'

interface ClientLayoutProps {
  children: React.ReactNode
}

export function ClientLayout({ children }: ClientLayoutProps) {
  const pathname = usePathname()
  const isAdminRoute = pathname?.startsWith('/admin')
  const isResearchWorkspace = pathname?.startsWith('/research/workspace')

  // 研究工作台页面：隐藏全局 Navbar 和 Footer（使用自己的布局）
  const hideGlobalNav = isAdminRoute || isResearchWorkspace
  const hideFooter = isAdminRoute || isResearchWorkspace

  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.2 }}>
      {!hideGlobalNav && <Navbar />}
      {children}
      {!hideFooter && <Footer />}
      <Toaster position="top-right" richColors />
    </MotionConfig>
  )
}
