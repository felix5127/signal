// Input: 用户交互（筛选条件变化、搜索关键词）
// Output: 筛选状态、搜索回调和回调函数
// Position: 首页筛选栏组件，BestBlogs风格，支持搜索
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { cn } from '@/lib/utils'
import { SearchBox } from './search-box'

// 时间筛选选项
export const TIME_FILTERS = [
  { value: '1d', label: '1天' },
  { value: '1w', label: '1周' },
  { value: '1m', label: '1月' },
  { value: '3m', label: '3月' },
  { value: '1y', label: '1年' },
] as const

// 分类筛选选项
export const DOMAIN_FILTERS = [
  { value: '', label: '全部' },
  { value: '软件编程', label: '软件编程' },
  { value: '人工智能', label: '人工智能' },
  { value: '产品设计', label: '产品设计' },
  { value: '商业科技', label: '商业科技' },
] as const

// 语言筛选选项（Phase 1.5 新增）
export const LANGUAGE_FILTERS = [
  { value: '', label: '全部语言' },
  { value: 'zh', label: '仅中文' },
  { value: 'en', label: '仅英文' },
] as const

// 评分筛选选项（Phase 1.5 新增）
export const SCORE_FILTERS = [
  { value: '', label: '全部评分' },
  { value: '9.0', label: '9.0+ 推荐' },
  { value: '8.5', label: '8.5+ 值得读' },
  { value: '7.5', label: '7.5+ 基础' },
] as const

// 排序选项
export const SORT_OPTIONS = [
  { value: 'default', label: '默认' },
  { value: 'time', label: '时间' },
  { value: 'score', label: '评分' },
] as const

export type TimeFilter = typeof TIME_FILTERS[number]['value']
export type DomainFilter = typeof DOMAIN_FILTERS[number]['value']
export type LanguageFilter = typeof LANGUAGE_FILTERS[number]['value']
export type ScoreFilter = typeof SCORE_FILTERS[number]['value']
export type SortOption = typeof SORT_OPTIONS[number]['value']

export interface FilterState {
  timeFilter: TimeFilter
  domainFilter: DomainFilter
  langFilter: LanguageFilter // Phase 1.5 新增
  scoreFilter: ScoreFilter // Phase 1.5 新增
  sourceFilter: string // Phase 1.5 新增
  sortBy: SortOption
  featuredOnly: boolean
  searchKeyword: string
}

interface FilterBarProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onSearch: (keyword: string) => void
  searchLoading?: boolean
  className?: string
}

export function FilterBar({ filters, onFiltersChange, onSearch, searchLoading, className }: FilterBarProps) {
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div
      className={cn(
        'flex flex-col gap-4 py-4 border-b',
        'border-[var(--ds-border)]',
        className
      )}
    >
      {/* 搜索栏 */}
      <SearchBox
        value={filters.searchKeyword}
        onSearch={onSearch}
        loading={searchLoading}
        placeholder="搜索标题、摘要、标签..."
        className="w-full md:max-w-md"
      />

      {/* 第一行筛选：时间 + 分类 + 语言 + 评分 */}
      <div className="flex flex-wrap items-center gap-3">
        {/* 时间筛选 */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {TIME_FILTERS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('timeFilter', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.timeFilter === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-[var(--ds-border-2)] hidden sm:block" />

        {/* 分类筛选 */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {DOMAIN_FILTERS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('domainFilter', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.domainFilter === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-[var(--ds-border-2)] hidden sm:block" />

        {/* 排序 */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {SORT_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('sortBy', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.sortBy === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-[var(--ds-border-2)] hidden sm:block" />

        {/* 语言筛选（Phase 1.5 新增） */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {LANGUAGE_FILTERS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('langFilter', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.langFilter === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-[var(--ds-border-2)] hidden sm:block" />

        {/* 评分筛选（Phase 1.5 新增） */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {SCORE_FILTERS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('scoreFilter', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.scoreFilter === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* 第二行筛选：排序 + 精选 + 来源清除 */}
      <div className="flex flex-wrap items-center gap-3">
        {/* 排序 */}
        <div className="flex items-center gap-1 bg-[var(--ds-surface-2)] rounded-2xl p-1">
          {SORT_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => updateFilter('sortBy', option.value)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-xl transition-all',
                filters.sortBy === option.value
                  ? 'bg-[var(--ds-bg)] text-[var(--ds-fg)] shadow-sm'
                  : 'text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-[var(--ds-border-2)] hidden sm:block" />

        {/* 精选开关 */}
        <button
          onClick={() => updateFilter('featuredOnly', !filters.featuredOnly)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-2xl text-sm font-medium transition-all',
            filters.featuredOnly
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md'
              : 'bg-[var(--ds-surface-2)] text-[var(--ds-muted)] hover:text-[var(--ds-fg)]'
          )}
        >
          <svg
            className={cn(
              'w-4 h-4 transition-transform',
              filters.featuredOnly && 'scale-110'
            )}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          精选
        </button>

        {/* 来源筛选状态（Phase 1.5 新增） */}
        {filters.sourceFilter && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/30 rounded-2xl">
            <span className="text-sm text-green-600 dark:text-green-400">
              来源: &ldquo;{filters.sourceFilter}&rdquo;
            </span>
            <button
              onClick={() => updateFilter('sourceFilter', '')}
              className="text-green-400 hover:text-green-600 dark:hover:text-green-300"
              aria-label="清除来源筛选"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* 搜索状态提示 */}
        {filters.searchKeyword && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-900/30 rounded-2xl">
            <span className="text-sm text-indigo-600 dark:text-indigo-400">
              搜索: &ldquo;{filters.searchKeyword}&rdquo;
            </span>
            <button
              onClick={() => onSearch('')}
              className="text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-300"
              aria-label="清除搜索"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
