/**
 * [INPUT]: Hero组件, FeaturesSection组件, ContentHubCards组件, 配置数据
 * [OUTPUT]: 产品介绍精简版首页（Hero + 核心特性 + 内容入口 + CTA）
 * [POS]: app/ 的根路由页面，展示产品核心特性与内容入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { Hero } from '@/components/landing/Hero'
import { FeaturesSection, signalHunterFeatures } from '@/components/landing/FeaturesSection'
import { ContentHubCards } from '@/components/content-hub-cards'
import { signalHunterHeroConfig } from '@/components/landing/Hero'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <Hero
        {...signalHunterHeroConfig}
        primaryCTA={{ text: '开始探索', href: '/articles' }}
      />

      {/* 核心特性展示（精简版：前6个） */}
      <FeaturesSection
        headline="为什么选择 Signal Hunter?"
        subheadline="AI驱动的技术情报分析平台，帮助您从信息噪音中发现高价值信号"
        features={signalHunterFeatures.slice(0, 6)}
        layout="grid"
      />

      {/* 内容入口卡片 */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              探索内容
            </h2>
            <p className="text-lg text-gray-600">
              选择您感兴趣的内容类型，开始探索高价值技术情报
            </p>
          </div>
          <ContentHubCards />
        </div>
      </section>

      {/* 简短CTA */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            准备好开始您的AI探索之旅了吗？
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            加入数千名开发者、投资者和技术创作者，每天节省2小时信息筛选时间
          </p>
          <Button size="xl" asChild className="text-xl md:text-2xl">
            <a href="/articles">
              立即开始
              <ArrowRight className="ml-2 h-6 w-6" />
            </a>
          </Button>
        </div>
      </section>
    </div>
  )
}
