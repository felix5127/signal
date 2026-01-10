/**
 * [INPUT]: 后端 API 响应数据
 * [OUTPUT]: 统一的 Resource 类型定义，导出给所有组件使用
 * [POS]: 类型定义中心，确保前后端类型一致性
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

/**
 * 统一的资源类型定义
 *
 * 命名规范：
 * - 统一使用 score（废弃 final_score）
 * - 统一使用 domain（废弃 category）
 * - 统一使用 source_name（废弃 source）
 * - 统一使用 one_sentence_summary（废弃 one_liner）
 */

export interface Resource {
  // 基础信息
  id: number
  type: 'article' | 'podcast' | 'tweet' | 'video'
  source_name: string  // 统一使用 source_name
  url: string

  // 标题与摘要
  title: string
  title_translated?: string
  one_sentence_summary: string  // 统一使用 one_sentence_summary
  one_sentence_summary_zh?: string
  summary?: string
  summary_zh?: string

  // 分析结果
  main_points?: Array<{ point: string; explanation: string }>
  main_points_zh?: Array<{ point: string; explanation: string }>
  key_quotes?: string[]
  key_quotes_zh?: string[]

  // 分类与评分
  domain: string  // 统一使用 domain（一级分类）
  subdomain?: string  // 二级分类（仅AI领域）
  tags?: string[]
  score: number  // 统一使用 score（0-100）
  is_featured?: boolean

  // 元信息
  author?: string
  language?: 'zh' | 'en'
  word_count?: number
  read_time?: number
  duration?: number  // 播客/视频时长（秒）

  // 来源图标
  source_icon_url?: string

  // 时间
  published_at?: string
  created_at?: string
  analyzed_at?: string
  updated_at?: string

  // 状态
  status?: 'pending' | 'analyzing' | 'published' | 'failed'
}

// 兼容旧代码的类型别名（逐步废弃）
export type ResourceLegacy = Omit<Resource, 'source_name' | 'domain' | 'score' | 'one_sentence_summary'> & {
  source?: string
  category?: string
  final_score?: number
  one_liner?: string
}

// 响应类型
export interface ResourceListResponse {
  items: Resource[]
  total: number
  page: number
  pageSize: number
}

export interface ResourceDetail extends Resource {
  content_markdown?: string
  content_html?: string
  transcript?: string
  audio_url?: string
  metadata?: Record<string, unknown>
}

// 筛选参数类型
export interface ResourceFilters {
  type?: Resource['type']
  domain?: string
  lang?: 'zh' | 'en'
  timeFilter?: '1d' | '1w' | '1m' | '3m' | '1y'
  minScore?: number
  sort?: 'default' | 'time' | 'score'
  featured?: boolean
  q?: string  // 搜索关键词
  source?: string  // 来源筛选
}

// 类型转换工具（用于迁移期）
export function normalizeResource(data: any): Resource {
  return {
    ...data,
    source_name: data.source_name ?? data.source ?? '',
    domain: data.domain ?? data.category ?? '',
    score: data.score ?? data.final_score ?? 0,
    one_sentence_summary: data.one_sentence_summary ?? data.one_liner ?? '',
  }
}
