/**
 * [INPUT]: 依赖 @/components/research 的工作台组件
 * [OUTPUT]: 对外提供研究项目工作台页面
 * [POS]: /research/workspace/[projectId] 路由页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const WorkspaceContent = dynamicImport(
  () => import('@/components/research/workspace'),
  { ssr: false }
)

export default function WorkspacePage({
  params,
}: {
  params: { projectId: string }
}) {
  return <WorkspaceContent projectId={params.projectId} />
}
