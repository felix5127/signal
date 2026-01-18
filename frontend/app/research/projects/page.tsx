/**
 * [INPUT]: 依赖 @/components/research 的项目列表组件
 * [OUTPUT]: 对外提供研究项目列表页面
 * [POS]: /research/projects 路由页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const ProjectListContent = dynamicImport(
  () => import('@/components/research/project-list'),
  { ssr: false }
)

export default function ProjectListPage() {
  return <ProjectListContent />
}
