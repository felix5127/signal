/**
 * [INPUT]: 依赖 lucide-react 图标，依赖 framer-motion，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供 Logo 展示条组件，用于展示信任背书
 * [POS]: landing/ 的信任展示区域，被 Landing Page 主页面消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { motion } from 'framer-motion'
import { fadeInUp, staggerContainer } from '@/lib/motion'

export interface LogoItem {
  name: string
  icon?: React.ReactNode
  src?: string
  alt?: string
}

export interface LogoBarProps {
  title?: string
  logos: LogoItem[]
  variant?: 'static' | 'marquee'
  grayscale?: boolean
}

export function LogoBar({
  title = 'Trusted by industry leaders',
  logos,
  variant = 'static',
  grayscale = true
}: LogoBarProps) {
  const logoClasses = `
    h-8 md:h-12 w-auto
    ${grayscale ? 'grayscale opacity-60 hover:grayscale-0 hover:opacity-100' : 'opacity-80 hover:opacity-100'}
    transition-all duration-200
  `

  return (
    <section className="py-12 md:py-16 border-y border-border/50 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Title */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-sm text-muted-foreground mb-8"
        >
          {title}
        </motion.p>

        {/* Logos Grid */}
        {variant === 'static' ? (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-100px' }}
            className="flex flex-wrap items-center justify-center gap-8 md:gap-12"
          >
            {logos.map((logo, index) => (
              <motion.div
                key={logo.name}
                variants={fadeInUp}
                className="flex items-center justify-center"
              >
                {logo.icon ? (
                  <div className={logoClasses}>{logo.icon}</div>
                ) : logo.src ? (
                  <img
                    src={logo.src}
                    alt={logo.alt || logo.name}
                    className={logoClasses}
                  />
                ) : (
                  <div className="text-lg font-semibold text-muted-foreground">
                    {logo.name}
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="overflow-hidden">
            <motion.div
              animate={{
                x: [0, -1000]
              }}
              transition={{
                x: {
                  duration: 20,
                  repeat: Infinity,
                  ease: 'linear',
                }
              }}
              className="flex items-center gap-8 md:gap-12 w-max"
            >
              {logos.concat(logos).map((logo, index) => (
                <div
                  key={`${logo.name}-${index}`}
                  className="flex items-center justify-center"
                >
                  {logo.icon ? (
                    <div className={logoClasses}>{logo.icon}</div>
                  ) : logo.src ? (
                    <img
                      src={logo.src}
                      alt={logo.alt || logo.name}
                      className={logoClasses}
                    />
                  ) : (
                    <div className="text-lg font-semibold text-muted-foreground">
                      {logo.name}
                    </div>
                  )}
                </div>
              ))}
            </motion.div>
          </div>
        )}
      </div>
    </section>
  )
}

/* ========================================
   预设配置 - Signal 使用
   ======================================== */

import {
  Github,
  Twitter,
  Linkedin,
  Youtube,
  MessageSquare
} from 'lucide-react'

export const signalHunterLogos: LogoItem[] = [
  {
    name: 'Y Combinator',
    icon: <span className="text-2xl font-bold text-orange-600">Y</span>
  },
  {
    name: 'Hacker News',
    icon: <span className="text-2xl font-bold text-orange-600">HN</span>
  },
  {
    name: 'GitHub',
    icon: <Github className="h-12 w-12" />
  },
  {
    name: 'Product Hunt',
    icon: <span className="text-2xl font-bold text-orange-600">PH</span>
  },
  {
    name: 'TechCrunch',
    icon: <span className="text-2xl font-bold text-green-600">TC</span>
  },
  {
    name: 'Wired',
    icon: <span className="text-2xl font-bold text-black">WIRED</span>
  }
]
