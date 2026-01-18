// Input: 各模块
// Output: 统一导出的设计系统
// Position: 设计系统顶层导出文件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Signal Hunter 设计系统
 * 基于 Figma 设计稿构建的完整设计系统
 *
 * @module design-system
 *
 * @example
 * // 导入所有组件
 * import { Button, Card, Badge } from '@/design-system'
 *
 * // 导入 Tokens
 * import { tokens, cssVariables } from '@/design-system/tokens'
 *
 * // 导入 Hooks
 * import { useTheme, useMediaQuery } from '@/design-system/hooks'
 */

// ============ Tokens ============
export { tokens, cssVariables, injectCSSVariables, getTextStyleClasses, tailwindExtension } from './tokens'
export { baseColors, semanticColors } from './tokens/colors'
export { baseSpacing, semanticSpacing } from './tokens/spacing'
export {
  fontFamilies,
  fontSizes,
  fontWeights,
  lineHeights,
  letterSpacings,
  textStyles,
} from './tokens/typography'
export { borderRadius, shadows, blur, duration, easing, transitions } from './tokens/effects'

// ============ Components ============
export {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  StatusBadge,
  ScoreBadge,
  Tag,
  TagGroup,
  Components,
} from './components'

export type { ButtonProps } from './components/Button'
export type { InputProps } from './components/Input'
export type { CardProps } from './components/Card'
export type { BadgeProps } from './components/Badge'
export type { TagProps, TagGroupProps } from './components/Tag'

// ============ Hooks ============
export {
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useScreenSize,
  breakpoints,
  useTheme,
  Hooks,
} from './hooks'

export type { Theme, UseThemeReturn } from './hooks/useTheme'

// ============ 默认导出 ============
/**
 * 设计系统对象，包含所有 Tokens、组件和 Hooks
 */
import { tokens } from './tokens'
import { Button, Input, Card, Badge, Tag } from './components'
import { useTheme, useMediaQuery } from './hooks'

const designSystem = {
  tokens,
  components: {
    Button,
    Input,
    Card,
    Badge,
    Tag,
  },
  hooks: {
    useTheme,
    useMediaQuery,
  },
}

export default designSystem
