/**
 * [INPUT]: resource_id (路由参数)
 * [OUTPUT]: 资源详情页面（服务端组件，异步加载数据）
 * [POS]: 详情页入口，根据资源类型渲染不同的详情组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { notFound } from 'next/navigation'
import ResourceDetail from '@/components/resource-detail'
import { PodcastDetail } from '@/components/podcast'
import type { Chapter } from '@/components/podcast'
import type { QAPair } from '@/components/podcast'

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
  featured_reason?: string
  featured_reason_zh?: string
  language?: string
  word_count?: number
  read_time?: number
  duration?: number
  audio_url?: string
  transcript?: string
  chapters?: Chapter[]
  qa_pairs?: QAPair[]
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

  // 根据类型渲染不同的详情组件
  if (resource.type === 'podcast') {
    return (
      <PodcastDetail
        resource={{
          ...resource,
          type: 'podcast' as const,
        }}
      />
    )
  }

  // 默认使用通用详情组件（文章/视频/推文）
  return <ResourceDetail resource={resource} />
}
