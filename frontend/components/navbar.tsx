/**
 * [INPUT]: 依赖 Next.js 的 Link/usePathname 路由能力，依赖 Lucide React 的图标组件，依赖 Framer Motion 的 Spring 物理引擎
 * [OUTPUT]: 对外提供全局导航栏组件，实现页面间路由导航、Logo 展示、桌面/移动端响应式菜单、Apple 级 Spring 交互动画
 * [POS]: components/ 的全局布局组件，被 app/layout.tsx 消费，在所有页面顶部固定显示
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Newspaper, Menu, X, FileText, Mic, Twitter, Video, Search } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

// 导航项配置 - 6项（信号源移至 /admin，需密码访问）
const NAV_ITEMS = [
  { id: 'articles', label: '文章', href: '/articles', icon: FileText },
  { id: 'podcasts', label: '播客', href: '/podcasts', icon: Mic },
  { id: 'tweets', label: '推文', href: '/tweets', icon: Twitter },
  { id: 'videos', label: '视频', href: '/videos', icon: Video },
  { id: 'featured', label: '精选', href: '/featured', icon: Newspaper },
  { id: 'research', label: '研究', href: '/research', icon: Search },
] as const

export default function Navbar() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(true) // 默认禁用动画
  const [isMounted, setIsMounted] = useState(false) // 客户端挂载检测

  useEffect(() => {
    setIsMounted(true) // 标记已挂载到客户端
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  // 在服务端渲染或未挂载时禁用动画
  const shouldAnimate = isMounted && !prefersReducedMotion

  return (
    <motion.nav
      key={pathname}
      initial={!shouldAnimate ? false : { y: -100 }}
      animate={!shouldAnimate ? false : { y: 0 }}
      transition={!shouldAnimate ? { duration: 0 } : { type: 'spring', stiffness: 300, damping: 30 }}
      className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-lg"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-24 items-center">
          {/* Logo - 左侧 */}
          <motion.div
            className="flex-shrink-0"
            whileHover={shouldAnimate ? { scale: 1.02 } : undefined}
            whileTap={shouldAnimate ? { scale: 0.97 } : undefined}
            transition={shouldAnimate ? { type: 'spring', stiffness: 400, damping: 25 } : { duration: 0 }}
          >
            <Link href="/" className="flex items-center space-x-3 group">
              <motion.div
                className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center"
                whileHover={shouldAnimate ? { rotate: 5 } : undefined}
                transition={shouldAnimate ? { type: 'spring', stiffness: 300, damping: 20 } : { duration: 0 }}
              >
                <span className="text-white font-bold">SH</span>
              </motion.div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent group-hover:opacity-80 transition-opacity">
                Signal Hunter
              </span>
            </Link>
          </motion.div>

          {/* 桌面端导航 - 居中 */}
          <div className="hidden md:flex flex-1 items-center justify-center md:space-x-3">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || pathname?.startsWith(item.href)

              return (
                <Link key={item.id} href={item.href}>
                  <motion.div
                    whileHover={shouldAnimate ? { y: -2 } : undefined}
                    whileTap={shouldAnimate ? { scale: 0.97 } : undefined}
                    transition={shouldAnimate ? { type: 'spring', stiffness: 400, damping: 30 } : { duration: 0 }}
                    className={cn(
                      'flex items-center space-x-3 px-6 py-4 rounded-xl font-semibold transition-all duration-200 cursor-pointer text-[22px]',
                      isActive
                        ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/30'
                        : 'text-gray-700 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    )}
                  >
                    <Icon className="w-6 h-6" />
                    <span>{item.label}</span>
                  </motion.div>
                </Link>
              )
            })}
          </div>

          {/* 移动端菜单按钮 - 右侧 */}
          <div className="flex-shrink-0 md:hidden">
            <motion.button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              whileTap={shouldAnimate ? { scale: 0.97 } : undefined}
              transition={shouldAnimate ? { type: 'spring', stiffness: 500, damping: 30 } : { duration: 0 }}
            >
              <AnimatePresence mode="wait">
                {mobileMenuOpen ? (
                  <motion.div
                    key="close"
                    initial={shouldAnimate ? { rotate: -90, opacity: 0 } : undefined}
                    animate={shouldAnimate ? { rotate: 0, opacity: 1 } : undefined}
                    exit={shouldAnimate ? { rotate: 90, opacity: 0 } : undefined}
                    transition={shouldAnimate ? { type: 'spring', stiffness: 400, damping: 30 } : { duration: 0 }}
                  >
                    <X className="w-6 h-6" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="menu"
                    initial={shouldAnimate ? { rotate: 90, opacity: 0 } : undefined}
                    animate={shouldAnimate ? { rotate: 0, opacity: 1 } : undefined}
                    exit={shouldAnimate ? { rotate: -90, opacity: 0 } : undefined}
                    transition={shouldAnimate ? { type: 'spring', stiffness: 400, damping: 30 } : { duration: 0 }}
                  >
                    <Menu className="w-6 h-6" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          </div>
        </div>

        {/* 移动端菜单 */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={shouldAnimate ? { opacity: 0, height: 0 } : undefined}
              animate={shouldAnimate ? { opacity: 1, height: 'auto' } : undefined}
              exit={shouldAnimate ? { opacity: 0, height: 0 } : undefined}
              transition={shouldAnimate ? { type: 'spring', stiffness: 300, damping: 35 } : { duration: 0 }}
              className="md:hidden border-t border-gray-200 dark:border-gray-800 overflow-hidden"
            >
              <div className="py-4 space-y-1">
                {NAV_ITEMS.map((item, index) => {
                  const Icon = item.icon
                  const isActive = pathname === item.href || pathname?.startsWith(item.href)

                  return (
                    <motion.div
                      key={item.id}
                      initial={shouldAnimate ? { opacity: 0, x: -20 } : undefined}
                      animate={shouldAnimate ? { opacity: 1, x: 0 } : undefined}
                      transition={shouldAnimate ? {
                        type: 'spring',
                        stiffness: 350,
                        damping: 30,
                        delay: index * 0.05
                      } : { duration: 0 }}
                    >
                      <Link
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={cn(
                          'flex items-center space-x-3 px-6 py-5 rounded-xl text-lg font-semibold transition-all duration-200',
                          isActive
                            ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/30'
                            : 'text-gray-700 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                        )}
                      >
                        <Icon className="w-6 h-6" />
                        <span>{item.label}</span>
                      </Link>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  )
}
