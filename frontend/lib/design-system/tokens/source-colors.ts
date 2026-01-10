/**
 * [INPUT]: 来源标识符
 * [OUTPUT]: Tailwind CSS 类名
 * [POS]: 设计系统颜色令牌，统一来源颜色
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

/**
 * 来源颜色映射
 * 移除硬编码，使用 CSS 变量和 Tailwind 类
 */

export const SOURCE_COLORS = {
  hn: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400 border-orange-200 dark:border-orange-800',
  github: 'bg-gray-50 text-gray-700 dark:bg-gray-800/50 dark:text-gray-300 border-gray-200 dark:border-gray-700',
  huggingface: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800',
  twitter: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  arxiv: 'bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 border-red-200 dark:border-red-800',
  producthunt: 'bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400 border-orange-200 dark:border-orange-800',
  blog: 'bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400 border-purple-200 dark:border-purple-800',
} as const

export type SourceType = keyof typeof SOURCE_COLORS

export function getSourceColor(source: string): string {
  return SOURCE_COLORS[source as SourceType] || SOURCE_COLORS.blog
}
