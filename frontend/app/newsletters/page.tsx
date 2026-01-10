// Input: Backend API (GET /api/newsletters)
// Output: 周刊列表页面，展示所有周刊卡片（带动效）
// Position: 周刊列表页，服务端渲染 + 响应式网格布局 + Framer Motion 动画
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import Link from 'next/link'
import { Star, BarChart3 } from 'lucide-react'

// 周刊数据类型
interface Newsletter {
  id: number
  title: string
  year: number
  week_number: number
  published_at: string
  created_at: string
  resource_count: number
  featured_count: number
  preview: string
}

interface ApiResponse {
  items: Newsletter[]
  total: number
  page: number
  page_size: number
}

// 服务端获取周刊列表
async function getNewsletters(): Promise<ApiResponse> {
  const apiUrl = process.env.INTERNAL_API_URL || 'http://signal-backend:8000'
  const res = await fetch(`${apiUrl}/api/newsletters?page_size=50`, {
    cache: 'no-store',
  })

  if (!res.ok) {
    throw new Error('Failed to fetch newsletters')
  }

  return res.json()
}

export default async function NewslettersPage() {
  const data = await getNewsletters()
  const { items } = data

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            📰 技术周刊
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            每周五自动生成，筛选本周最值得阅读的技术情报
          </p>
        </div>

        {/* 周刊卡片网格 */}
        {items.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              暂无周刊，敬请期待...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map((nl) => (
              <Link key={nl.id} href={`/newsletters/${nl.id}`} className="block h-full">
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-xl transition-all duration-200 border border-gray-100 dark:border-gray-700 h-full flex flex-col group">
                  {/* 标题 */}
                  <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
                    {nl.title}
                  </h3>

                  {/* 日期 */}
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                    📅 {new Date(nl.published_at).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>

                  {/* 预览 */}
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3 flex-grow">
                    {nl.preview}
                  </p>

                  {/* 统计信息 */}
                  <div className="flex justify-between text-sm pt-4 border-t border-gray-100 dark:border-gray-700">
                    <span className="text-gray-700 dark:text-gray-300 flex items-center gap-1">
                      <BarChart3 className="w-3 h-3" />
                      {nl.resource_count}篇收录
                    </span>
                    <span className="text-yellow-600 dark:text-yellow-400 font-semibold flex items-center gap-1">
                      <Star className="w-3 h-3 fill-current" />
                      {nl.featured_count}篇精选
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* 底部说明 */}
        <div className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>周刊由 AI 自动生成，每周五 17:00 发布</p>
          <p className="mt-1">收录评分 ≥ 70 的优质技术信号，精选评分 ≥ 85 的重磅内容</p>
        </div>
      </div>
    </div>
  )
}
