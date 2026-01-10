// Input: 各 tokens 模块
// Output: 统一导出的设计系统 Tokens
// Position: 设计系统 Tokens 顶层导出文件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Signal Hunter 设计系统 Tokens
 * 从 Figma 设计稿提取的标准化设计变量
 *
 * @module design-system/tokens
 */

// ============ 导入所有 Tokens ============
import { baseColors, semanticColors, cssVariables as colorVars } from './colors'
import { baseSpacing, semanticSpacing, cssVariables as spacingVars } from './spacing'
import { fontFamilies, fontSizes, fontWeights, lineHeights, letterSpacings, textStyles, cssVariables as typographyVars } from './typography'
import { borderRadius, shadows, blur, duration, easing, transitions, cssVariables as effectVars } from './effects'

// ============ 顶层 Tokens 导出 ============
export const tokens = {
  colors: {
    base: baseColors,
    semantic: semanticColors,
  },
  spacing: {
    base: baseSpacing,
    semantic: semanticSpacing,
  },
  typography: {
    families: fontFamilies,
    sizes: fontSizes,
    weights: fontWeights,
    lineHeights: lineHeights,
    letterSpacings: letterSpacings,
    styles: textStyles,
  },
  effects: {
    borderRadius,
    shadows,
    blur,
    duration,
    easing,
    transitions,
  },
}

// ============ CSS 变量集合 ============
export const cssVariables = {
  ...colorVars,
  ...spacingVars,
  ...typographyVars,
  ...effectVars,
}

// ============ Tailwind 配置扩展 ============
export const tailwindExtension = {
  colors: {
    ...semanticColors.background,
    ...semanticColors.text,
    ...semanticColors.border,
    primary: semanticColors.text.primary,
    success: {
      100: '#CDEED3',
    },
  },
  spacing: {
    ...baseSpacing,
    ...semanticSpacing.container,
    ...semanticSpacing.component,
    ...semanticSpacing.layout,
  },
  fontSize: {
    xs: [fontSizes.xs, lineHeights.snug],
    sm: [fontSizes.sm, lineHeights.normal],
    base: [fontSizes.base, lineHeights.normal],
    md: [fontSizes.md, lineHeights.relaxed],
    lg: [fontSizes.lg, lineHeights.relaxed],
    xl: [fontSizes.xl, lineHeights.normal],
    '2xl': [fontSizes['2xl'], lineHeights.normal],
    '3xl': [fontSizes['3xl'], lineHeights.tight],
    '4xl': [fontSizes['4xl'], lineHeights.tight],
    '5xl': [fontSizes['5xl'], lineHeights.snug],
    '6xl': [fontSizes['6xl'], lineHeights.tight],
  },
  fontWeight: fontWeights,
  lineHeight: lineHeights,
  letterSpacing: {
    tighter: letterSpacings.tighter,
    tight: letterSpacings.tight,
    normal: letterSpacings.normal,
    wide: letterSpacings.wide,
    wider: letterSpacings.wider,
  },
  borderRadius: {
    none: borderRadius.none,
    xs: borderRadius.xs,
    sm: borderRadius.sm,
    md: borderRadius.md,
    lg: borderRadius.lg,
    xl: borderRadius.xl,
    '2xl': borderRadius['2xl'],
    full: borderRadius.full,
  },
  boxShadow: {
    xs: shadows.xs,
    sm: shadows.sm,
    md: shadows.md,
    lg: shadows.lg,
    xl: shadows.xl,
    inner: shadows.inner,
    'brand-sm': shadows.brand.sm,
    'brand-md': shadows.brand.md,
    'brand-lg': shadows.brand.lg,
  },
  backdropBlur: blur,
  transitionDuration: duration,
  transitionTimingFunction: easing,
}

// ============ 应用 CSS 变量的函数 ============
/**
 * 将设计系统 CSS 变量注入到 :root
 * 使用方式: import { injectCSSVariables } from '@/design-system/tokens'
 *   injectCSSVariables()
 */
export const injectCSSVariables = () => {
  if (typeof document === 'undefined') return

  const root = document.documentElement
  Object.entries(cssVariables).forEach(([key, value]) => {
    root.style.setProperty(key, value as string)
  })
}

// ============ 文本样式辅助函数 ============
/**
 * 根据预设名称获取文本样式类名
 * @param {string} styleName - 预设样式名称 (hero, page-title, section-title, card-title, body, caption, label, quote)
 * @returns {string} Tailwind 类名字符串
 */
export const getTextStyleClasses = (styleName: keyof typeof textStyles): string => {
  const style = textStyles[styleName]
  if (!style) return ''

  const classes: string[] = []

  // 字体大小
  if (style.fontSize) {
    const sizeKey = Object.entries(fontSizes).find(([, v]) => v === style.fontSize)?.[0]
    if (sizeKey) classes.push(`text-${sizeKey}`)
  }

  // 字重
  if (style.fontWeight) {
    const weightKey = Object.entries(fontWeights).find(([, v]) => v === style.fontWeight)?.[0]
    if (weightKey) classes.push(`font-${weightKey}`)
  }

  // 行高
  if (style.lineHeight) {
    const heightKey = Object.entries(lineHeights).find(([, v]) => v === style.lineHeight)?.[0]
    if (heightKey) classes.push(`leading-${heightKey}`)
  }

  // 字母间距
  if (style.letterSpacing) {
    const spacingKey = Object.entries(letterSpacings).find(([, v]) => v === style.letterSpacing)?.[0]
    if (spacingKey) classes.push(`tracking-${spacingKey}`)
  }

  // 大写转换
  if ('textTransform' in style && style.textTransform === 'uppercase') {
    classes.push('uppercase')
  }

  return classes.join(' ')
}

// ============ 默认导出 ============
export default tokens
