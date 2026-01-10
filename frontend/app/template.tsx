/**
 * [INPUT]: 依赖 PageTransition 组件、子页面 children
 * [OUTPUT]: 对外提供路由级页面过渡包装器
 * [POS]: app/ 模板文件，对每个页面单独渲染，实现路由切换动画
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import PageTransition from '@/components/page-transition'

export default function Template({ children }: { children: React.ReactNode }) {
  return <PageTransition>{children}</PageTransition>
}
