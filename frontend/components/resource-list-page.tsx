'use client'

/**
 * [INPUT]: RESOURCE_TYPES配置, 卡片组件, 筛选器组件
 * [OUTPUT]: 标准化的资源列表页面（包含筛选器、无限滚动、错误处理）
 * [POS]: components/ 的基础列表页模板，被 /articles /podcasts /tweets /videos 路由消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { useState, useEffect, useCallback } from 'react'
import type { FilterState, TimeFilter, SortOption } from '@/components/compact-filter-toolbar'
import { RESOURCE_TYPES, type ResourceType } from '@/lib/resource-types'
import { CompactFilterToolbar } from '@/components/compact-filter-toolbar'
import { InfiniteScroll } from '@/components/infinite-scroll'
import { cn } from '@/lib/utils'

export interface Resource {
  id: number
  type: string
  title: string
  description: string
  url: string
  author?: string
  published_at?: string
  created_at: string
  final_score?: number
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
}

/**
 * 计算时间范围
 */
function getTimeRange(filter: TimeFilter): Date | null {
  const now = new Date()
  switch (filter) {
    case '1d':
      return new Date(now.getTime() - 24 * 60 * 60 * 1000)
    case '1w':
      return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    case '1m':
      return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    case '3m':
      return new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
    case '1y':
      return new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
    default:
      return null
  }
}

/**
 * 获取排序参数
 */
function getSortParam(sortBy: SortOption): string {
  switch (sortBy) {
    case 'time':
      return 'created_at'
    case 'score':
      return 'final_score'
    default:
      return 'created_at'
  }
}

/**
 * 获取 API 地址（直接访问后端）
 */
function getApiUrl(): string {
  // 开发环境直接访问后端，绕过 Next.js 代理
  return process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : '/api'
}

/**
 * 资源列表页面组件
 *
 * 基础列表页模板，封装了筛选器、无限滚动、错误处理等所有逻辑
 * 4个独立页面通过配置复用此组件
 */
export function ResourceListPage({
  resourceType,
  CardComponent,
}: ResourceListPageProps) {
  const config = RESOURCE_TYPES[resourceType]
  const pageSize = 12

  // 状态管理
  const [filters, setFilters] = useState<FilterState>({
    timeFilter: '1m',
    domainFilter: '',
    langFilter: '',
    scoreFilter: '',
    sourceFilter: '',
    sortBy: 'default',
    featuredOnly: false,
    searchKeyword: '',
  })

  const [resources, setResources] = useState<Resource[]>([])
  const [loading, setLoading] = useState(true)
  const [searchLoading, setSearchLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  /**
   * 获取资源数据（普通列表或搜索）
   */
  const fetchResources = useCallback(async (isLoadMore: boolean = false) => {
    const isSearchMode = filters.searchKeyword.trim() !== ''

    // 根据是否加载更多设置加载状态
    if (isLoadMore) {
      setIsLoadingMore(true)
    } else {
      if (isSearchMode) {
        setSearchLoading(true)
      } else {
        setLoading(true)
      }
    }

    // 第一页时重置状态
    if (currentPage === 1 && !isLoadMore) {
      setResources([])
      setHasMore(true)
    }

    setError(null)

    try {
      const apiUrl = getApiUrl()

      let response: Response
      let data: ApiResponse

      if (isSearchMode) {
        // 搜索模式
        const params = new URLSearchParams({
          q: filters.searchKeyword.trim(),
          page: currentPage.toString(),
          pageSize: pageSize.toString(),
          sort: filters.sortBy,
          type: resourceType,
        })

        if (filters.domainFilter) params.set('domain', filters.domainFilter)
        if (filters.langFilter) params.set('lang', filters.langFilter)
        if (filters.sourceFilter) params.set('source', filters.sourceFilter)
        if (filters.scoreFilter) params.set('minScore', filters.scoreFilter)
        if (filters.timeFilter) params.set('timeFilter', filters.timeFilter)

        response = await fetch(`${apiUrl}/api/resources/search?${params.toString()}`)
        if (!response.ok) throw new Error(`搜索请求失败: ${response.status}`)

        const searchData = await response.json()
        data = {
          items: searchData.items,
          total: searchData.total,
          limit: searchData.pageSize,
          offset: (searchData.page - 1) * searchData.pageSize,
        }
      } else {
        // 普通列表模式
        const params = new URLSearchParams({
          page: currentPage.toString(),
          pageSize: pageSize.toString(),
          sort: filters.sortBy,
          type: resourceType,
        })

        // 时间过滤：只有非空时才发送（空字符串表示"全部时间"）
        if (filters.timeFilter) params.set('timeFilter', filters.timeFilter)
        if (filters.domainFilter) params.set('domain', filters.domainFilter)
        if (filters.langFilter) params.set('lang', filters.langFilter)
        if (filters.sourceFilter) params.set('source', filters.sourceFilter)
        if (filters.scoreFilter) params.set('minScore', filters.scoreFilter)
        if (filters.featuredOnly) params.set('featured', 'true')

        response = await fetch(`${apiUrl}/resources?${params.toString()}`)
        if (!response.ok) throw new Error(`API 请求失败: ${response.status}`)

        data = await response.json()
      }

      // 根据页码决定是替换还是追加数据
      if (currentPage === 1 || !isLoadMore) {
        setResources(data.items)
      } else {
        setResources(prev => [...prev, ...data.items])
      }

      setTotalItems(data.total)
      setHasMore(data.items.length === pageSize)
    } catch (err) {
      console.error('获取资源失败:', err)
      setError(err instanceof Error ? err.message : '获取数据失败')
      setResources([])
    } finally {
      setLoading(false)
      setSearchLoading(false)
      setIsLoadingMore(false)
    }
  }, [currentPage, filters, resourceType, pageSize])

  /**
   * 处理搜索
   */
  const handleSearch = useCallback((keyword: string) => {
    setFilters((prev: FilterState) => ({ ...prev, searchKeyword: keyword }))
    setCurrentPage(1)
  }, [])

  /**
   * 加载更多
   */
  const loadMore = useCallback(() => {
    if (hasMore && !loading && !isLoadingMore) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
    }
  }, [hasMore, loading, isLoadingMore, currentPage])

  /**
   * 刷新数据
   */
  const refresh = useCallback(() => {
    setCurrentPage(1)
    setResources([])
    setHasMore(true)
  }, [])

  // 监听筛选变化
  useEffect(() => {
    if (currentPage === 1) {
      fetchResources(false)
    }
  }, [filters, resourceType, currentPage, fetchResources])

  // 获取数据
  useEffect(() => {
    const isLoadMore = currentPage > 1
    fetchResources(isLoadMore)
  }, [currentPage, fetchResources])

  return (
    <div className="min-h-screen bg-white">
      {/* 筛选工具栏 */}
      <div className="mb-8 flex justify-center">
        <div className="w-full max-w-2xl">
          <CompactFilterToolbar
            filters={filters}
            onFiltersChange={setFilters}
            onSearch={handleSearch}
            searchLoading={loading}
          />
        </div>
      </div>

      {/* 加载状态 */}
      {loading && resources.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      )}

      {/* 错误状态 */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8 text-red-500"
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
          <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
          <p className="text-gray-500 mb-4">{error}</p>
        </div>
      )}

      {/* 空状态 */}
      {!loading && !error && resources.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8 text-gray-400"
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
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {filters.searchKeyword ? '未找到匹配结果' : '暂无数据'}
          </h3>
          <p className="text-gray-500 text-center">
            {filters.searchKeyword
              ? `没有找到包含 "${filters.searchKeyword}" 的资源，请尝试其他关键词`
              : '当前筛选条件下没有找到资源'}
          </p>
        </div>
      )}

      {/* 资源列表 */}
      {!loading && !error && resources.length > 0 && (
        <>
          {/* 统计信息 */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              共 <span className="font-medium text-gray-900">{resources.length}</span> 条结果
            </p>
          </div>

          {/* 无限滚动容器 */}
          <InfiniteScroll hasMore={hasMore} isLoading={loading} onLoadMore={loadMore}>
            <div
              className={cn(
                config.layout === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                  : '-mx-4'
              )}
            >
              {resources.map((resource) => (
                <CardComponent key={resource.id} resource={resource} />
              ))}
            </div>
          </InfiniteScroll>
        </>
      )}
    </div>
  )
}
