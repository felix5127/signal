/**
 * [INPUT]: 无外部依赖
 * [OUTPUT]: 对外提供 formatTime, formatDuration 工具函数
 * [POS]: podcast/ 的公共工具函数，消除组件间重复代码
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

/**
 * 格式化时间 (秒 -> HH:MM:SS 或 MM:SS)
 */
export function formatTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

/**
 * 格式化时长（更友好的描述）
 */
export function formatDuration(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '0 分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return minutes > 0 ? `${hours} 小时 ${minutes} 分钟` : `${hours} 小时`
  }
  return `${minutes} 分钟`
}
