/**
 * [INPUT]: HomePageContent 客户端组件
 * [OUTPUT]: 产品介绍首页（服务端组件包装器）
 * [POS]: app/ 的根路由页面，强制动态渲染
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import dynamicImport from 'next/dynamic'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'
export const revalidate = 0

// 使用 dynamic import 禁用 SSR
const HomePageContent = dynamicImport(
  () => import('@/components/home-page-content'),
  { ssr: false }
)

export default function HomePage() {
  return <HomePageContent />
}
