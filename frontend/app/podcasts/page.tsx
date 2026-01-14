// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'
/**
 * [INPUT]: ResourceListPage基础组件, ResourceCard卡片组件
 * [OUTPUT]: 播客列表页面（展示所有播客类型资源，支持筛选和搜索）
 * [POS]: app/podcasts/ 的路由页面，导航栏"播客"入口的目标页
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { ResourceCard } from '@/components/resource-card'

export default function PodcastsPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">技术播客</h1>
        <p className="text-muted-foreground">
          行业专家访谈与技术讨论，聆听前沿思考
        </p>
      </div>

      {/* 资源列表 */}
      <ResourceListPage resourceType="podcast" CardComponent={ResourceCard} />
    </main>
  )
}

export const metadata = {
  title: '技术播客 - Signal Hunter',
  description: '精选技术播客与访谈节目，涵盖人工智能、软件工程等领域',
}
