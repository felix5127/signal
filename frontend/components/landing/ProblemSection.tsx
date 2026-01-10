/**
 * [INPUT]: 依赖 @/components/ui 的 Card 组件，依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供痛点展示区域组件，用于引发用户共鸣
 * [POS]: landing/ 的痛点展示区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { AlertCircle, X } from 'lucide-react'
import { fadeInUp, staggerContainer, viewportConfig } from '@/lib/motion'

export interface PainPoint {
  icon?: React.ReactNode
  title: string
  description: string
}

export interface ProblemSectionProps {
  headline: string
  subheadline?: string
  painPoints: PainPoint[]
}

export function ProblemSection({
  headline,
  subheadline,
  painPoints
}: ProblemSectionProps) {
  return (
    <section className="py-20 md:py-28 bg-muted/30">
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

        {/* Pain Points Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {painPoints.map((painPoint, index) => (
            <motion.div key={index} variants={fadeInUp}>
              <Card
                variant="default"
                className="relative h-full hover:shadow-lg transition-all duration-200"
              >
                <CardContent className="p-6">
                  {/* Icon */}
                  <div className="mb-4 flex items-start gap-3">
                    <div className="flex-shrink-0">
                      {painPoint.icon || (
                        <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
                          <X className="h-6 w-6 text-destructive" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-xl font-semibold mb-2">
                    {painPoint.title}
                  </h3>

                  {/* Description */}
                  <p className="text-muted-foreground">
                    {painPoint.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal Hunter 使用
   ======================================== */

export const signalHunterPainPoints: PainPoint[] = [
  {
    title: 'Information Overload',
    description: 'Drowning in endless HN posts, GitHub repos, and research papers, unable to identify what truly matters.'
  },
  {
    title: 'Time-Consuming Filtering',
    description: 'Spending 2+ hours daily manually sifting through noise to find 2-3 valuable signals worth your attention.'
  },
  {
    title: 'Missing Critical Insights',
    description: 'Losing opportunities while sleeping—new breakthroughs happen 24/7, and you can\'t keep up manually.'
  }
]
