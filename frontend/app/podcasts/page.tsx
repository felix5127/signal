// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

/**
 * PodcastsPage - 播客列表页
 * 设计规范: Mercury.com 浅色系
 * - 背景色: #FBFCFD
 * - 主色调: #1E3A5F (深海军蓝)
 * - 文字色: #272735, #6B6B6B, #9A9A9A
 * - 圆角: 16px
 * - 播客卡片: 3列网格，带彩色缩略图和播放按钮
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { PodcastCard } from '@/components/podcast-card'

export default function PodcastsPage() {
  return (
    <ResourceListPage
      resourceType="podcast"
      CardComponent={PodcastCard}
      pageTitle="播客"
      pageSubtitle="收听行业专家访谈，了解技术前沿"
      wideLayout
    />
  )
}

export const metadata = {
  title: '技术播客 - Signal',
  description: '精选技术播客与访谈节目，涵盖人工智能、软件工程等领域',
}
