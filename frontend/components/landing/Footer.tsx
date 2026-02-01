/**
 * [INPUT]: 依赖 lucide-react 图标，依赖 @/lib 的 cn 工具函数
 * [OUTPUT]: 对外提供页脚组件，包含导航链接、法律信息和社交媒体图标
 * [POS]: landing/ 的页脚区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import Link from 'next/link'
import { Github, Twitter, Linkedin, Youtube, Mail } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface FooterLink {
  label: string
  href: string
}

export interface FooterColumn {
  title: string
  links: FooterLink[]
}

export interface FooterProps {
  columns: FooterColumn[]
  legal?: FooterLink[]
  social?: {
    github?: string
    twitter?: string
    linkedin?: string
    youtube?: string
    email?: string
  }
  copyright?: string
}

export function Footer({ columns, legal, social, copyright }: FooterProps) {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-border/50 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Content */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {columns.map((column, index) => (
            <div key={index} className="space-y-4">
              <h3 className="font-semibold text-sm">{column.title}</h3>
              <ul className="space-y-3">
                {column.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-border/50 pt-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Legal Links */}
            {legal && legal.length > 0 && (
              <div className="flex items-center gap-4 text-sm">
                {legal.map((link, index) => (
                  <Link
                    key={index}
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            )}

            {/* Social Icons */}
            {social && (
              <div className="flex items-center gap-4">
                {social.github && (
                  <Link
                    href={social.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Github className="h-5 w-5" />
                  </Link>
                )}
                {social.twitter && (
                  <Link
                    href={social.twitter}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Twitter className="h-5 w-5" />
                  </Link>
                )}
                {social.linkedin && (
                  <Link
                    href={social.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Linkedin className="h-5 w-5" />
                  </Link>
                )}
                {social.youtube && (
                  <Link
                    href={social.youtube}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Youtube className="h-5 w-5" />
                  </Link>
                )}
                {social.email && (
                  <Link
                    href={`mailto:${social.email}`}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Mail className="h-5 w-5" />
                  </Link>
                )}
              </div>
            )}

            {/* Copyright */}
            <p className="text-sm text-muted-foreground">
              {copyright || `© ${currentYear} Signal. All rights reserved.`}
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

export const signalHunterFooterColumns: FooterColumn[] = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'Pricing', href: '#pricing' },
      { label: 'FAQ', href: '#faq' },
      { label: 'Changelog', href: '/newsletters' }
    ]
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: 'https://github.com/felixwithai/signal' },
      { label: 'API Reference', href: '/stats' },
      { label: 'Blog', href: '/newsletters' },
      { label: 'RSS Feed', href: '/api/feeds/rss' }
    ]
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: 'https://github.com/felixwithai' },
      { label: 'Careers', href: '#' },
      { label: 'Contact', href: 'mailto:support@signalhunter.com' }
    ]
  },
  {
    title: 'Community',
    links: [
      { label: 'GitHub', href: 'https://github.com/felixwithai/signal' },
      { label: 'Twitter', href: 'https://twitter.com/felixwithai' },
      { label: 'Discord', href: '#' }
    ]
  }
]

export const signalHunterFooterLegal: FooterLink[] = [
  { label: 'Privacy', href: '/privacy' },
  { label: 'Terms', href: '/terms' },
  { label: 'License', href: 'https://github.com/felixwithai/signal/blob/main/LICENSE' }
]

export const signalHunterFooterSocial = {
  github: 'https://github.com/felixwithai/signal',
  twitter: 'https://twitter.com/felixwithai',
  linkedin: 'https://linkedin.com/in/felixwithai',
  email: 'support@signalhunter.com'
}
