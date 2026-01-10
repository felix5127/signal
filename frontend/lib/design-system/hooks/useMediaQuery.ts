// Input: 媒体查询字符串
// Output: 当前是否匹配该媒体查询
// Position: 响应式设计 Hook，用于检测屏幕尺寸
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState, useEffect } from 'react'

// ============ 预定义断点 ============
export const breakpoints = {
  xs: '(max-width: 480px)',
  sm: '(max-width: 640px)',
  md: '(max-width: 768px)',
  lg: '(max-width: 1024px)',
  xl: '(max-width: 1280px)',
  '2xl': '(max-width: 1536px)',

  // 最小宽度查询
  'min-sm': '(min-width: 640px)',
  'min-md': '(min-width: 768px)',
  'min-lg': '(min-width: 1024px)',
  'min-xl': '(min-width: 1280px)',
  'min-2xl': '(min-width: 1536px)',
}

// ============ 媒体查询 Hook ============
/**
 * 监听媒体查询匹配状态
 * @param query - 媒体查询字符串或预定义断点
 * @returns 是否匹配该媒体查询
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)')
 * const isTablet = useMediaQuery(breakpoints.md)
 * const isDesktop = useMediaQuery(breakpoints['min-lg'])
 */
export function useMediaQuery(query: string): boolean {
  // 预定义断点映射
  const resolvedQuery = breakpoints[query as keyof typeof breakpoints] || query

  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia(resolvedQuery).matches
  })

  useEffect(() => {
    if (typeof window === 'undefined') return

    const mediaQuery = window.matchMedia(resolvedQuery)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)

    // 现代浏览器使用 addEventListener
    mediaQuery.addEventListener('change', handler)

    return () => {
      mediaQuery.removeEventListener('change', handler)
    }
  }, [resolvedQuery])

  return matches
}

// ============ 便捷 Hooks ============

/**
 * 检测是否为移动设备 (≤ 768px)
 */
export function useIsMobile(): boolean {
  return useMediaQuery(breakpoints.md)
}

/**
 * 检测是否为平板设备 (768px - 1024px)
 */
export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 769px) and (max-width: 1024px)')
}

/**
 * 检测是否为桌面设备 (≥ 1024px)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(breakpoints['min-lg'])
}

/**
 * 获取当前屏幕尺寸类别
 */
export function useScreenSize(): 'mobile' | 'tablet' | 'desktop' {
  const isMobile = useIsMobile()
  const isTablet = useIsTablet()

  if (isMobile) return 'mobile'
  if (isTablet) return 'tablet'
  return 'desktop'
}

// ============ 默认导出 ============
export default useMediaQuery
