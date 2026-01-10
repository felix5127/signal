// Input: newsletter_id (路由参数)
// Output: 周刊详情页面（服务端组件，调用 API 获取周刊数据后渲染 Markdown）
// Position: 服务端页面入口，负责获取周刊数据，生成 SEO 元数据，渲染详情页
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md

import { notFound } from 'next/navigation'
import Link from 'next/link'
import { Metadata } from 'next'
import MarkdownRenderer from '@/components/markdown-renderer'
import { Star, BarChart3 } from 'lucide-react'

// 周刊详情类型
interface NewsletterDetail {
  id: number
  title: string
  year: number
  week_number: number
  content: string
  resource_ids: number[]
  published_at: string
  created_at: string
  resource_count: number
  featured_count: number
}

// 服务端获取周刊详情
async function getNewsletter(id: string): Promise<NewsletterDetail | null> {
  const apiUrl = process.env.INTERNAL_API_URL || 'http://signal-backend:8000'
  const res = await fetch(`${apiUrl}/api/newsletters/${id}`, {
    cache: 'no-store',
  })

  if (!res.ok) {
    return null
  }

  return res.json()
}

// 生成 SEO 元数据
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const newsletter = await getNewsletter(id)

  if (!newsletter) {
    return {
      title: '周刊未找到 - Signal Hunter',
    }
  }

  return {
    title: `${newsletter.title} - Signal Hunter`,
    description: `${newsletter.resource_count}篇收录，${newsletter.featured_count}篇精选`,
    openGraph: {
      title: newsletter.title,
      description: `${newsletter.resource_count}篇收录，${newsletter.featured_count}篇精选`,
      type: 'article',
    },
  }
}

export default async function NewsletterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const newsletter = await getNewsletter(id)

  if (!newsletter) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* 返回按钮 */}
        <Link
          href="/newsletters"
          className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline mb-8 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回周刊列表
        </Link>

        {/* 周刊头部信息 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 mb-8 shadow-lg border border-gray-100 dark:border-gray-700">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {newsletter.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-gray-600 dark:text-gray-400 mb-6">
            <span className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {new Date(newsletter.published_at).toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
            <span className="flex items-center">
              <BarChart3 className="w-4 h-4 mr-1" />
              {newsletter.resource_count}篇收录
            </span>
            <span className="flex items-center text-yellow-600 dark:text-yellow-400 font-semibold">
              <Star className="w-4 h-4 mr-1 fill-current" />
              {newsletter.featured_count}篇精选
            </span>
          </div>
        </div>

        {/* 周刊正文内容 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg border border-gray-100 dark:border-gray-700">
          <div className="prose prose-lg dark:prose-invert max-w-none">
            <MarkdownRenderer content={newsletter.content} />
          </div>
        </div>

        {/* 底部说明 */}
        <div className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>本周刊由 AI Signal Hunter 自动生成</p>
          <p className="mt-1">收录本周最值得阅读的技术情报</p>
        </div>
      </div>
    </div>
  )
}
