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
  // 已移除: hn, github, huggingface, arxiv, producthunt
  twitter: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  blog: 'bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400 border-purple-200 dark:border-purple-800',
  podcast: 'bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400 border-green-200 dark:border-green-800',
} as const

export type SourceType = keyof typeof SOURCE_COLORS

export function getSourceColor(source: string): string {
  return SOURCE_COLORS[source as SourceType] || SOURCE_COLORS.blog
}
