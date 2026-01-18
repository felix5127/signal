/**
 * [INPUT]: 无外部依赖
 * [OUTPUT]: 对外提供 Admin 后台通用工具函数
 * [POS]: lib/ 的 Admin 工具函数模块，被 components/admin/ 复用
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

// ========== 时间格式化 ==========

/**
 * 格式化 ISO 时间字符串为中文本地化格式
 * @param isoString - ISO 8601 格式的时间字符串
 * @param options - 可选的格式化选项
 * @returns 格式化后的字符串，如 "01/15 14:30"
 */
export function formatTime(
  isoString: string | null | undefined,
  options?: {
    showSeconds?: boolean
    showYear?: boolean
  }
): string {
  if (!isoString) return '-'

  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return '-'

    const formatOptions: Intl.DateTimeFormatOptions = {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }

    if (options?.showSeconds) {
      formatOptions.second = '2-digit'
    }

    if (options?.showYear) {
      formatOptions.year = 'numeric'
    }

    return date.toLocaleString('zh-CN', formatOptions)
  } catch {
    return '-'
  }
}

// ========== API 响应处理 ==========

/**
 * API 响应结果类型
 */
export interface ApiResult<T> {
  success: boolean
  data?: T
  error?: string
}

/**
 * 统一的 API 请求处理函数
 * @param url - 请求 URL
 * @param options - fetch 选项
 * @returns Promise<ApiResult<T>>
 */
export async function fetchApi<T>(
  url: string,
  options?: RequestInit
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(url, {
      ...options,
      cache: 'no-store',
    })

    const data = await res.json()

    // 双重检查：HTTP 状态码 + 响应体 success 字段
    if (!res.ok) {
      return {
        success: false,
        error: data.error || data.message || `HTTP ${res.status}`,
      }
    }

    // 如果响应体有 success 字段，检查它
    if (typeof data.success === 'boolean' && !data.success) {
      return {
        success: false,
        error: data.error || data.message || '请求失败',
      }
    }

    return {
      success: true,
      data: data.data !== undefined ? data.data : data,
    }
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : '网络请求失败',
    }
  }
}

// ========== 数值格式化 ==========

/**
 * 格式化数字，添加千位分隔符
 * @param value - 数字或 undefined
 * @returns 格式化后的字符串
 */
export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-'
  return value.toLocaleString('zh-CN')
}

// ========== 类型守卫 ==========

/**
 * 检查对象是否为空（null, undefined, 空对象）
 */
export function isEmpty(obj: unknown): boolean {
  if (obj === null || obj === undefined) return true
  if (typeof obj === 'object') {
    return Object.keys(obj).length === 0
  }
  return false
}
