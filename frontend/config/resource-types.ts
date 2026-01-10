/**
 * [INPUT]: 无外部依赖
 * [OUTPUT]: 资源类型配置元数据（id/label/icon/path/component/layout/description）
 * [POS]: config/ 的资源类型配置，被列表页面、导航栏、内容入口卡片消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { FileText, Mic, Twitter, Video, LucideIcon } from 'lucide-react'

/**
 * 资源类型配置
 *
 * 单一真相源，定义了4种资源类型的所有元数据
 * 导航栏、列表页、内容入口卡片都共享此配置
 */
export const RESOURCE_TYPES = {
  article: {
    id: 'article',
    label: '文章',
    icon: FileText,
    path: '/articles',
    component: 'ArticleListCard',
    layout: 'list',
    description: '深度技术文章与研究成果，帮助您快速掌握前沿技术',
  },
  podcast: {
    id: 'podcast',
    label: '播客',
    icon: Mic,
    path: '/podcasts',
    component: 'ResourceCard',
    layout: 'grid',
    description: '行业专家访谈与技术讨论，聆听前沿思考',
  },
  tweet: {
    id: 'tweet',
    label: '推文',
    icon: Twitter,
    path: '/tweets',
    component: 'TweetCard',
    layout: 'list',
    description: '技术专家观点与即时思考，快速捕捉行业动态',
  },
  video: {
    id: 'video',
    label: '视频',
    icon: Video,
    path: '/videos',
    component: 'ResourceCard',
    layout: 'grid',
    description: '技术教程与会议演讲，视频化学习前沿技术',
  },
} as const

/**
 * 资源类型键
 */
export type ResourceType = keyof typeof RESOURCE_TYPES

/**
 * 资源类型元数据
 */
export interface ResourceTypeConfig {
  id: string
  label: string
  icon: LucideIcon
  path: string
  component: string
  layout: 'list' | 'grid'
  description: string
}

/**
 * 获取资源类型配置
 */
export function getResourceType(type: ResourceType): ResourceTypeConfig {
  return RESOURCE_TYPES[type]
}

/**
 * 获取所有资源类型列表
 */
export function getAllResourceTypes(): ResourceType[] {
  return Object.keys(RESOURCE_TYPES) as ResourceType[]
}

/**
 * 根据路径获取资源类型
 */
export function getResourceTypeByPath(path: string): ResourceType | null {
  for (const [key, config] of Object.entries(RESOURCE_TYPES)) {
    if (config.path === path) {
      return key as ResourceType
    }
  }
  return null
}
