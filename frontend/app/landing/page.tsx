// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'
/**
 * [INPUT]: 依赖 components/landing 的所有 Section 组件，依赖 @/lib/motion 的动画预设
 * [OUTPUT]: 对外提供完整的 Landing Page 页面，整合所有营销区域
 * [POS]: app/ 的落地页，被用户访问 /landing 路由时消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import {
  Hero,
  LogoBar,
  ProblemSection,
  FeaturesSection,
  HowItWorks,
  Testimonials,
  Pricing,
  FAQ,
  FinalCTA,
  Footer
} from '@/components/landing'
import { signalHunterPricing } from '@/components/landing/Pricing'

/* ========================================
   Signal Landing Page
   ======================================== */

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <Hero
        headline="Discover High-Value Signals from the Noise"
        subheadline="AI-powered technical intelligence platform that filters, analyzes, and summarizes the most valuable signals from tech blogs, podcasts, and Twitter—saving you 2 hours daily."
        primaryCTA={{
          text: 'Get Started Free',
          href: '/resources'
        }}
        secondaryCTA={{
          text: 'View Demo',
          href: '#how-it-works'
        }}
        socialProof="Trusted by 10,000+ developers, investors, and tech creators worldwide"
      />

      {/* Logo Bar */}
      <LogoBar
        title="Trusted by industry leaders"
        logos={[
          { name: 'Y Combinator', icon: <span className="text-2xl font-bold text-orange-600">Y</span> },
          { name: 'Twitter', icon: <span className="text-2xl font-bold text-blue-500">𝕏</span> },
          { name: 'RSS', icon: <span className="text-2xl font-bold text-orange-500">RSS</span> },
          { name: 'Podcasts', icon: <span className="text-2xl font-bold text-purple-600">🎙️</span> },
          { name: 'TechCrunch', icon: <span className="text-2xl font-bold text-green-600">TC</span> }
        ]}
      />

      {/* Problem Section */}
      <ProblemSection
        headline="Still Struggling with Information Overload?"
        painPoints={[
          {
            title: 'Information Overload',
            description: 'Drowning in endless blog posts, tweets, and podcasts, unable to identify what truly matters.'
          },
          {
            title: 'Time-Consuming Filtering',
            description: 'Spending 2+ hours daily manually sifting through noise to find 2-3 valuable signals worth your attention.'
          },
          {
            title: 'Missing Critical Insights',
            description: 'Losing opportunities while sleeping—new breakthroughs happen 24/7, and you can\'t keep up manually.'
          }
        ]}
      />

      {/* Features Section */}
      <FeaturesSection
        headline="Everything You Need to Stay Ahead"
        subheadline="Powerful AI-driven features designed to help you discover, analyze, and act on high-value technical signals."
        features={[
          {
            title: 'AI-Powered Filtering',
            description: 'Advanced AI models analyze and filter thousands of signals daily, identifying only the most valuable content worth your time.',
            badge: 'Powered by Kimi AI'
          },
          {
            title: 'Real-Time Processing',
            description: 'Automated hourly collection from Twitter, tech blogs, and podcasts ensures you never miss breaking developments.'
          },
          {
            title: 'Smart Scoring',
            description: 'Each signal is scored 0-100 based on novelty, impact, and reproducibility. Focus on ≥70 scores for curated quality.'
          },
          {
            title: 'AI Summaries',
            description: 'Get instant 300-word summaries with one-line takeaways, detailed analysis, and automatic categorization.'
          },
          {
            title: 'Deep Research',
            description: 'One-click 1500-word reports with technical analysis, competitive landscape, and use case exploration.',
            badge: 'New'
          },
          {
            title: 'Trend Tracking',
            description: 'Monitor emerging patterns across repositories, papers, and products. Stay ahead of the innovation curve.'
          }
        ]}
      />

      {/* How It Works */}
      <HowItWorks
        headline="How Signal Works"
        subheadline="Simple 3-step process to transform information overload into actionable intelligence"
        steps={[
          {
            step: 1,
            title: 'Data Collection',
            description: 'Our system automatically monitors curated Twitter accounts, tech blogs via RSS, and AI podcasts every hour.'
          },
          {
            step: 2,
            title: 'AI Analysis',
            description: 'Each signal is processed by Kimi AI to check if it meets our quality criteria: new code, novel models, original research, or reproducible results.'
          },
          {
            step: 3,
            title: 'Smart Delivery',
            description: 'High-quality signals (score ≥70) are saved with AI-generated summaries, tags, and categorized into your personalized feed.'
          }
        ]}
      />

      {/* Testimonials */}
      <Testimonials
        headline="What Our Users Say"
        subheadline="Join thousands of satisfied users who have transformed their information consumption"
        testimonials={[
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
        ]}
      />

      {/* Pricing */}
      <Pricing
        headline="Simple, Transparent Pricing"
        subheadline="No hidden fees. Cancel anytime. Choose the plan that fits your needs."
        plans={signalHunterPricing}
        toggle={{
          monthly: 'Monthly',
          annually: 'Annually',
          onSave: 'Save 20%'
        }}
      />

      {/* FAQ */}
      <FAQ
        headline="Frequently Asked Questions"
        faqs={[
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
            answer: 'Our system runs hourly, collecting the latest signals from Twitter, tech blogs, and podcasts. New content is typically processed and available within 30-60 minutes after publication.'
          }
        ]}
      />

      {/* Final CTA */}
      <FinalCTA
        headline="Ready to Discover High-Value Signals?"
        subheadline="Join thousands of developers, investors, and tech creators who save 2+ hours daily with AI-powered intelligence."
        primaryCTA={{
          text: 'Get Started Free',
          href: '/resources'
        }}
        secondaryCTA={{
          text: 'Schedule Demo',
          href: 'mailto:support@signalhunter.com'
        }}
      />

      {/* Footer */}
      <Footer
        columns={[
          {
            title: 'Product',
            links: [
              { label: 'Features', href: '#features' },
              { label: 'Pricing', href: '#pricing' },
              { label: 'FAQ', href: '#faq' }
            ]
          },
          {
            title: 'Resources',
            links: [
              { label: 'Documentation', href: 'https://github.com/felixwithai/signal' },
              { label: 'API', href: '/stats' },
              { label: 'Blog', href: '/newsletters' }
            ]
          },
          {
            title: 'Company',
            links: [
              { label: 'About', href: 'https://github.com/felixwithai' },
              { label: 'Contact', href: 'mailto:support@signalhunter.com' }
            ]
          },
          {
            title: 'Community',
            links: [
              { label: 'GitHub', href: 'https://github.com/felixwithai/signal' },
              { label: 'Twitter', href: 'https://twitter.com/felixwithai' }
            ]
          }
        ]}
        legal={[
          { label: 'Privacy', href: '/privacy' },
          { label: 'Terms', href: '/terms' }
        ]}
        social={{
          github: 'https://github.com/felixwithai/signal',
          twitter: 'https://twitter.com/felixwithai',
          email: 'support@signalhunter.com'
        }}
      />
    </div>
  )
}
