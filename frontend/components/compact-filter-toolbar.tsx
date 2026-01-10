// Input: 筛选状态、筛选更新回调、搜索回调
// Output: 工具栏式筛选器 UI（Linear/Raycast 风格）
// Position: 首页搜索区下方，单行工具栏布局
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState } from 'react'
import { Clock, Tag, Star, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SearchBox } from './search-box'

// 导出类型供外部使用
export type FilterState = {
  timeFilter: TimeFilter
  domainFilter: DomainFilter
  langFilter: LanguageFilter
  scoreFilter: ScoreFilter
  sourceFilter: string
  sortBy: SortOption
  featuredOnly: boolean
  searchKeyword: string
}

export type TimeFilter = '' | '1d' | '1w' | '1m' | '3m' | '1y'
export type DomainFilter = '' | '软件编程' | '人工智能' | '产品设计' | '商业科技'
export type LanguageFilter = '' | 'zh' | 'en'
export type ScoreFilter = '' | '9.0' | '8.5' | '7.5'
export type SortOption = 'default' | 'time' | 'score'

// 重新导出类型
export const TIME_FILTERS = [
  { value: '', label: '全部时间' },
  { value: '1d', label: '1天' },
  { value: '1w', label: '1周' },
  { value: '1m', label: '1月' },
  { value: '3m', label: '3月' },
  { value: '1y', label: '1年' },
] as const

export const DOMAIN_FILTERS = [
  { value: '', label: '全部分类' },
  { value: '软件编程', label: '软件编程' },
  { value: '人工智能', label: '人工智能' },
  { value: '产品设计', label: '产品设计' },
  { value: '商业科技', label: '商业科技' },
] as const

export const LANGUAGE_FILTERS = [
  { value: '', label: '全部语言' },
  { value: 'zh', label: '仅中文' },
  { value: 'en', label: '仅英文' },
] as const

export const SCORE_FILTERS = [
  { value: '', label: '全部评分' },
  { value: '9.0', label: '9.0+ 推荐' },
  { value: '8.5', label: '8.5+ 值得读' },
  { value: '7.5', label: '7.5+ 基础' },
] as const

export const SORT_OPTIONS = [
  { value: 'default', label: '默认排序' },
  { value: 'time', label: '最新时间' },
  { value: 'score', label: '最高评分' },
] as const

interface CompactFilterToolbarProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onSearch: (keyword: string) => void
  searchLoading?: boolean
  className?: string
}

// 下拉菜单按钮组件 - 使用 Lucide 图标
function FilterDropdown({
  icon: Icon,
  label,
  value,
  options,
  onChange,
  isActive
}: {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  label: string
  value: string
  options: readonly { value: string; label: string }[]
  onChange: (value: string) => void
  isActive: boolean
}) {
  const [isOpen, setIsOpen] = useState(false)

  const selectedOption = options.find(opt => opt.value === value)
  const displayLabel = selectedOption?.label || label

  const handleSelect = (newValue: string) => {
    onChange(newValue)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-lg text-[15px] font-medium transition-all',
          'hover:bg-slate-100/80',
          isActive
            ? 'bg-white/50 backdrop-blur-md ring-1 ring-black/5 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.5)] text-purple-700'
            : 'text-slate-600'
        )}
      >
        <Icon className={cn('w-4 h-4', isActive ? 'text-purple-600' : 'text-slate-400')} />
        <span>{label}:</span>
        <span className={cn(
          'font-medium',
          isActive && 'text-purple-700'
        )}>
          {displayLabel}
        </span>
        <svg
          className={cn(
            'w-4 h-4 transition-transform',
            isActive ? 'text-purple-400' : 'text-slate-400',
            isOpen && 'transform rotate-180'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* 遮罩层 */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* 下拉菜单 */}
          <div className="absolute top-full left-0 mt-2 z-50 min-w-[200px] bg-white rounded-lg shadow-xl border border-slate-200 py-1">
            {options.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={cn(
                  'w-full px-4 py-2 text-sm text-left transition-colors',
                  'hover:bg-slate-50',
                  value === option.value
                    ? 'bg-violet-50 text-violet-700 font-medium'
                    : 'text-slate-700'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export function CompactFilterToolbar({
  filters,
  onFiltersChange,
  onSearch,
  searchLoading,
  className
}: CompactFilterToolbarProps) {
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className={cn('flex flex-col gap-6', className)}>
      {/* 搜索框 - 居中、无阴影 */}
      <div className="flex justify-center">
        <SearchBox
          value={filters.searchKeyword}
          onSearch={onSearch}
          loading={searchLoading}
          placeholder="搜索标题、摘要、标签..."
          className="max-w-2xl w-full"
        />
      </div>

      {/* 工具栏 - 单行水平布局 */}
      <div className="flex items-center justify-center gap-2 flex-wrap">
        {/* 时间筛选 */}
        <FilterDropdown
          icon={Clock}
          label="时间"
          value={filters.timeFilter}
          options={TIME_FILTERS}
          onChange={(value) => updateFilter('timeFilter', value as TimeFilter)}
          isActive={filters.timeFilter !== ''}
        />

        {/* 分类筛选 */}
        <FilterDropdown
          icon={Tag}
          label="分类"
          value={filters.domainFilter}
          options={DOMAIN_FILTERS}
          onChange={(value) => updateFilter('domainFilter', value as DomainFilter)}
          isActive={filters.domainFilter !== ''}
        />

        {/* 评分筛选 */}
        <FilterDropdown
          icon={Star}
          label="评分"
          value={filters.scoreFilter}
          options={SCORE_FILTERS}
          onChange={(value) => updateFilter('scoreFilter', value as ScoreFilter)}
          isActive={filters.scoreFilter !== ''}
        />

        {/* 来源筛选状态（可清除） */}
        {filters.sourceFilter && (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 rounded-lg">
            <span className="text-sm text-green-600">
              来源: {filters.sourceFilter}
            </span>
            <button
              onClick={() => updateFilter('sourceFilter', '')}
              className="text-green-400 hover:text-green-600"
              aria-label="清除来源筛选"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
