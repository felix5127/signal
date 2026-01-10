/**
 * [INPUT]: framer-motion动画库，Lucide React图标，hoverLift动效预设
 * [OUTPUT]: 内容类型快捷入口卡片网格（4个卡片链接到对应独立页面）
 * [POS]: components/ 的首页内容入口组件，被首页消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import Link from 'next/link'
import { FileText, Mic, Twitter, Video } from 'lucide-react'
import { motion } from 'framer-motion'
import { fadeInUp, staggerContainer, hoverLift } from '@/lib/motion'

// 资源类型配置（本地定义，避免路径解析问题）
const RESOURCE_TYPES = [
  {
    id: 'article',
    label: '文章',
    icon: FileText,
    path: '/articles',
    description: '深度技术文章与研究成果，帮助您快速掌握前沿技术',
  },
  {
    id: 'podcast',
    label: '播客',
    icon: Mic,
    path: '/podcasts',
    description: '行业专家访谈与技术讨论，聆听前沿思考',
  },
  {
    id: 'tweet',
    label: '推文',
    icon: Twitter,
    path: '/tweets',
    description: '技术专家观点与即时思考，快速捕捉行业动态',
  },
  {
    id: 'video',
    label: '视频',
    icon: Video,
    path: '/videos',
    description: '技术教程与会议演讲，视频化学习前沿技术',
  },
] as const

/**
 * 内容入口卡片组件
 *
 * 在首页展示4个内容类型的快捷入口
 * 每个卡片包含图标、标题、描述和链接
 */
export function ContentHubCards() {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      {Object.values(RESOURCE_TYPES).map((type, index) => {
        const Icon = type.icon
        return (
          <motion.div key={type.id} variants={fadeInUp} custom={index}>
            <motion.div
              whileHover="hover"
              initial="rest"
              variants={hoverLift}
            >
              <Link
                href={type.path}
                className="group block p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white shadow-md hover:shadow-lg transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg flex items-center justify-center">
                    <Icon className="w-6 h-6 text-purple-600" />
                  </div>
                  <span className="text-2xl text-gray-300 group-hover:text-purple-500 transition-colors duration-200">
                    →
                  </span>
                </div>
                <h3 className="text-xl font-bold mb-2 text-gray-900 group-hover:text-purple-600 transition-colors duration-200">
                  {type.label}
                </h3>
                <p className="text-sm text-gray-600">
                  {type.description}
                </p>
              </Link>
            </motion.div>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
