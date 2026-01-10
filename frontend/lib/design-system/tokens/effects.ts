// Input: Figma设计稿提取的圆角、阴影和动效
// Output: 标准化的效果 Tokens
// Position: 设计系统视觉效果定义，圆角、阴影、动效
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Figma 设计稿效果分析
 * - 圆角: 3px, 4px, 12px, 9999px (胶囊)
 * - 阴影: 微妙的投影系统
 * - 动效: 快速过渡 (150-300ms)
 */

// ============ 圆角 ============
const borderRadius = {
  none: '0px',
  xs: '3px',      // 小圆角 - 标签、小按钮
  sm: '4px',      // 中小圆角 - 输入框
  md: '8px',      // 中圆角 - 卡片
  lg: '12px',     // 大圆角 - 容器
  xl: '16px',     // 超大圆角
  '2xl': '24px',  // 特大圆角
  full: '9999px', // 完全圆角/胶囊形
}

// ============ 阴影 ============
const shadows = {
  // 微妙阴影 - 小元素
  xs: '0 1px 2px rgba(0, 0, 0, 0.05)',

  // 小阴影 - 按钮、标签
  sm: '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)',

  // 中阴影 - 卡片
  md: '0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.04)',

  // 大阴影 - 浮动卡片
  lg: '0 10px 15px rgba(0, 0, 0, 0.08), 0 4px 6px rgba(0, 0, 0, 0.04)',

  // 超大阴影 - 弹窗
  xl: '0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)',

  // 内阴影
  inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.05)',

  // 品牌色阴影
  brand: {
    sm: '0 2px 8px rgba(98, 88, 255, 0.15)',
    md: '0 4px 12px rgba(98, 88, 255, 0.2)',
    lg: '0 8px 24px rgba(98, 88, 255, 0.25)',
  },

  // 深色模式阴影
  dark: {
    sm: '0 1px 3px rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px rgba(0, 0, 0, 0.4)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.5)',
  },
}

// ============ 模糊效果 ============
const blur = {
  sm: '4px',
  md: '8px',
  lg: '16px',
  xl: '24px',
  '2xl': '40px',
  full: '80px',
}

// ============ 动效时长 ============
const duration = {
  instant: '100ms',
  fast: '150ms',
  normal: '200ms',
  slow: '300ms',
  slower: '500ms',
}

// ============ 动效缓动 ============
const easing = {
  // 线性
  linear: 'linear',

  // 标准
  ease: 'ease',
  'ease-in': 'ease-in',
  'ease-out': 'ease-out',
  'ease-in-out': 'ease-in-out',

  // 自定义
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
}

// ============ 过渡组合 ============
const transitions = {
  // 快速过渡
  fast: `${duration.fast} ${easing.smooth}`,

  // 标准过渡
  normal: `${duration.normal} ${easing.smooth}`,

  // 慢速过渡
  slow: `${duration.slow} ${easing.smooth}`,

  // 弹跳过渡
  bounce: `${duration.normal} ${easing.bounce}`,

  // 颜色过渡
  colors: `color ${duration.normal} ${easing.smooth}`,

  // 背景过渡
  backgrounds: `background-color ${duration.normal} ${easing.smooth}`,

  // 边框过渡
  borders: `border-color ${duration.normal} ${easing.smooth}`,

  // 阴影过渡
  shadows: `box-shadow ${duration.normal} ${easing.smooth}`,

  // 变换过渡
  transforms: `transform ${duration.fast} ${easing.sharp}`,

  // 全部属性
  all: `all ${duration.normal} ${easing.smooth}`,
}

// ============ CSS 变量 ============
const cssVariables = {
  // 圆角
  '--radius-none': borderRadius.none,
  '--radius-xs': borderRadius.xs,
  '--radius-sm': borderRadius.sm,
  '--radius-md': borderRadius.md,
  '--radius-lg': borderRadius.lg,
  '--radius-xl': borderRadius.xl,
  '--radius-2xl': borderRadius['2xl'],
  '--radius-full': borderRadius.full,

  // 阴影
  '--shadow-xs': shadows.xs,
  '--shadow-sm': shadows.sm,
  '--shadow-md': shadows.md,
  '--shadow-lg': shadows.lg,
  '--shadow-xl': shadows.xl,
  '--shadow-inner': shadows.inner,

  // 模糊
  '--blur-sm': blur.sm,
  '--blur-md': blur.md,
  '--blur-lg': blur.lg,
  '--blur-xl': blur.xl,
  '--blur-2xl': blur['2xl'],
  '--blur-full': blur.full,

  // 动效
  '--duration-fast': duration.fast,
  '--duration-normal': duration.normal,
  '--duration-slow': duration.slow,

  '--transition-fast': transitions.fast,
  '--transition-normal': transitions.normal,
  '--transition-slow': transitions.slow,
}

// ============ Tailwind 配置导出 ============
const tailwindEffects = {
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

// ============ 导出 ============
export { borderRadius, shadows, blur, duration, easing, transitions, cssVariables }
export default tailwindEffects
