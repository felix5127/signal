/**
 * [INPUT]: 依赖 @/components/ui 的 Button 组件，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供最终行动召唤区域组件，包含渐变背景和CTA按钮
 * [POS]: landing/ 的最终CTA区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight, Sparkles } from 'lucide-react'
import { fadeInUp, viewportConfig } from '@/lib/motion'

export interface FinalCTAProps {
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
}

export function FinalCTA({
  headline,
  subheadline,
  primaryCTA,
  secondaryCTA
}: FinalCTAProps) {
  return (
    <section className="relative py-20 md:py-32 overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-accent/10 to-primary/10" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

      {/* Decorative Elements */}
      <div className="absolute top-0 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-accent/20 rounded-full blur-3xl" />

      {/* Content */}
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={viewportConfig}
        className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center"
      >
        {/* Badge */}
        <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 mb-6">
          <div className="px-4 py-2 rounded-full bg-primary/10 text-primary font-semibold text-sm">
            <Sparkles className="h-4 w-4 inline mr-1" />
            Start Your Journey Today
          </div>
        </motion.div>

        {/* Headline */}
        <motion.h2
          variants={fadeInUp}
          className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6"
        >
          {headline}
        </motion.h2>

        {/* Subheadline */}
        <motion.p
          variants={fadeInUp}
          className="text-xl md:text-2xl text-muted-foreground mb-10"
        >
          {subheadline}
        </motion.p>

        {/* CTA Buttons */}
        {(primaryCTA || secondaryCTA) && (
          <motion.div
            variants={fadeInUp}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            {primaryCTA && (
              <Button
                size="xl"
                variant="default"
                onClick={primaryCTA.onClick}
                className="group text-lg"
                {...(primaryCTA.href && { as: 'a', href: primaryCTA.href })}
              >
                {primaryCTA.text}
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            )}

            {secondaryCTA && (
              <Button
                size="xl"
                variant="outline"
                onClick={secondaryCTA.onClick}
                className="text-lg"
                {...(secondaryCTA.href && { as: 'a', href: secondaryCTA.href })}
              >
                {secondaryCTA.text}
              </Button>
            )}
          </motion.div>
        )}
      </motion.div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

export const signalHunterFinalCTA: FinalCTAProps = {
  headline: 'Ready to Discover High-Value Signals?',
  subheadline: 'Join thousands of developers, investors, and tech creators who save 2+ hours daily with AI-powered intelligence.',
  primaryCTA: {
    text: 'Get Started Free',
    href: '/resources'
  },
  secondaryCTA: {
    text: 'Schedule Demo',
    href: 'mailto:support@signalhunter.com'
  }
}
