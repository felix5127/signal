// Input: Figma设计稿提取的字体样式
// Output: 标准化的排版 Tokens
// Position: 设计系统排版定义，统一字体大小、行高、字重
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Figma 设计稿字体分析
 * - 字体族: Inter (优先), 系统后备字体
 * - 字体大小范围: 10.8px ~ 103.4px
 * - 行高范围: 1.35 ~ 1.72
 * - 字重: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)
 */

// ============ 字体族 ============
const fontFamilies = {
  default: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
}

// ============ 字体大小 ============
const fontSizes = {
  // 从 Figma 提取的精确值，四舍五入
  xs: '10.8px',     // style_0MVPJL - 小标签
  sm: '11.6px',     // style_6QVCML - 辅助文本
  base: '15.4px',   // style_3EZJRH - 正文
  md: '17px',       // style_IHV6OX - 次级标题
  lg: '17.4px',     // style_9828KC - 卡片标题
  xl: '25.9px',     // style_YLLJYG - 三级标题
  '2xl': '26px',    // style_PB54PO - 二级标题
  '3xl': '34.7px',  // style_LPHLTP - 引用文本
  '4xl': '35px',    // style_79LIQF - 大标题
  '5xl': '55.7px',  // style_1QCC4O - 主标题
  '6xl': '103.4px', // style_KZ4235 - 超大标题 (Hero)
}

// ============ 字重 ============
const fontWeights = {
  light: 300,
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
}

// ============ 行高 ============
const lineHeights = {
  tight: '1.35',      // 紧凑
  snug: '1.4',        // 适中紧凑
  normal: '1.55',     // 正常 (style_3EZJRH)
  relaxed: '1.58',    // 宽松
  loose: '1.69',      // 很宽松 (style_IHV6OX)
}

// ============ 字母间距 ============
const letterSpacings = {
  tighter: '-0.25%',   // 紧凑
  tight: '-0.15%',     // 适中紧凑
  normal: '0%',        // 正常
  wide: '0.1%',        // 宽松
  wider: '8%',         // 很宽松 (大写标签)
}

// ============ 文本样式预设 ============
const textStyles = {
  // Hero 标题
  hero: {
    fontSize: fontSizes['6xl'],
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacings.tight,
  },

  // 页面标题
  'page-title': {
    fontSize: fontSizes['5xl'],
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.snug,
    letterSpacing: letterSpacings.tight,
  },

  // 区块标题
  'section-title': {
    fontSize: fontSizes['2xl'],
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacings.tight,
  },

  // 卡片标题
  'card-title': {
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.relaxed,
    letterSpacing: letterSpacings.tighter,
  },

  // 正文
  body: {
    fontSize: fontSizes.base,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacings.tight,
  },

  // 辅助文本
  caption: {
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacings.tighter,
  },

  // 标签
  label: {
    fontSize: fontSizes.xs,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.snug,
    letterSpacing: letterSpacings.wider,
    textTransform: 'uppercase',
  },

  // 引用
  quote: {
    fontSize: fontSizes['3xl'],
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacings.tight,
  },
}

// ============ CSS 变量 ============
const cssVariables = {
  // 字体族
  '--font-family-default': fontFamilies.default,
  '--font-family-mono': fontFamilies.mono,

  // 字体大小
  '--font-size-xs': fontSizes.xs,
  '--font-size-sm': fontSizes.sm,
  '--font-size-base': fontSizes.base,
  '--font-size-md': fontSizes.md,
  '--font-size-lg': fontSizes.lg,
  '--font-size-xl': fontSizes.xl,
  '--font-size-2xl': fontSizes['2xl'],
  '--font-size-3xl': fontSizes['3xl'],
  '--font-size-4xl': fontSizes['4xl'],
  '--font-size-5xl': fontSizes['5xl'],
  '--font-size-6xl': fontSizes['6xl'],

  // 字重
  '--font-weight-light': fontWeights.light,
  '--font-weight-regular': fontWeights.regular,
  '--font-weight-medium': fontWeights.medium,
  '--font-weight-semibold': fontWeights.semibold,
  '--font-weight-bold': fontWeights.bold,

  // 行高
  '--line-height-tight': lineHeights.tight,
  '--line-height-snug': lineHeights.snug,
  '--line-height-normal': lineHeights.normal,
  '--line-height-relaxed': lineHeights.relaxed,
  '--line-height-loose': lineHeights.loose,
}

// ============ Tailwind 配置导出 ============
const tailwindTypography = {
  fontFamily: {
    sans: fontFamilies.default.split(', '),
    mono: fontFamilies.mono.split(', '),
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
  letterSpacing: letterSpacings,
}

// ============ 导出 ============
export { fontFamilies, fontSizes, fontWeights, lineHeights, letterSpacings, textStyles, cssVariables }

const typography = { ...tailwindTypography, textStyles }
export default typography
