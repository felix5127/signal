// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'
/**
 * [INPUT]: ResourceListPage基础组件, TweetCard卡片组件
 * [OUTPUT]: 推文列表页面（展示所有推文类型资源，支持筛选和搜索）
 * [POS]: app/tweets/ 的路由页面，导航栏"推文"入口的目标页
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { TweetCard } from '@/components/tweet-card'

export default function TweetsPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">💬 精选推文</h1>
        <p className="text-muted-foreground">
          技术专家观点与即时思考，快速捕捉行业动态
        </p>
      </div>

      {/* 资源列表 */}
      <ResourceListPage resourceType="tweet" CardComponent={TweetCard} />
    </main>
  )
}

export const metadata = {
  title: '精选推文 - Signal Hunter',
  description: 'Twitter技术专家观点分享，即时获取行业动态与思考',
}
