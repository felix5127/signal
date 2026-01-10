// Input: 各 hook 模块
// Output: Hooks 便捷导出对象
// Position: 设计系统 Hooks 便捷导出
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import { useMediaQuery, useIsMobile, useIsTablet, useIsDesktop, useScreenSize, breakpoints } from './useMediaQuery'
import { useTheme } from './useTheme'

export const Hooks = {
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useScreenSize,
  useTheme,
}
