// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

/**
 * ArticlesPage - 文章列表页
 * 设计规范: Mercury.com 浅色系
 * - 背景色: #FBFCFD
 * - 主色调: #1E3A5F (深海军蓝)
 * - 文字色: #272735, #6B6B6B, #9A9A9A
 * - 圆角: 16px
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { ArticleListCard } from '@/components/article-list-card'

export default function ArticlesPage() {
  return (
    <ResourceListPage
      resourceType="article"
      CardComponent={ArticleListCard}
      pageTitle="文章"
      pageSubtitle="浏览最新文章，掌握技术动态"
    />
  )
}

export const metadata = {
  title: '技术文章 - Signal',
  description: '精选技术文章与深度解读，覆盖人工智能、软件编程、产品设计等领域',
}
