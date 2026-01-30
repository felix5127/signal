/**
 * [INPUT]: 依赖 Next.js 的 Metadata 类型定义、ClientLayout 客户端布局组件、全局样式文件
 * [OUTPUT]: 对外提供根布局组件，包含全局元数据、主题初始化脚本、ClientLayout（Navbar+Footer+Toaster+MotionConfig）
 * [POS]: app/ 的根布局组件，是整个应用的布局容器，包裹所有子页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import type { Metadata } from 'next'
import dynamic from 'next/dynamic'
import { Inter } from 'next/font/google'
import './globals.css'

// Inter 字体配置
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

// 强制动态渲染，禁用静态生成（layout 中不支持 dynamic，需要在每个页面中设置）

// 使用 dynamic import 禁用 SSR，避免 framer-motion 在服务端渲染时出错
const ClientLayout = dynamic(
  () => import('@/components/ClientLayout').then(mod => mod.ClientLayout),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    ),
  }
)

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
    <html lang="zh-CN" suppressHydrationWarning className={inter.variable}>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeScript }}
        />
      </head>
      <body className={`${inter.className} antialiased`}>
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  )
}
