// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'
/**
 * [INPUT]: 依赖 Next.js not-found 边界、lucide-react 图标、Button 组件
 * [OUTPUT]: 自定义 404 错误页面
 * [POS]: app/ 的全局错误处理页面，处理未匹配的路由
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import Link from 'next/link'
import { Home, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white">
      <div className="text-center px-4">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mt-4">页面未找到</h2>
        <p className="text-gray-600 mt-2">抱歉，您访问的页面不存在。</p>
        <Button asChild className="mt-6">
          <Link href="/">
            <Home className="w-4 h-4" />
            返回首页
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </div>
    </div>
  )
}
