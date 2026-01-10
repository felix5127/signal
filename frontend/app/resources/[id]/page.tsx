// Input: resource_id (路由参数)
// Output: 资源详情页面（服务端组件，异步加载数据）
// Position: 详情页入口，在服务端获取数据后渲染 ResourceDetail 组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import { notFound } from 'next/navigation'
import ResourceDetail from '@/components/resource-detail'

interface Resource {
  id: number
  type: string
  source_name: string
  source_icon_url?: string
  url: string
  title: string
  title_translated?: string
  author?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  summary_zh?: string
  content_markdown?: string
  domain?: string
  subdomain?: string
  tags?: string[]
  score?: number
  is_featured?: boolean
  language?: string
  word_count?: number
  read_time?: number
  duration?: number
  published_at?: string
  created_at?: string
  analyzed_at?: string
  main_points?: Array<{ point: string; explanation: string }>
  main_points_zh?: Array<{ point: string; explanation: string }>
  key_quotes?: string[]
  key_quotes_zh?: string[]
}

export default async function ResourceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  // 服务端直接 fetch 数据
  const apiUrl = process.env.INTERNAL_API_URL || 'http://localhost:8000'
  const res = await fetch(`${apiUrl}/api/resources/${id}`, {
    cache: 'no-store',
  })

  if (!res.ok) {
    notFound()
  }

  const resource: Resource = await res.json()

  return <ResourceDetail resource={resource} />
}
