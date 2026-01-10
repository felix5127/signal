/**
 * [INPUT]: 依赖 React useState/useEffect、framer-motion、lucide-react
 * [OUTPUT]: 返回顶部浮动按钮组件
 * [POS]: components/ 的交互组件，被长列表页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ChevronUp } from 'lucide-react'

export function BackToTop() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const toggle = () => setVisible(window.scrollY > 400)
    window.addEventListener('scroll', toggle)
    return () => window.removeEventListener('scroll', toggle)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: visible ? 1 : 0,
        scale: visible ? 1 : 0.8,
        pointerEvents: visible ? 'auto' : 'none',
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      onClick={scrollToTop}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      className="fixed bottom-8 right-8 w-12 h-12 text-white rounded-full z-50 flex items-center justify-center transition-all duration-200"
      style={{
        background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 85%, black) 50%, color-mix(in srgb, var(--primary) 70%, black) 100%)',
        boxShadow: '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
      }}
      onHoverStart={(e) => {
        const target = e.currentTarget as HTMLElement | null
        if (target) {
          target.style.boxShadow = '0 6px 20px color-mix(in srgb, var(--primary) 45%, transparent), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.15)'
        }
      }}
      onHoverEnd={(e) => {
        const target = e.currentTarget as HTMLElement | null
        if (target) {
          target.style.boxShadow = '0 4px 12px color-mix(in srgb, var(--primary) 35%, transparent), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)'
        }
      }}
      aria-label="返回顶部"
    >
      <ChevronUp className="w-6 h-6" />
    </motion.button>
  )
}
