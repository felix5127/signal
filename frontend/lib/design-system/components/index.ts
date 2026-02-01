// Input: 各组件模块
// Output: 统一导出的设计系统组件
// Position: 设计系统组件顶层导出文件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Signal 设计系统组件库
 * 基于 Figma 设计稿构建的标准化 UI 组件
 *
 * @module design-system/components
 */

// ============ 导出所有组件 ============
export { Button, default as ButtonComponent } from './Button'
export type { ButtonProps } from './Button'

export { Input, default as InputComponent } from './Input'
export type { InputProps } from './Input'

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  default as CardComponent,
} from './Card'
export type { CardProps } from './Card'

export {
  Badge,
  StatusBadge,
  ScoreBadge,
  default as BadgeComponent,
} from './Badge'
export type { BadgeProps } from './Badge'

export { Tag, TagGroup, default as TagComponent } from './Tag'
export type { TagProps, TagGroupProps } from './Tag'

// ============ 便捷导出 ============
/**
 * 统一的对象形式导出，支持解构使用
 * @example
 * import { Components } from '@/design-system'
 * const { Button, Card, Badge } = Components
 */
export { Components } from './Components'

