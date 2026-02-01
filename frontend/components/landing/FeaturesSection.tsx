/**
 * [INPUT]: 依赖 @/components/ui 的 Card 组件，依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供特性展示区域组件，支持多种布局模式（grid/bento/alternating）
 * [POS]: landing/ 的特性展示区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { fadeInUp, fadeInLeft, fadeInRight, staggerContainer, viewportConfig } from '@/lib/motion'

export interface FeatureItem {
  icon?: React.ReactNode
  title: string
  description: string
  badge?: string
  span?: 1 | 2 // For bento grid layout
}

export type FeaturesLayout = 'grid' | 'bento' | 'alternating'

export interface FeaturesSectionProps {
  headline: string
  subheadline?: string
  features: FeatureItem[]
  layout?: FeaturesLayout
}

export function FeaturesSection({
  headline,
  subheadline,
  features,
  layout = 'grid'
}: FeaturesSectionProps) {
  const getGridCols = () => {
    switch (layout) {
      case 'grid':
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
      case 'bento':
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
      case 'alternating':
        return 'grid-cols-1'
    }
  }

  return (
    <section className="py-20 md:py-28">
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

        {/* Features Grid */}
        {layout === 'alternating' ? (
          <div className="max-w-4xl mx-auto space-y-12">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial="hidden"
                whileInView="visible"
                viewport={viewportConfig}
                variants={index % 2 === 0 ? fadeInLeft : fadeInRight}
              >
                <Card variant="raised" className="hover:shadow-lg transition-all duration-200">
                  <CardContent className="p-8">
                    <div className="flex gap-6">
                      <div className="flex-shrink-0">
                        {feature.icon && (
                          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                            {feature.icon}
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-xl font-semibold">{feature.title}</h3>
                          {feature.badge && (
                            <Badge variant="default">{feature.badge}</Badge>
                          )}
                        </div>
                        <p className="text-muted-foreground">{feature.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={viewportConfig}
            className={`grid ${getGridCols()} gap-6`}
          >
            {features.map((feature, index) => (
              <motion.div
                key={index}
                variants={fadeInUp}
                className={feature.span === 2 ? 'md:col-span-2' : ''}
              >
                <Card
                  variant="raised"
                  className="relative h-full hover:shadow-lg transition-all duration-200"
                >
                  <CardHeader>
                    <div className="flex items-start justify-between mb-2">
                      {feature.icon && (
                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                          {feature.icon}
                        </div>
                      )}
                      {feature.badge && <Badge variant="default">{feature.badge}</Badge>}
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

import {
  Brain,
  Zap,
  Target,
  FileText,
  Database,
  TrendingUp
} from 'lucide-react'

export const signalHunterFeatures: FeatureItem[] = [
  {
    icon: <Brain className="h-6 w-6 text-primary" />,
    title: 'AI-Powered Filtering',
    description: 'Advanced AI models analyze and filter thousands of signals daily, identifying only the most valuable content worth your time.',
    badge: 'Powered by Kimi AI'
  },
  {
    icon: <Zap className="h-6 w-6 text-primary" />,
    title: 'Real-Time Processing',
    description: 'Automated hourly collection from HN, GitHub, arXiv, and Hugging Face ensures you never miss breaking developments.',
  },
  {
    icon: <Target className="h-6 w-6 text-primary" />,
    title: 'Smart Scoring',
    description: 'Each signal is scored 0-100 based on novelty, impact, and reproducibility. Focus on ≥70 scores for curated quality.',
  },
  {
    icon: <FileText className="h-6 w-6 text-primary" />,
    title: 'AI Summaries',
    description: 'Get instant 300-word summaries with one-line takeaways, detailed analysis, and automatic categorization.',
  },
  {
    icon: <Database className="h-6 w-6 text-primary" />,
    title: 'Deep Research',
    description: 'One-click 1500-word reports with technical analysis, competitive landscape, and use case exploration.',
    badge: 'New'
  },
  {
    icon: <TrendingUp className="h-6 w-6 text-primary" />,
    title: 'Trend Tracking',
    description: 'Monitor emerging patterns across repositories, papers, and products. Stay ahead of the innovation curve.',
  }
]
