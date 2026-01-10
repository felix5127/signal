/**
 * [INPUT]: 依赖 framer-motion MotionConfig, sonner Toaster, Navbar, Footer
 * [OUTPUT]: 对外提供客户端布局包装器，包含所有客户端组件
 * [POS]: components/ 的布局组件，被 app/layout.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { MotionConfig } from 'framer-motion'
import { Toaster } from 'sonner'
import Navbar from '@/components/navbar'
import { Footer } from '@/components/Footer'

interface ClientLayoutProps {
  children: React.ReactNode
}

export function ClientLayout({ children }: ClientLayoutProps) {
  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.2 }}>
      <Navbar />
      {children}
      <Footer />
      <Toaster position="top-right" richColors />
    </MotionConfig>
  )
}
