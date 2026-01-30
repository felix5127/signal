// Input: Mercury 风格设计规范
// Output: 统一的 Mercury 风格颜色 Tokens
// Position: 设计系统核心颜色定义
// Style: Mercury.com - 简洁大气

/**
 * Signal Hunter 设计系统 - Mercury 风格
 * 核心理念: 简洁 · 大气 · 专业
 */

// ============ 基础颜色 ============
export const baseColors = {
  // 中性色
  white: '#FFFFFF',
  black: '#000000',

  // 灰度色阶 (Mercury 风格)
  gray: {
    50: '#fbfcfd',   // 主背景
    100: '#f6f5f2',  // 次级背景
    200: '#eeeeed',  // 卡片背景
    300: '#e5e5e4',  // 边框
    400: '#a1a1a0',  // 弱化文字
    500: '#6b7280',  // 次要文字
    600: '#4b5563',  // 正文
    700: '#374151',  // 标题
    800: '#272735',  // 深色文字
    900: '#1a1a24',  // 最深
  },

  // 主色 - 墨绿 (Mercury Green)
  primary: {
    50: '#f1f7f3',   // 浅背景
    100: '#dcebe1',
    200: '#bbd8c6',
    300: '#8ebfa3',
    400: '#5da17c',
    500: '#188554',  // 主色
    600: '#0d6b41',
    700: '#0d5c3a',
    800: '#0c4a30',
    900: '#0a3d28',
  },

  // 强调色 - 琥珀金 (Accent)
  accent: {
    50: '#fdfaf3',
    100: '#f9f0dc',
    200: '#f2dfb8',
    300: '#e9c98a',
    400: '#ddb05a',
    500: '#8a753c',  // 主强调
    600: '#7a6634',
    700: '#65532b',
    800: '#524427',
    900: '#453925',
  },

  // 语义色
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
  },
}

// ============ 语义映射 ============
export const semanticColors = {
  // 背景色
  background: {
    DEFAULT: baseColors.gray[50],      // #fbfcfd
    primary: baseColors.white,          // 卡片/弹窗
    secondary: baseColors.gray[100],    // 次级区域
    tertiary: baseColors.gray[200],     // 输入框
    inverse: baseColors.gray[800],      // 深色背景
  },

  // 文字色
  text: {
    DEFAULT: baseColors.gray[800],      // #272735 主文字
    primary: baseColors.primary[500],   // #188554 品牌色文字
    secondary: baseColors.gray[500],    // #6b7280 次要文字
    muted: baseColors.gray[400],        // #a1a1a0 弱化文字
    inverse: baseColors.white,          // 反色文字
  },

  // 边框色
  border: {
    DEFAULT: 'rgba(0, 0, 0, 0.06)',     // 轻边框
    subtle: 'rgba(0, 0, 0, 0.04)',      // 极轻边框
    strong: 'rgba(0, 0, 0, 0.1)',       // 强边框
    focus: baseColors.primary[500],     // 聚焦边框
  },

  // 交互状态
  interaction: {
    hover: baseColors.gray[100],
    active: baseColors.gray[200],
    disabled: baseColors.gray[50],
  },
}

// ============ CSS 变量导出 ============
export const cssVariables = {
  // Mercury 统一变量
  '--bg-primary': baseColors.gray[50],
  '--bg-secondary': baseColors.gray[100],
  '--bg-card': baseColors.white,
  '--bg-input': baseColors.gray[200],

  '--text-primary': baseColors.gray[800],
  '--text-secondary': baseColors.gray[500],
  '--text-muted': baseColors.gray[400],

  '--color-primary': baseColors.primary[500],
  '--color-primary-light': baseColors.primary[50],
  '--color-primary-dark': baseColors.primary[700],

  '--color-accent': baseColors.accent[500],
  '--color-accent-light': baseColors.accent[50],

  '--border-light': 'rgba(0, 0, 0, 0.06)',
  '--border-default': 'rgba(0, 0, 0, 0.1)',

  // 保留的语义变量（兼容 shadcn/ui）
  '--color-white': baseColors.white,
  '--color-black': baseColors.black,
}

export default baseColors
