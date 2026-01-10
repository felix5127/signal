/**
 * [INPUT]: 依赖 @/components/ui 的 Button、Badge 组件，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供 Hero 区域组件，包含标题、副标题、CTA 按钮和视觉元素
 * [POS]: landing/ 的首屏区域，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, Zap, Sparkles } from 'lucide-react'
import { fadeInUp, staggerContainer, viewportConfig } from '@/lib/motion'

export interface HeroProps {
  badge?: {
    text: string
    variant?: 'default' | 'secondary' | 'outline'
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
  socialProof?: string
  visual?: React.ReactNode
}

export function Hero({
  badge,
  headline,
  subheadline,
  primaryCTA,
  secondaryCTA,
  socialProof,
  visual
}: HeroProps) {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-accent/10 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        viewport={viewportConfig}
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center"
      >
        {/* Badge */}
        {badge && (
          <motion.div variants={fadeInUp} className="flex justify-center mb-8">
            <Badge variant={badge.variant || 'default'} className="text-sm px-4 py-2">
              {badge.text}
            </Badge>
          </motion.div>
        )}

        {/* Headline */}
        <motion.h1
          variants={fadeInUp}
          className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6"
        >
          {headline}
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          variants={fadeInUp}
          className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-10"
        >
          {subheadline}
        </motion.p>

        {/* CTA Buttons */}
        {(primaryCTA || secondaryCTA) && (
          <motion.div
            variants={fadeInUp}
            className="flex justify-center mb-12"
          >
            {primaryCTA && (
              <Link href={primaryCTA.href || '#'} onClick={primaryCTA.onClick}>
                <Button
                  size="xl"
                  variant="default"
                  className="group text-xl md:text-2xl"
                >
                  {primaryCTA.text}
                  <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            )}

            {secondaryCTA && (
              <Link href={secondaryCTA.href || '#'} onClick={secondaryCTA.onClick}>
                <Button
                  size="xl"
                  variant="outline"
                  className="text-xl md:text-2xl"
                >
                  {secondaryCTA.text}
                </Button>
              </Link>
            )}
          </motion.div>
        )}

        {/* Social Proof */}
        {socialProof && (
          <motion.div
            variants={fadeInUp}
            className="flex items-center justify-center gap-2 text-muted-foreground"
          >
            <Sparkles className="h-5 w-5 text-primary" />
            <p className="text-sm">{socialProof}</p>
          </motion.div>
        )}

        {/* Visual */}
        {visual && (
          <motion.div
            variants={fadeInUp}
            className="mt-16 relative"
          >
            {visual}
          </motion.div>
        )}
      </motion.div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal Hunter 使用
   ======================================== */

export const signalHunterHeroConfig: HeroProps = {
  headline: 'Discover High-Value Signals from the Noise',
  subheadline: 'AI-powered technical intelligence platform that filters, analyzes, and summarizes the most valuable signals from Hacker News, GitHub, and arXiv—saving you 2 hours daily.',
  primaryCTA: {
    text: 'Get Started Free',
    href: '/resources'
  }
}
