/**
 * Hero - Mercury.com 风格首屏区域
 * 设计规范: 深海军蓝主题 + Inter字体 + 统计数据
 */
'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, Sparkles } from 'lucide-react'

export interface HeroProps {
  badge?: {
    text: string
  }
  headline: string
  subheadline: string
  primaryCTA?: {
    text: string
    href?: string
    onClick?: () => void
  }
  secondaryCTA?: {
    text: string
    href?: string
    onClick?: () => void
  }
  stats?: {
    signals: string
    sources: string
    categories: string
  }
  // Backward compatibility
  socialProof?: string
}

// 动画配置
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
}

export function Hero({
  badge,
  headline,
  subheadline,
  primaryCTA,
  secondaryCTA,
  stats,
}: HeroProps) {
  return (
    <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden bg-[#FBFCFD]">
      {/* 背景装饰 - Mercury 风格微妙渐变 */}
      <div className="absolute inset-0 -z-10">
        {/* 主背景 */}
        <div className="absolute inset-0 bg-[#FBFCFD]" />

        {/* 微妙的渐变光晕 */}
        <div
          className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, #D4DDE8 0%, transparent 70%)',
          }}
        />
        <div
          className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full opacity-15"
          style={{
            background: 'radial-gradient(circle, #EFF6FF 0%, transparent 70%)',
          }}
        />

        {/* 网格装饰 */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0,0,0,0.06) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0,0,0,0.06) 1px, transparent 1px)
            `,
            backgroundSize: '64px 64px',
          }}
        />
      </div>

      {/* 内容 */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center"
      >
        {/* Badge */}
        {badge && (
          <motion.div variants={fadeInUp} className="flex justify-center mb-6">
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[20px] text-[13px] font-medium text-[#1E3A5F]"
              style={{ backgroundColor: 'rgba(30, 58, 95, 0.08)' }}
            >
              <Sparkles className="w-3.5 h-3.5" />
              {badge.text}
            </span>
          </motion.div>
        )}

        {/* Headline */}
        <motion.h1
          variants={fadeInUp}
          transition={{ duration: 0.5 }}
          className="text-4xl md:text-5xl lg:text-[56px] font-light text-[#272735] mb-6"
          style={{ letterSpacing: '-0.5px', lineHeight: 1.1 }}
        >
          {headline}
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          variants={fadeInUp}
          transition={{ duration: 0.5 }}
          className="text-base md:text-lg text-[#6B6B6B] max-w-[640px] mx-auto mb-10"
          style={{ lineHeight: 1.6 }}
        >
          {subheadline}
        </motion.p>

        {/* CTA Buttons - 设计稿规范: 16px字号, 500字重, 10px圆角, 14px/28px内边距 */}
        {(primaryCTA || secondaryCTA) && (
          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            {primaryCTA && (
              <Link
                href={primaryCTA.href || '#'}
                className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-[10px] bg-[#1E3A5F] text-white text-base font-medium transition-all hover:bg-[#152840]"
              >
                {primaryCTA.text}
                <ArrowRight className="w-[18px] h-[18px] transition-transform group-hover:translate-x-1" />
              </Link>
            )}

            {secondaryCTA && (
              <Link
                href={secondaryCTA.href || '#'}
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-[10px] border border-[#E8E5E0] text-[#272735] text-base font-medium transition-all hover:bg-[#F8F9FA]"
              >
                {secondaryCTA.text}
              </Link>
            )}
          </motion.div>
        )}

        {/* Stats */}
        {stats && (
          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-16"
          >
            <div className="flex flex-col items-center gap-1">
              <div className="text-[32px] font-medium text-[#1E3A5F]">{stats.signals}</div>
              <div className="text-sm text-[#9A9A9A]">技术信号</div>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="text-[32px] font-medium text-[#1E3A5F]">{stats.sources}</div>
              <div className="text-sm text-[#9A9A9A]">精选内容</div>
            </div>
            <div className="flex flex-col items-center gap-1">
              <div className="text-[32px] font-medium text-[#1E3A5F]">{stats.categories}</div>
              <div className="text-sm text-[#9A9A9A]">研究报告</div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </section>
  )
}

/* 预设配置 */
export const signalHunterHeroConfig: HeroProps = {
  badge: {
    text: 'AI 驱动的技术情报分析',
  },
  headline: '发现改变世界的技术信号',
  subheadline: '从 Hacker News、GitHub、arXiv 等源头自动筛选高质量技术信号，通过 AI 生成结构化摘要和研究报告',
  primaryCTA: {
    text: '开始探索',
    href: '/articles',
  },
  secondaryCTA: {
    text: '了解更多',
    href: '/featured',
  },
  stats: {
    signals: '10,000+',
    sources: '500+',
    categories: '50+',
  },
}
