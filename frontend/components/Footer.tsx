/**
 * Footer - Mercury.com 风格全局页脚
 * 设计规范: 浅色背景 #F8F9FA + 深海军蓝主题
 */

import Link from 'next/link'
import { Radar } from 'lucide-react'

const footerLinks = {
  content: [
    { label: '文章', href: '/articles' },
    { label: '视频', href: '/videos' },
    { label: '播客', href: '/podcasts' },
    { label: '推文', href: '/tweets' },
  ],
  about: [
    { label: '关于我们', href: '/about' },
    { label: '联系方式', href: '/contact' },
  ],
}

export function Footer() {
  return (
    <footer
      className="border-t py-16 px-4 sm:px-6 lg:px-20"
      style={{ backgroundColor: '#F8F9FA', borderColor: '#E8E5E0' }}
    >
      <div className="max-w-7xl mx-auto">
        {/* 主要内容区域 */}
        <div className="flex flex-col md:flex-row justify-between gap-12 mb-12">
          {/* Logo 和描述 */}
          <div style={{ width: 300 }}>
            <div className="flex items-center gap-2 mb-4">
              <Radar className="w-6 h-6" style={{ color: '#1E3A5F' }} />
              <span className="text-lg font-semibold" style={{ color: '#272735' }}>
                Signal Hunter
              </span>
            </div>
            <p
              className="text-sm leading-relaxed"
              style={{ color: '#6B6B6B', width: 280 }}
            >
              AI 驱动的技术情报分析平台，帮助你发现改变世界的技术信号。
            </p>
          </div>

          {/* 链接区域 */}
          <div className="flex gap-20">
            {/* 内容链接 */}
            <div className="flex flex-col gap-4">
              <h4 className="text-sm font-semibold" style={{ color: '#272735' }}>
                内容
              </h4>
              <ul className="flex flex-col gap-3">
                {footerLinks.content.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm hover:text-[#1E3A5F] transition-colors"
                      style={{ color: '#6B6B6B' }}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* 关于链接 */}
            <div className="flex flex-col gap-4">
              <h4 className="text-sm font-semibold" style={{ color: '#272735' }}>
                关于
              </h4>
              <ul className="flex flex-col gap-3">
                {footerLinks.about.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm hover:text-[#1E3A5F] transition-colors"
                      style={{ color: '#6B6B6B' }}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* 底部版权 */}
        <div
          className="border-t pt-6"
          style={{ borderColor: '#E8E5E0' }}
        >
          <p className="text-[13px]" style={{ color: '#9A9A9A' }}>
            © 2024 Signal Hunter. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
