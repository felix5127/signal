/**
 * [INPUT]: 依赖 @/components/ui 的 Card、Badge、Button 组件，依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供定价方案展示区域组件，支持多个定价方案和高亮显示
 * [POS]: landing/ 的定价展示区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, X } from 'lucide-react'
import { fadeInUp, staggerContainer, viewportConfig } from '@/lib/motion'

export interface PricingFeature {
  name: string
  included: boolean
}

export interface PricingPlan {
  name: string
  price: string
  period?: string
  description?: string
  features: PricingFeature[]
  cta: string
  highlighted?: boolean
  href?: string
}

export interface PricingProps {
  headline: string
  subheadline?: string
  plans: PricingPlan[]
  toggle?: {
    monthly: string
    annually: string
    onSave?: string
  }
}

export function Pricing({ headline, subheadline, plans, toggle }: PricingProps) {
  const [isAnnual, setIsAnnual] = useState(false)

  return (
    <section id="pricing" className="py-20 md:py-28">
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

        {/* Toggle */}
        {toggle && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="flex items-center justify-center gap-4 mb-12"
          >
            <span className={`text-sm ${!isAnnual ? 'font-semibold' : 'text-muted-foreground'}`}>
              {toggle.monthly}
            </span>
            <button
              onClick={() => setIsAnnual(!isAnnual)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                isAnnual ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <motion.div
                animate={{ x: isAnnual ? 28 : 4 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="absolute top-1 w-5 h-5 bg-white rounded-full shadow-md"
              />
            </button>
            <span className={`text-sm ${isAnnual ? 'font-semibold' : 'text-muted-foreground'}`}>
              {toggle.annually}
            </span>
            {toggle.onSave && (
              <Badge variant="default" className="ml-2">
                {toggle.onSave}
              </Badge>
            )}
          </motion.div>
        )}

        {/* Pricing Cards */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 items-center"
        >
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              variants={fadeInUp}
              className={`relative ${plan.highlighted ? 'lg:scale-105' : ''}`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                  <Badge variant="default" className="text-sm px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}
              <Card
                variant={plan.highlighted ? 'raised' : 'default'}
                className={`h-full hover:shadow-lg transition-all duration-200 ${
                  plan.highlighted ? 'ring-2 ring-primary' : ''
                }`}
              >
                <CardHeader>
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold">{plan.price}</span>
                      {plan.period && (
                        <span className="text-muted-foreground">/{plan.period}</span>
                      )}
                    </div>
                    {plan.description && (
                      <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Features */}
                  <ul className="space-y-3">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start gap-3">
                        {feature.included ? (
                          <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                        ) : (
                          <X className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                        )}
                        <span
                          className={
                            feature.included ? 'text-foreground' : 'text-muted-foreground'
                          }
                        >
                          {feature.name}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  <Button
                    size="lg"
                    variant={plan.highlighted ? 'default' : 'outline'}
                    className="w-full"
                    {...(plan.href && { as: 'a', href: plan.href })}
                  >
                    {plan.cta}
                  </Button>
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
   预设配置 - Signal 使用
   ======================================== */

export const signalHunterPricing: PricingPlan[] = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for exploring',
    features: [
      { name: '50 signals per month', included: true },
      { name: 'Basic AI summaries', included: true },
      { name: 'Email support', included: true },
      { name: 'Deep Research reports', included: false },
      { name: 'API access', included: false },
      { name: 'Priority processing', included: false }
    ],
    cta: 'Get Started Free',
    href: '/resources'
  },
  {
    name: 'Pro',
    price: '$19',
    period: 'month',
    description: 'For serious signal hunters',
    features: [
      { name: 'Unlimited signals', included: true },
      { name: 'Advanced AI analysis', included: true },
      { name: 'Deep Research (10/month)', included: true },
      { name: 'API access (10K requests)', included: true },
      { name: 'Priority support', included: true },
      { name: 'Custom filters', included: false }
    ],
    cta: 'Start Pro Trial',
    highlighted: true,
    href: '/resources'
  },
  {
    name: 'Team',
    price: '$49',
    period: 'month',
    description: 'For teams and organizations',
    features: [
      { name: 'Everything in Pro', included: true },
      { name: '5 team members', included: true },
      { name: 'Unlimited Deep Research', included: true },
      { name: 'Unlimited API access', included: true },
      { name: 'Custom integrations', included: true },
      { name: 'Dedicated support', included: true }
    ],
    cta: 'Contact Sales',
    href: 'mailto:sales@signalhunter.com'
  }
]
