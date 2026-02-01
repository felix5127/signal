/**
 * [INPUT]: 依赖 @/components/ui 的 Card 组件，依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供工作流程展示区域组件，展示步骤化的使用流程
 * [POS]: landing/ 的工作流程区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { fadeInUp, staggerContainer, viewportConfig } from '@/lib/motion'
import { Check } from 'lucide-react'

export interface StepItem {
  step: number
  title: string
  description: string
  icon?: React.ReactNode
  visual?: React.ReactNode
}

export interface HowItWorksProps {
  headline: string
  subheadline?: string
  steps: StepItem[]
}

export function HowItWorks({ headline, subheadline, steps }: HowItWorksProps) {
  return (
    <section id="how-it-works" className="py-20 md:py-28 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
          className="text-center mb-16"
        >
          <motion.h2
            variants={fadeInUp}
            className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4"
          >
            {headline}
          </motion.h2>
          {subheadline && (
            <motion.p
              variants={fadeInUp}
              className="text-xl text-muted-foreground max-w-3xl mx-auto"
            >
              {subheadline}
            </motion.p>
          )}
        </motion.div>

        {/* Steps */}
        <div className="max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={step.step}
              initial="hidden"
              whileInView="visible"
              viewport={viewportConfig}
              variants={fadeInUp}
              className="relative"
            >
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute left-12 top-24 w-0.5 h-24 bg-gradient-to-b from-primary/30 to-transparent" />
              )}

              <div className="flex gap-8 items-start mb-12 last:mb-0">
                {/* Step Number */}
                <div className="flex-shrink-0 relative">
                  <div className="w-16 h-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-2xl font-bold shadow-lg">
                    {step.step}
                  </div>
                  {index < steps.length - 1 && (
                    <div className="hidden md:block absolute left-1/2 top-16 w-0.5 h-24 bg-border -translate-x-1/2" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <Card variant="raised" className="hover:shadow-lg transition-all duration-200">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="text-2xl font-bold">{step.title}</h3>
                        {step.icon && (
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            {step.icon}
                          </div>
                        )}
                      </div>
                      <p className="text-muted-foreground mb-4">{step.description}</p>
                      {step.visual && (
                        <div className="mt-4 rounded-lg bg-muted/50 p-4">
                          {step.visual}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Final CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary/10 text-primary font-semibold">
            <Check className="h-5 w-5" />
            <span>Simple 3-Step Process</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

import {
  Search,
  Brain,
  FileText
} from 'lucide-react'

export const signalHunterSteps: StepItem[] = [
  {
    step: 1,
    title: 'Data Collection',
    description: 'Our system automatically monitors HN frontpage, GitHub Trending, arXiv new submissions, and Hugging Face releases every hour.',
    icon: <Search className="h-5 w-5 text-primary" />
  },
  {
    step: 2,
    title: 'AI Analysis',
    description: 'Each signal is processed by Kimi AI to check if it meets our quality criteria: new code, novel models, original research, or reproducible results.',
    icon: <Brain className="h-5 w-5 text-primary" />
  },
  {
    step: 3,
    title: 'Smart Delivery',
    description: 'High-quality signals (score ≥70) are saved with AI-generated summaries, tags, and categorized into your personalized feed.',
    icon: <FileText className="h-5 w-5 text-primary" />
  }
]
