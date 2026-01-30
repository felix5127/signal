/**
 * ContentHubCards - Mercury.com 风格内容入口卡片
 * 设计规范: 深海军蓝主题 + 16px圆角 + 图标+标题+描述+数量
 */
'use client'

import Link from 'next/link'
import { FileText, Mic, Twitter, Video } from 'lucide-react'
import { motion } from 'framer-motion'

// 资源类型配置 - 按设计稿颜色方案
const RESOURCE_TYPES = [
  {
    id: 'article',
    label: '文章',
    icon: FileText,
    path: '/articles',
    description: '深度技术文章与分析报告',
    count: '2,340 篇',
    iconColor: '#1E3A5F',
    iconBg: '#1E3A5F15',
  },
  {
    id: 'video',
    label: '视频',
    icon: Video,
    path: '/videos',
    description: '技术演讲与教程视频',
    count: '890 个',
    iconColor: '#3D6B4F',
    iconBg: '#3D6B4F15',
  },
  {
    id: 'podcast',
    label: '播客',
    icon: Mic,
    path: '/podcasts',
    description: '行业播客与访谈节目',
    count: '156 期',
    iconColor: '#8B4049',
    iconBg: '#8B404915',
  },
  {
    id: 'tweet',
    label: '推文',
    icon: Twitter,
    path: '/tweets',
    description: '技术领袖的精选推文',
    count: '4,560 条',
    iconColor: '#6366F1',
    iconBg: '#6366F115',
  },
] as const

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

/**
 * 内容入口卡片组件 - 按设计稿垂直布局
 * 设计规范: 图标在上 → 标题 → 描述 → 数量
 */
export function ContentHubCards() {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-100px' }}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      {RESOURCE_TYPES.map((type) => {
        const Icon = type.icon
        return (
          <motion.div key={type.id} variants={fadeInUp}>
            <Link
              href={type.path}
              className="group flex flex-col gap-4 p-6 rounded-2xl bg-white border border-[#E8E5E0] transition-all duration-200 hover:shadow-lg hover:-translate-y-1"
            >
              {/* 图标 */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: type.iconBg }}
              >
                <Icon className="w-6 h-6" style={{ color: type.iconColor }} />
              </div>

              {/* 标题 + 描述 */}
              <div className="flex flex-col gap-2">
                <h3 className="text-lg font-medium text-[#272735]">
                  {type.label}
                </h3>
                <p className="text-sm text-[#6B6B6B] leading-relaxed">
                  {type.description}
                </p>
              </div>

              {/* 数量 */}
              <span className="text-[13px] font-medium text-[#9A9A9A]">
                {type.count}
              </span>
            </Link>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
