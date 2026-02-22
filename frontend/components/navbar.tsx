/**
 * Navbar - Mercury.com 风格全局导航栏
 * 设计规范: 深海军蓝主题 + 搜索框 + CTA按钮
 */
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FileText, Mic, Twitter, Search, Menu, X, Radar, Home } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

// 导航项配置 - 按设计稿顺序: 首页/文章/播客/推文 (视频功能已禁用)
const NAV_ITEMS = [
  { id: 'home', label: '首页', href: '/', icon: Home },
  { id: 'articles', label: '文章', href: '/articles', icon: FileText },
  { id: 'podcasts', label: '播客', href: '/podcasts', icon: Mic },
  { id: 'tweets', label: '推文', href: '/tweets', icon: Twitter },
] as const

export default function Navbar() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  // 监听滚动
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav
      className={cn(
        "sticky top-0 z-50 w-full",
        "transition-all duration-300",
        scrolled
          ? "bg-white/95 backdrop-blur-md border-b border-[rgba(0,0,0,0.06)] shadow-sm"
          : "bg-[#FBFCFD] border-b border-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo - 设计稿: Radar 雷达图标 */}
          <Link
            href="/"
            className="flex items-center gap-2 group transition-opacity hover:opacity-80"
          >
            <Radar className="w-7 h-7 text-[#1E3A5F]" />
            <span className="text-xl font-semibold text-[#272735]">
              Signal
            </span>
          </Link>

          {/* 桌面端导航 */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_ITEMS.map((item) => {
              // 首页需要精确匹配，其他页面支持前缀匹配
              const isActive = item.href === '/'
                ? pathname === '/'
                : pathname === item.href || pathname?.startsWith(item.href + '/')

              return (
                <Link key={item.id} href={item.href}>
                  <span
                    className={cn(
                      "text-sm font-medium transition-colors duration-200",
                      isActive
                        ? "text-[#1E3A5F]"
                        : "text-[#6B6B6B] hover:text-[#272735]"
                    )}
                  >
                    {item.label}
                  </span>
                </Link>
              )
            })}
          </div>

          {/* 右侧操作区 - 设计稿: 仅搜索框 */}
          <div className="flex items-center gap-3">
            {/* 搜索框 - 设计稿: 灰色背景圆角 */}
            <button
              type="button"
              onClick={() => setSearchOpen(!searchOpen)}
              className={cn(
                "hidden md:flex items-center gap-2 px-4 py-2 rounded-lg",
                "text-sm text-[#9A9A9A]",
                "bg-[#F5F3F0]",
                "hover:bg-[#EFECE8]",
                "transition-all duration-200"
              )}
            >
              <Search className="w-4 h-4" />
              <span>搜索信号...</span>
            </button>

            {/* 移动端菜单按钮 */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={cn(
                "md:hidden p-2 rounded-lg",
                "text-[#6B6B6B]",
                "hover:bg-[#F8F9FA]",
                "transition-colors duration-200"
              )}
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* 移动端菜单 */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
              className="md:hidden border-t border-[rgba(0,0,0,0.06)] overflow-hidden"
            >
              <div className="py-3 space-y-1">
                {NAV_ITEMS.map((item, index) => {
                  const Icon = item.icon
                  // 首页需要精确匹配
                  const isActive = item.href === '/'
                    ? pathname === '/'
                    : pathname === item.href || pathname?.startsWith(item.href + '/')

                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05, duration: 0.2 }}
                    >
                      <Link
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={cn(
                          "flex items-center gap-3 px-4 py-3 rounded-lg",
                          "text-base font-medium",
                          "transition-all duration-200",
                          isActive
                            ? "bg-[#EEF2F6] text-[#1E3A5F]"
                            : "text-[#6B6B6B] hover:text-[#272735] hover:bg-[#F8F9FA]"
                        )}
                      >
                        <Icon className="w-5 h-5" />
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
    </nav>
  )
}
