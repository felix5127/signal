/**
 * [INPUT]: React children，Next.js usePathname
 * [OUTPUT]: 对外提供 Admin 后台布局（侧边栏 + 主内容区）
 * [POS]: admin/ 的根布局，包裹所有 admin 子页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Database,
  Calendar,
  Activity,
  FileWarning,
  LogOut,
  Menu,
  X,
  Home,
} from 'lucide-react'
import { useState } from 'react'

// ========== 侧边栏导航配置 ==========

const NAV_ITEMS = [
  { id: 'sources', label: '信号源', href: '/admin/sources', icon: Database },
  { id: 'scheduler', label: '调度器', href: '/admin/scheduler', icon: Calendar },
  { id: 'system', label: '系统状态', href: '/admin/system', icon: Activity },
  { id: 'logs', label: '采集日志', href: '/admin/logs', icon: FileWarning },
] as const

// ========== 组件 ==========

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // 登录页面不显示侧边栏
  if (pathname === '/admin/login') {
    return <>{children}</>
  }

  const handleLogout = async () => {
    try {
      await fetch('/api/admin/logout', { method: 'POST' })
      router.push('/admin/login')
    } catch (e) {
      console.error('Logout error:', e)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--ds-surface)]">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-[var(--ds-bg)] border-b border-[var(--ds-border)] z-40 flex items-center justify-between px-4">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-lg hover:bg-[var(--ds-surface)] transition-colors"
        >
          <Menu className="w-5 h-5 text-[var(--ds-fg)]" />
        </button>
        <span className="font-semibold text-[var(--ds-fg)]">Admin</span>
        <div className="w-9" /> {/* Spacer */}
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-[var(--ds-bg)] border-r border-[var(--ds-border)] z-50 transform transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        {/* Sidebar Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[var(--ds-border)]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-[var(--ds-fg)]">Admin</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-lg hover:bg-[var(--ds-surface)] transition-colors"
          >
            <X className="w-5 h-5 text-[var(--ds-fg)]" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.id}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'text-[var(--ds-muted)] hover:bg-[var(--ds-surface)] hover:text-[var(--ds-fg)]'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--ds-border)]">
          <Link
            href="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[var(--ds-muted)] hover:bg-[var(--ds-surface)] hover:text-[var(--ds-fg)] transition-colors mb-1"
          >
            <Home className="w-5 h-5" />
            <span className="font-medium">返回首页</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">退出登录</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
        {children}
      </main>
    </div>
  )
}
