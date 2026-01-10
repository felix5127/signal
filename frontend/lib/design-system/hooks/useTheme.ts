// Input: 无
// Output: 当前主题、主题切换函数
// Position: 主题管理 Hook，用于深色/浅色模式切换
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState, useEffect, useCallback } from 'react'

// ============ 类型定义 ============
export type Theme = 'light' | 'dark' | 'system'

export interface UseThemeReturn {
  /** 当前主题 */
  theme: Theme
  /** 实际应用的主题（system 模式下自动解析为 light/dark） */
  resolvedTheme: 'light' | 'dark'
  /** 设置主题 */
  setTheme: (theme: Theme) => void
  /** 切换 light/dark */
  toggleTheme: () => void
}

// ============ 主题 Hook ============
/**
 * 主题管理 Hook
 * 支持浅色/深色/系统默认三种模式
 *
 * @example
 * const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme()
 */
export function useTheme(): UseThemeReturn {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'system'

    // 从 localStorage 读取
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored && ['light', 'dark', 'system'].includes(stored)) {
      return stored
    }

    return 'system'
  })

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  // 更新 DOM class
  useEffect(() => {
    const root = document.documentElement

    // 移除旧的 class
    root.classList.remove('light', 'dark')

    // 确定实际应用的主题
    let actualTheme: 'light' | 'dark' = 'light'
    if (theme === 'system') {
      actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    } else {
      actualTheme = theme
    }

    // 添加新的 class
    root.classList.add(actualTheme)
    setResolvedTheme(actualTheme)

    // 更新 meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        actualTheme === 'dark' ? '#161818' : '#FFFFFF'
      )
    }
  }, [theme])

  // 监听系统主题变化
  useEffect(() => {
    if (theme !== 'system') return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      const newTheme = e.matches ? 'dark' : 'light'
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(newTheme)
      setResolvedTheme(newTheme)
    }

    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [theme])

  // 设置主题
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
  }, [])

  // 切换主题
  const toggleTheme = useCallback(() => {
    setThemeState((prev: Theme) => {
      if (prev === 'light') return 'dark'
      if (prev === 'dark') return 'light'
      // system 模式下根据当前系统主题切换
      return resolvedTheme === 'dark' ? 'light' : 'dark'
    })
  }, [resolvedTheme])

  return {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  }
}

// ============ 默认导出 ============
export default useTheme
