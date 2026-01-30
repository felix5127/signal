'use client'

/**
 * ResourceListPage - Mercury 风格资源列表页面
 * 特点: 简洁页头 + 分类筛选标签 + 文章卡片列表 + 分页导航
 * 设计规范: 背景 #FBFCFD, 主色调 #1E3A5F, 16px 圆角
 */

import { useState, useEffect, useCallback } from 'react'
import { RESOURCE_TYPES, type ResourceType } from '@/lib/resource-types'
import { Pagination } from '@/components/pagination'
import { cn } from '@/lib/utils'

export interface Resource {
  id: number
  type: string
  title: string
  title_translated?: string
  description?: string
  url: string
  author?: string
  source?: string
  source_name?: string
  source_icon_url?: string
  thumbnail_url?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  summary_zh?: string
  content_markdown?: string
  domain?: string
  subdomain?: string
  tags?: string[]
  score?: number
  final_score?: number
  is_featured?: boolean
  word_count?: number
  read_time?: number
  duration?: number
  published_at?: string
  created_at?: string
  metadata?: Record<string, any>
}

interface ApiResponse {
  items: Resource[]
  total: number
  limit: number
  offset: number
}

interface ResourceListPageProps {
  resourceType: ResourceType
  CardComponent: React.ComponentType<{ resource: Resource }>
  pageTitle?: string
  pageSubtitle?: string
  wideLayout?: boolean
}

// 分类筛选标签配置
const CATEGORY_FILTERS = [
  { value: '', label: '全部' },
  { value: '人工智能', label: 'AI-ML' },
  { value: '软件编程', label: '开发工具' },
  { value: '商业科技', label: 'Web3' },
] as const

/**
 * 获取 API 地址
 */
function getApiUrl(): string {
  return process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : '/api'
}

/**
 * 资源列表页面组件
 *
 * 包含页面标题、分类筛选和文章列表
 */
export function ResourceListPage({
  resourceType,
  CardComponent,
  pageTitle,
  pageSubtitle,
  wideLayout = false,
}: ResourceListPageProps) {
  const config = RESOURCE_TYPES[resourceType]
  const pageSize = 20

  // 根据 wideLayout 决定容器宽度
  const containerClass = wideLayout ? 'max-w-6xl' : 'max-w-4xl'

  // 状态管理
  const [categoryFilter, setCategoryFilter] = useState('')
  const [resources, setResources] = useState<Resource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  /**
   * 获取资源数据
   */
  const fetchResources = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const apiUrl = getApiUrl()

      const params = new URLSearchParams({
        page: currentPage.toString(),
        pageSize: pageSize.toString(),
        sort: 'default',
        type: resourceType,
      })

      if (categoryFilter) params.set('domain', categoryFilter)

      const response = await fetch(`${apiUrl}/resources?${params.toString()}`)
      if (!response.ok) throw new Error(`API 请求失败: ${response.status}`)

      const data: ApiResponse = await response.json()

      setResources(data.items)
      setTotalItems(data.total)
      setTotalPages(Math.ceil(data.total / pageSize))
    } catch (err) {
      console.error('获取资源失败:', err)
      setError(err instanceof Error ? err.message : '获取数据失败')
      setResources([])
    } finally {
      setLoading(false)
    }
  }, [currentPage, categoryFilter, resourceType, pageSize])

  /**
   * 处理分类筛选变化
   */
  const handleCategoryChange = useCallback((value: string) => {
    setCategoryFilter(value)
    setCurrentPage(1)
  }, [])

  /**
   * 处理页码变化
   */
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
    // 滚动到页面顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  // 获取数据
  useEffect(() => {
    fetchResources()
  }, [fetchResources])

  // 默认标题和副标题
  const displayTitle = pageTitle || config.label
  const displaySubtitle = pageSubtitle || config.description

  return (
    <div className="min-h-screen bg-[#FBFCFD]">
      {/* 页面头部 */}
      <header className="pt-8 pb-6">
        <div className={cn(containerClass, "mx-auto px-4 sm:px-6 lg:px-8")}>
          <h1 className="text-[28px] md:text-[32px] font-semibold text-[#272735] tracking-tight">
            {displayTitle}
          </h1>
          <p className="mt-2 text-[15px] text-[#6B6B6B]">
            {displaySubtitle}
          </p>
        </div>
      </header>

      {/* 分类筛选标签 */}
      <div className="pb-6">
        <div className={cn(containerClass, "mx-auto px-4 sm:px-6 lg:px-8")}>
          <div className="flex items-center gap-3 flex-wrap">
            {CATEGORY_FILTERS.map((filter) => {
              const isActive = categoryFilter === filter.value
              return (
                <button
                  key={filter.value}
                  onClick={() => handleCategoryChange(filter.value)}
                  className={cn(
                    'w-[80px] h-[36px] rounded-[16px] text-[14px] font-medium',
                    'transition-all duration-200',
                    'flex items-center justify-center',
                    isActive
                      ? 'bg-[#1E3A5F] text-white'
                      : 'bg-white text-[#6B6B6B] border border-[#E5E5E5] hover:border-[#1E3A5F] hover:text-[#1E3A5F]'
                  )}
                >
                  {filter.label}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className={cn(containerClass, "mx-auto px-4 sm:px-6 lg:px-8 pb-16")}>
        {/* 加载状态 */}
        {loading && resources.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-3 border-[#E5E5E5] border-t-[#1E3A5F] rounded-full animate-spin" />
            <p className="mt-4 text-[14px] text-[#9A9A9A]">加载中...</p>
          </div>
        )}

        {/* 错误状态 */}
        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center mb-4">
              <svg
                className="w-7 h-7 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h3 className="text-[16px] font-medium text-[#272735] mb-2">加载失败</h3>
            <p className="text-[14px] text-[#9A9A9A] mb-4">{error}</p>
          </div>
        )}

        {/* 空状态 */}
        {!loading && !error && resources.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-14 h-14 rounded-full bg-[#F6F5F2] flex items-center justify-center mb-4">
              <svg
                className="w-7 h-7 text-[#9A9A9A]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                />
              </svg>
            </div>
            <h3 className="text-[16px] font-medium text-[#272735] mb-2">暂无数据</h3>
            <p className="text-[14px] text-[#9A9A9A] text-center">
              当前筛选条件下没有找到资源
            </p>
          </div>
        )}

        {/* 资源列表 */}
        {!loading && !error && resources.length > 0 && (
          <>
            {/* 统计信息 */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-[13px] text-[#9A9A9A]">
                共 <span className="font-medium text-[#272735]">{totalItems}</span> 条结果
                {totalPages > 1 && (
                  <span className="ml-2">
                    · 第 <span className="font-medium text-[#272735]">{currentPage}</span> / {totalPages} 页
                  </span>
                )}
              </p>
            </div>

            {/* 资源卡片列表 */}
            {config.layout === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {resources.map((resource) => (
                  <CardComponent key={resource.id} resource={resource} />
                ))}
              </div>
            ) : (
              /* 设计稿: 推文列表白色卡片容器 + 16px圆角 + 边框 */
              <div className="bg-white rounded-2xl border border-[#E8E5E0] overflow-hidden">
                {resources.map((resource) => (
                  <CardComponent key={resource.id} resource={resource} />
                ))}
              </div>
            )}

            {/* 分页导航 */}
            {totalPages > 1 && (
              <div className="mt-8 pb-4">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
