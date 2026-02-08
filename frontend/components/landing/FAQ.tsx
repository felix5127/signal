/**
 * [INPUT]: 依赖 @/components/ui 的 Accordion 组件，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供常见问题展示区域组件，使用折叠面板交互
 * [POS]: landing/ 的常见问题区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion'
import { fadeInUp, viewportConfig } from '@/lib/motion'

export interface FAQItem {
  question: string
  answer: string
}

export interface FAQProps {
  headline: string
  subheadline?: string
  faqs: FAQItem[]
}

export function FAQ({ headline, subheadline, faqs }: FAQProps) {
  return (
    <section id="faq" className="py-20 md:py-28 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
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

        {/* FAQ Accordion */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
          className="max-w-3xl mx-auto"
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                variants={fadeInUp}
                className="rounded-lg border border-border bg-background"
              >
                <AccordionItem value={`item-${index}`} className="border-0">
                  <AccordionTrigger className="px-6 py-4 text-left hover:no-underline hover:text-primary transition-colors">
                    <span className="text-lg font-semibold">{faq.question}</span>
                  </AccordionTrigger>
                  <AccordionContent className="px-6 pb-4">
                    <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
                  </AccordionContent>
                </AccordionItem>
              </motion.div>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

export const signalHunterFAQs: FAQItem[] = [
  {
    question: 'How accurate are the AI summaries?',
    answer: 'Our Kimi AI-powered summaries achieve over 95% accuracy in capturing key technical details. The AI is trained on technical documentation and research papers, ensuring it understands domain-specific terminology and context.'
  },
  {
    question: 'Can I use Signal for commercial purposes?',
    answer: 'Yes! The Pro and Team plans include commercial usage rights. You can use the signals, summaries, and reports for your business, investment research, or content creation.'
  },
  {
    question: 'How often is the data updated?',
    answer: 'Our system runs hourly, collecting the latest signals from Twitter, RSS blogs, and podcasts. New content is typically processed and available within 30-60 minutes after publication.'
  },
  {
    question: 'What sources do you track?',
    answer: 'We currently track curated Twitter accounts, high-quality tech blogs via RSS, and AI/tech podcasts. We\'re continuously adding more sources based on user feedback.'
  },
  {
    question: 'Can I request custom sources or features?',
    answer: 'Absolutely! Team plan users get custom integrations. For other plans, you can suggest new sources or features through our feedback page, and we\'ll prioritize based on demand.'
  },
  {
    question: 'Is there a free trial for paid plans?',
    answer: 'Yes, we offer a 14-day free trial for the Pro plan with full access to all features. No credit card required to start.'
  }
]
