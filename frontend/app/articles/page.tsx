/**
 * [INPUT]: ResourceListPage基础组件, ArticleListCard卡片组件
 * [OUTPUT]: 文章列表页面（展示所有文章类型资源，支持筛选和搜索）
 * [POS]: app/articles/ 的路由页面，导航栏"文章"入口的目标页
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { ArticleListCard } from '@/components/article-list-card'

export default function ArticlesPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">技术文章</h1>
        <p className="text-muted-foreground">
          深度技术文章与研究成果，帮助您快速掌握前沿技术
        </p>
      </div>

      {/* 资源列表 */}
      <ResourceListPage resourceType="article" CardComponent={ArticleListCard} />
    </main>
  )
}

export const metadata = {
  title: '技术文章 - Signal Hunter',
  description: '精选技术文章与深度解读，覆盖人工智能、软件编程、产品设计等领域',
}
