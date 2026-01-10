/**
 * [INPUT]: 依赖 Next.js 的 Metadata 类型定义、子页面组件、全局样式文件、framer-motion 的 MotionConfig
 * [OUTPUT]: 对外提供根布局组件，包含全局元数据、主题初始化脚本、Navbar、Footer、Toaster、全局动画配置
 * [POS]: app/ 的根布局组件，是整个应用的布局容器，包裹所有子页面，提供全局导航和页脚
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/navbar'
import { Footer } from '@/components/Footer'
import { Toaster } from 'sonner'
import { MotionConfig } from 'framer-motion'

export const metadata: Metadata = {
  title: 'Signal Hunter - 技术情报聚合',
  description: '面向超级个体的技术情报分析系统',
  icons: {
    icon: '/favicon.ico',
  },
  alternates: {
    types: {
      'application/rss+xml': [
        { url: 'https://signal.felixwithai.com/api/feeds/rss', title: 'Signal Hunter - 全站订阅' },
        { url: 'https://signal.felixwithai.com/api/feeds/rss?featured=true', title: 'Signal Hunter - 精选内容' },
      ],
    },
  },
}

// 主题初始化脚本（防止闪烁）
const themeScript = `
  (function() {
    try {
      var theme = localStorage.getItem('theme');
      var systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      var resolvedTheme = theme === 'system' ? systemTheme : (theme || systemTheme);

      document.documentElement.classList.add(resolvedTheme);

      // 设置 meta theme-color
      var metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.setAttribute('name', 'theme-color');
        document.head.appendChild(metaThemeColor);
      }
      metaThemeColor.setAttribute('content', resolvedTheme === 'dark' ? '#000000' : '#FFFFFF');
    } catch (e) {}
  })();
`

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeScript }}
        />
      </head>
      <body className="antialiased">
        <MotionConfig reducedMotion="user" transition={{ duration: 0.2 }}>
          <Navbar />
          {children}
          <Footer />
          <Toaster position="top-right" richColors />
        </MotionConfig>
      </body>
    </html>
  )
}
