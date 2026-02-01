// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

/**
 * TweetsPage - 推文列表页
 * 设计规范: Mercury.com 浅色系
 * - 背景色: #FBFCFD
 * - 主色调: #1E3A5F (深海军蓝)
 * - 文字色: #272735, #6B6B6B, #9A9A9A
 * - 圆角: 16px
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { TweetCard } from '@/components/tweet-card'

export default function TweetsPage() {
  return (
    <ResourceListPage
      resourceType="tweet"
      CardComponent={TweetCard}
      pageTitle="推文"
      pageSubtitle="快速捕捉技术专家观点与行业动态"
    />
  )
}

export const metadata = {
  title: '精选推文 - Signal',
  description: 'Twitter技术专家观点分享，即时获取行业动态与思考',
}
