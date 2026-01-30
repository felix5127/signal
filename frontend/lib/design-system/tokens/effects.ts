// Input: Mercury 风格设计规范
// Output: 统一的 Mercury 风格效果 Tokens
// Position: 设计系统视觉效果定义
// Style: Mercury.com - 简洁大气，大圆角，极淡阴影

/**
 * Signal Hunter 设计系统 - Mercury 风格效果
 * 核心特点: 大圆角 (2rem)、极淡阴影、微妙玻璃效果
 */

// ============ 圆角 (Mercury 大圆角风格) ============
export const borderRadius = {
  none: '0px',
  xs: '0.25rem',    // 4px - 小元素
  sm: '0.5rem',     // 8px - 输入框内部
  md: '1rem',       // 16px - 中等元素
  lg: '1.5rem',     // 24px - 卡片
  xl: '2rem',       // 32px - 大卡片、按钮 (Mercury 默认)
  '2xl': '2.5rem',  // 40px - 特大元素
  '3xl': '3rem',    // 48px - Hero 元素
  full: '9999px',   // 胶囊形
}

// ============ 阴影 (Mercury 极淡风格) ============
export const shadows = {
  // 无阴影
  none: 'none',

  // 极淡阴影 - Mercury 风格核心
  xs: '0 1px 2px rgba(0, 0, 0, 0.03)',
  sm: '0 2px 4px rgba(0, 0, 0, 0.04)',
  md: '0 4px 8px rgba(0, 0, 0, 0.05)',
  lg: '0 8px 16px rgba(0, 0, 0, 0.06)',
  xl: '0 16px 32px rgba(0, 0, 0, 0.08)',

  // 卡片悬浮阴影
  'card-hover': '0 12px 24px rgba(0, 0, 0, 0.08)',

  // 内阴影 (输入框)
  inner: 'inset 0 1px 2px rgba(0, 0, 0, 0.04)',

  // 品牌色阴影 (墨绿)
  brand: {
    sm: '0 2px 8px rgba(24, 133, 84, 0.12)',
    md: '0 4px 16px rgba(24, 133, 84, 0.16)',
    lg: '0 8px 24px rgba(24, 133, 84, 0.2)',
  },

  // 强调色阴影 (琥珀金)
  accent: {
    sm: '0 2px 8px rgba(138, 117, 60, 0.12)',
    md: '0 4px 16px rgba(138, 117, 60, 0.16)',
  },
}

// ============ 玻璃效果 (Mercury 风格) ============
export const glass = {
  // 轻度玻璃 - 内容卡片
  light: {
    background: 'rgba(255, 255, 255, 0.8)',
    blur: '8px',
    border: '1px solid rgba(0, 0, 0, 0.04)',
  },
  // 标准玻璃 - 导航栏
  standard: {
    background: 'rgba(255, 255, 255, 0.7)',
    blur: '12px',
    border: '1px solid rgba(0, 0, 0, 0.06)',
  },
  // 深度玻璃 - 弹窗
  deep: {
    background: 'rgba(255, 255, 255, 0.6)',
    blur: '16px',
    border: '1px solid rgba(0, 0, 0, 0.08)',
  },
}

// ============ 模糊效果 ============
export const blur = {
  none: '0px',
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  '2xl': '24px',
  '3xl': '40px',
}

// ============ 动效时长 (Mercury 简洁风格) ============
export const duration = {
  instant: '100ms',
  fast: '150ms',
  normal: '200ms',
  slow: '300ms',
  slower: '400ms',
}

// ============ 动效缓动 ============
export const easing = {
  linear: 'linear',
  ease: 'ease',
  'ease-in': 'ease-in',
  'ease-out': 'ease-out',
  'ease-in-out': 'ease-in-out',
  // Mercury 风格缓动
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  // Apple 风格
  apple: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
  'apple-out': 'cubic-bezier(0.22, 1, 0.36, 1)',
}

// ============ 过渡组合 ============
export const transitions = {
  fast: `${duration.fast} ${easing.smooth}`,
  normal: `${duration.normal} ${easing.smooth}`,
  slow: `${duration.slow} ${easing.smooth}`,
  all: `all ${duration.normal} ${easing.smooth}`,
  transform: `transform ${duration.fast} ${easing.sharp}`,
  colors: `color, background-color, border-color ${duration.normal} ${easing.smooth}`,
  shadow: `box-shadow ${duration.normal} ${easing.smooth}`,
}

// ============ CSS 变量 ============
export const cssVariables = {
  // 圆角
  '--radius-xs': borderRadius.xs,
  '--radius-sm': borderRadius.sm,
  '--radius-md': borderRadius.md,
  '--radius-lg': borderRadius.lg,
  '--radius-xl': borderRadius.xl,
  '--radius-2xl': borderRadius['2xl'],
  '--radius-3xl': borderRadius['3xl'],
  '--radius-full': borderRadius.full,
  '--radius': borderRadius.xl,  // 默认圆角

  // 阴影
  '--shadow-xs': shadows.xs,
  '--shadow-sm': shadows.sm,
  '--shadow-md': shadows.md,
  '--shadow-lg': shadows.lg,
  '--shadow-xl': shadows.xl,
  '--shadow-card-hover': shadows['card-hover'],
  '--shadow-inner': shadows.inner,

  // 玻璃效果
  '--glass-bg-light': glass.light.background,
  '--glass-bg-standard': glass.standard.background,
  '--glass-bg-deep': glass.deep.background,
  '--glass-blur-light': glass.light.blur,
  '--glass-blur-standard': glass.standard.blur,
  '--glass-blur-deep': glass.deep.blur,

  // 模糊
  '--blur-sm': blur.sm,
  '--blur-md': blur.md,
  '--blur-lg': blur.lg,
  '--blur-xl': blur.xl,

  // 动效
  '--duration-fast': duration.fast,
  '--duration-normal': duration.normal,
  '--duration-slow': duration.slow,
  '--transition-fast': transitions.fast,
  '--transition-normal': transitions.normal,
  '--transition-slow': transitions.slow,
}

// ============ 默认导出 ============
export default { borderRadius, shadows, glass, blur, duration, easing, transitions, cssVariables }
