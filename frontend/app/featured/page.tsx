/**
 * [INPUT]: FeaturedPageContent 客户端组件
 * [OUTPUT]: 精选页面（服务端组件包装器）
 * [POS]: app/featured/ 的路由页面，强制动态渲染
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const FeaturedPageContent = dynamicImport(
  () => import('@/components/featured-page-content'),
  { ssr: false }
)

export default function FeaturedPage() {
  return <FeaturedPageContent />
}
