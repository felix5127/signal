// Input: 各 hook 模块
// Output: 统一导出的设计系统 Hooks
// Position: 设计系统 Hooks 顶层导出文件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Signal 设计系统 Hooks
 * 通用 React Hooks 集合
 *
 * @module design-system/hooks
 */

// ============ 导出所有 Hooks ============
export {
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useScreenSize,
  breakpoints,
} from './useMediaQuery'

export {
  useTheme,
  type Theme,
  type UseThemeReturn,
} from './useTheme'

// ============ 便捷导出 ============
/**
 * 统一的对象形式导出，支持解构使用
 * @example
 * import { Hooks } from '@/design-system'
 * const { useMediaQuery, useTheme } = Hooks
 */
export { Hooks } from './Hooks'

