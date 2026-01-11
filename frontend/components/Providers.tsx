/**
 * [INPUT]: 依赖 framer-motion 的 MotionConfig
 * [OUTPUT]: 对外提供客户端 Provider 包装器，包含动画配置
 * [POS]: components/ 的 Provider 组件，被 app/layout.tsx 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { MotionConfig } from 'framer-motion'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.2 }}>
      {children}
    </MotionConfig>
  )
}
