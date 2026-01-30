/**
 * HomePage - Mercury.com 风格首页内容
 * 设计规范: 深海军蓝主题 + Inter字体 + 16px圆角
 */
'use client'

import { useState, useEffect } from 'react'
import { Hero, signalHunterHeroConfig } from '@/components/landing/Hero'
import { ContentHubCards } from '@/components/content-hub-cards'
import { Button } from '@/components/ui/button'
import { ArrowRight, FileText, Mic, Twitter, Video, Calendar, Flame } from 'lucide-react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'

// 动画配置
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}

// 精选内容类型
interface FeaturedResource {
  id: number
  title: string
  title_translated?: string
  description?: string
  one_sentence_summary_zh?: string
  type: string
  published_at?: string
  created_at?: string
  tags?: string[]
}

// 获取 API 地址
function getApiUrl(): string {
  return process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : '/api'
}

// 彩色占位图背景
const placeholderColors = [
  'bg-gradient-to-br from-blue-400 to-indigo-500',
  'bg-gradient-to-br from-emerald-400 to-teal-500',
  'bg-gradient-to-br from-orange-400 to-rose-500',
]

// 类型图标映射
const typeIcons: Record<string, React.ElementType> = {
  article: FileText,
  podcast: Mic,
  tweet: Twitter,
  video: Video,
}

// 类型中文映射
const typeLabels: Record<string, string> = {
  article: '文章',
  podcast: '播客',
  tweet: '推文',
  video: '视频',
}

export default function HomePageContent() {
  const [featuredResources, setFeaturedResources] = useState<FeaturedResource[]>([])
  const [loading, setLoading] = useState(true)

  // 获取精选内容
  useEffect(() => {
    async function fetchFeatured() {
      try {
        const apiUrl = getApiUrl()
        const response = await fetch(`${apiUrl}/resources?featured=true&pageSize=3&sort=time`)
        if (response.ok) {
          const data = await response.json()
          setFeaturedResources(data.items || [])
        }
      } catch (error) {
        console.error('获取精选内容失败:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchFeatured()
  }, [])

  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="min-h-screen bg-[#FBFCFD]">
      {/* Hero Section */}
      <Hero {...signalHunterHeroConfig} />

      {/* Categories Section - 探索内容 */}
      <section className="py-20 bg-[#FBFCFD]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-100px' }}
            variants={staggerContainer}
          >
            {/* Section Header */}
            <motion.div
              variants={fadeInUp}
              className="flex items-center justify-between mb-10"
            >
              <h2 className="text-2xl md:text-3xl font-semibold text-[#272735]">
                探索内容
              </h2>
              <Link
                href="/articles"
                className="text-sm font-medium text-[#1E3A5F] hover:text-[#152840] transition-colors flex items-center gap-1"
              >
                查看全部
                <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>

            {/* Content Hub Cards */}
            <ContentHubCards />
          </motion.div>
        </div>
      </section>

      {/* Featured Section - 精选信号 */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-100px' }}
            variants={staggerContainer}
          >
            {/* Section Header - 设计稿: 标题 + 绿色徽章 */}
            <motion.div
              variants={fadeInUp}
              className="flex items-center justify-between mb-8"
            >
              <div className="flex items-center gap-3">
                <h2 className="text-[28px] font-medium text-[#272735]">
                  精选信号
                </h2>
                {/* 绿色徽章 - 设计稿 */}
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-md" style={{ backgroundColor: '#3D6B4F15' }}>
                  <Flame className="w-3.5 h-3.5" style={{ color: '#3D6B4F' }} />
                  <span className="text-xs font-medium" style={{ color: '#3D6B4F' }}>评分 ≥ 70</span>
                </div>
              </div>
              <Link
                href="/featured"
                className="text-sm font-medium text-[#1E3A5F] hover:text-[#152840] transition-colors flex items-center gap-1"
              >
                查看全部
                <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>

            {/* Featured Cards */}
            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {loading ? (
                // Loading skeleton
                [...Array(3)].map((_, i) => (
                  <motion.div
                    key={i}
                    variants={fadeInUp}
                    className="bg-white rounded-2xl overflow-hidden border border-[rgba(0,0,0,0.06)]"
                  >
                    <div className={`h-48 ${placeholderColors[i]} animate-pulse`} />
                    <div className="p-6">
                      <div className="h-4 bg-gray-200 rounded w-16 mb-3" />
                      <div className="h-6 bg-gray-200 rounded w-full mb-2" />
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-4" />
                      <div className="h-3 bg-gray-200 rounded w-20" />
                    </div>
                  </motion.div>
                ))
              ) : featuredResources.length > 0 ? (
                featuredResources.map((resource, index) => {
                  const Icon = typeIcons[resource.type] || FileText
                  return (
                    <motion.div key={resource.id} variants={fadeInUp}>
                      <Link href={`/resources/${resource.id}`}>
                        <div className="group bg-white rounded-2xl overflow-hidden border border-[rgba(0,0,0,0.06)] transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
                          {/* 彩色占位图 */}
                          <div className={`h-48 ${placeholderColors[index % 3]} relative`}>
                            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                            <div className="absolute bottom-4 left-4">
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-white/90 text-[#272735]">
                                <Icon className="w-3 h-3" />
                                {typeLabels[resource.type] || resource.type}
                              </span>
                            </div>
                          </div>
                          {/* 内容区域 */}
                          <div className="p-6">
                            <h3 className="text-lg font-semibold text-[#272735] mb-2 line-clamp-2 group-hover:text-[#1E3A5F] transition-colors">
                              {resource.title_translated || resource.title}
                            </h3>
                            <p className="text-sm text-[#6B6B6B] line-clamp-2 mb-4">
                              {resource.one_sentence_summary_zh || resource.description || ''}
                            </p>
                            <div className="flex items-center text-xs text-[#9A9A9A]">
                              <Calendar className="w-3 h-3 mr-1" />
                              {formatDate(resource.published_at || resource.created_at)}
                            </div>
                          </div>
                        </div>
                      </Link>
                    </motion.div>
                  )
                })
              ) : (
                // Empty state
                <div className="col-span-3 text-center py-12">
                  <p className="text-[#6B6B6B]">暂无精选内容</p>
                </div>
              )}
            </motion.div>
          </motion.div>
        </div>
      </section>

    </div>
  )
}
