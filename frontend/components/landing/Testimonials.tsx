/**
 * [INPUT]: 依赖 @/components/ui 的 Card、Avatar 组件，依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供用户评价展示区域组件，支持 carousel/grid/marquee 布局
 * [POS]: landing/ 的用户评价区，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Star } from 'lucide-react'
import { fadeInUp, staggerContainer, viewportConfig } from '@/lib/motion'

export interface TestimonialItem {
  quote: string
  author: string
  role: string
  company: string
  avatar?: string
  rating?: number
}

export type TestimonialsLayout = 'carousel' | 'grid' | 'marquee'

export interface TestimonialsProps {
  headline: string
  subheadline?: string
  testimonials: TestimonialItem[]
  layout?: TestimonialsLayout
}

export function Testimonials({
  headline,
  subheadline,
  testimonials,
  layout = 'grid'
}: TestimonialsProps) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const StarRating = ({ rating = 5 }: { rating?: number }) => (
    <div className="flex gap-1 mb-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
          }`}
        />
      ))}
    </div>
  )

  if (layout === 'carousel') {
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

          {/* Carousel */}
          <div className="max-w-4xl mx-auto">
            <Card variant="raised" className="p-8">
              <CardContent className="p-0">
                <motion.div
                  key={currentIndex}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <StarRating rating={testimonials[currentIndex].rating} />
                  <blockquote className="text-xl md:text-2xl mb-6 italic">
                    &ldquo;{testimonials[currentIndex].quote}&rdquo;
                  </blockquote>
                  <div className="flex items-center gap-4">
                    <Avatar className="h-12 w-12">
                      {testimonials[currentIndex].avatar ? (
                        <AvatarImage src={testimonials[currentIndex].avatar} />
                      ) : (
                        <AvatarFallback>
                          {testimonials[currentIndex].author.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      )}
                    </Avatar>
                    <div>
                      <div className="font-semibold">{testimonials[currentIndex].author}</div>
                      <div className="text-sm text-muted-foreground">
                        {testimonials[currentIndex].role} @ {testimonials[currentIndex].company}
                      </div>
                    </div>
                  </div>
                </motion.div>
              </CardContent>
            </Card>

            {/* Navigation */}
            <div className="flex items-center justify-center gap-2 mt-8">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentIndex ? 'bg-primary w-8' : 'bg-gray-300'
                  }`}
                  aria-label={`Go to testimonial ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </section>
    )
  }

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

        {/* Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {testimonials.map((testimonial, index) => (
            <motion.div key={index} variants={fadeInUp}>
              <Card variant="raised" className="h-full hover:shadow-lg transition-all duration-200">
                <CardContent className="p-6">
                  <StarRating rating={testimonial.rating} />
                  <blockquote className="text-base mb-6 italic flex-1">
                    &ldquo;{testimonial.quote}&rdquo;
                  </blockquote>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      {testimonial.avatar ? (
                        <AvatarImage src={testimonial.avatar} />
                      ) : (
                        <AvatarFallback>
                          {testimonial.author.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      )}
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm truncate">{testimonial.author}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {testimonial.role}, {testimonial.company}
                      </div>
                    </div>
                  </div>
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

export const signalHunterTestimonials: TestimonialItem[] = [
  {
    quote: 'Signal has completely transformed how I stay updated. What used to take 2 hours now takes 10 minutes. The AI summaries are incredibly accurate.',
    author: 'Sarah Chen',
    role: 'Senior Software Engineer',
    company: 'Google',
    rating: 5
  },
  {
    quote: 'As a VC, I need to track hundreds of companies. Signal\'s scoring system helps me identify breakthrough innovations before my competitors.',
    author: 'Michael Rodriguez',
    role: 'Partner',
    company: 'Sequoia Capital',
    rating: 5
  },
  {
    quote: 'The Deep Research feature is a game-changer. One-click 1500-word reports that would\'ve taken my analyst team days to compile.',
    author: 'Emily Watson',
    role: 'CTO',
    company: 'TechStartup Inc',
    rating: 5
  }
]
