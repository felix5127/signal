/**
 * ArticleListCard - Mercury 风格文章列表卡片
 * 设计规范: 左侧彩色占位图 + 右侧内容
 * - 标签统一尺寸: 72px x 28px
 * - 圆角: 16px
 * - 主色调: #1E3A5F
 */
'use client'

import { cn } from '@/lib/utils'

export interface ArticleResource {
  id: number
  source?: string
  source_name?: string
  source_icon_url?: string
  thumbnail_url?: string
  url: string
  title: string
  title_translated?: string
  one_sentence_summary?: string
  one_sentence_summary_zh?: string
  summary?: string
  summary_zh?: string
  content_markdown?: string
  score?: number
  final_score?: number
  is_featured?: boolean
  domain?: string
  subdomain?: string
  tags?: string[]
  published_at?: string
  created_at?: string
  word_count?: number
  read_time?: number
}

interface ArticleListCardProps {
  resource: ArticleResource
  className?: string
}

// 域名对应的颜色配置
const DOMAIN_COLORS: Record<string, { bg: string; text: string; placeholder: string }> = {
  '人工智能': { bg: '#EEF2FF', text: '#4F46E5', placeholder: '#818CF8' },
  '软件编程': { bg: '#ECFDF5', text: '#059669', placeholder: '#34D399' },
  '商业科技': { bg: '#FEF3C7', text: '#D97706', placeholder: '#FBBF24' },
  '产品设计': { bg: '#FCE7F3', text: '#DB2777', placeholder: '#F472B6' },
}

const DEFAULT_COLOR = { bg: '#F3F4F6', text: '#6B7280', placeholder: '#9CA3AF' }

// 提取摘要内容的前两句
function getSummaryPreview(summary?: string): string {
  if (!summary) return ''

  const sentences = summary
    .replace(/([。！？\.!?])\s*/g, '$1|||')
    .split('|||')

  const contentLines: string[] = []
  for (const sentence of sentences) {
    const trimmed = sentence.trim()
    if (trimmed && trimmed.length > 2) {
      contentLines.push(trimmed)
      if (contentLines.length >= 2) break
    }
  }

  return contentLines.join('')
}

// 格式化日期
function formatDate(dateString?: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}

export function ArticleListCard({ resource, className }: ArticleListCardProps) {
  const displayTitle = resource.title_translated || resource.title

  const summaryText = resource.summary_zh || resource.summary || ''
  const displaySummary = getSummaryPreview(summaryText) ||
    resource.one_sentence_summary_zh ||
    resource.one_sentence_summary ||
    ''

  const sourceName = resource.source_name || (resource.source ? SOURCE_NAMES[resource.source] : undefined) || resource.source || 'Unknown'
  const domain = resource.domain || ''
  const displayTime = resource.published_at || resource.created_at

  // 获取域名对应的颜色
  const colorConfig = DOMAIN_COLORS[domain] || DEFAULT_COLOR

  return (
    <a
      href={`/resources/${resource.id}`}
      className={cn(
        'group flex gap-4 py-5',
        'border-b border-[#E5E5E5]',
        'hover:bg-[#FAFBFC]',
        'transition-colors duration-200',
        className
      )}
    >
      {/* 左侧：封面图 / 彩色占位图 */}
      <div
        className="flex-shrink-0 w-[100px] h-[80px] rounded-[12px] overflow-hidden flex items-center justify-center"
        style={{ backgroundColor: colorConfig.bg }}
      >
        {resource.thumbnail_url ? (
          <img
            src={resource.thumbnail_url}
            alt=""
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div
            className="w-10 h-10 rounded-[8px] opacity-60"
            style={{ backgroundColor: colorConfig.placeholder }}
          />
        )}
      </div>

      {/* 右侧：内容区域 */}
      <div className="flex-1 min-w-0 flex flex-col justify-between">
        {/* 上部：标签 + 标题 */}
        <div>
          {/* 标签行 */}
          <div className="flex items-center gap-2 mb-2">
            {/* 分类标签 */}
            {domain && (
              <span
                className="inline-flex items-center justify-center w-[72px] h-[28px] rounded-[8px] text-[12px] font-medium"
                style={{
                  backgroundColor: colorConfig.bg,
                  color: colorConfig.text
                }}
              >
                {domain === '人工智能' ? 'AI-ML' :
                 domain === '软件编程' ? '开发工具' :
                 domain === '商业科技' ? 'Web3' : domain}
              </span>
            )}
          </div>

          {/* 标题 */}
          <h3
            className={cn(
              'text-[16px] font-medium text-[#272735] leading-[1.4]',
              'group-hover:text-[#1E3A5F]',
              'transition-colors duration-200',
              'line-clamp-2'
            )}
          >
            {displayTitle}
          </h3>

          {/* 摘要 */}
          {displaySummary && (
            <p className="mt-1.5 text-[14px] text-[#6B6B6B] leading-[1.5] line-clamp-2">
              {displaySummary}
            </p>
          )}
        </div>

        {/* 下部：来源 + 日期 */}
        <div className="flex items-center gap-3 mt-3">
          <span className="text-[13px] text-[#9A9A9A]">
            {sourceName}
          </span>
          <span className="text-[13px] text-[#D4D4D4]">|</span>
          <span className="text-[13px] text-[#9A9A9A]">
            {formatDate(displayTime)}
          </span>
        </div>
      </div>
    </a>
  )
}
