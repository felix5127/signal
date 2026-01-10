// Input: Figma设计稿提取的间距值（8px基准网格）
// Output: 标准化的间距 Tokens
// Position: 设计系统间距定义，统一所有空间尺寸
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Figma 设计稿间距分析
 * - 基于 8px 基准网格
 * - 容器内边距: 48px (lg), 24px (md), 16px (sm)
 * - 组件间距: 4px, 8px, 12px, 16px, 24px, 32px, 48px
 */

// ============ 基础间距 (8px 基准) ============
const baseSpacing = {
  0: '0px',
  1: '4px',    // 0.5x
  2: '8px',    // 1x - 基准单位
  3: '12px',   // 1.5x
  4: '16px',   // 2x
  5: '20px',   // 2.5x
  6: '24px',   // 3x
  8: '32px',   // 4x
  10: '40px',  // 5x
  12: '48px',  // 6x
  16: '64px',  // 8x
  20: '80px',  // 10x
  24: '96px',  // 12x
  32: '128px', // 16x
}

// ============ 语义间距 ============
const semanticSpacing = {
  // 容器内边距
  container: {
    xs: baseSpacing[4],   // 16px - 小容器
    sm: baseSpacing[6],   // 24px - 中容器
    md: baseSpacing[10],  // 40px - 大容器
    lg: baseSpacing[12],  // 48px - 超大容器
    xl: baseSpacing[16],  // 64px - 特大容器
  },

  // 组件间距
  component: {
    xs: baseSpacing[1],   // 4px - 紧凑
    sm: baseSpacing[2],   // 8px - 小间距
    md: baseSpacing[3],   // 12px - 中间距
    lg: baseSpacing[4],   // 16px - 大间距
    xl: baseSpacing[6],   // 24px - 超大间距
  },

  // 布局间距
  layout: {
    xs: baseSpacing[4],   // 16px - 紧凑布局
    sm: baseSpacing[6],   // 24px - 小布局
    md: baseSpacing[10],  // 40px - 中布局
    lg: baseSpacing[12],  // 48px - 大布局
    xl: baseSpacing[20],  // 80px - 超大布局
  },

  // Section 间距
  section: {
    sm: baseSpacing[12],  // 48px - 小 section
    md: baseSpacing[16],  // 64px - 中 section
    lg: baseSpacing[20],  // 80px - 大 section
    xl: baseSpacing[24],  // 96px - 超大 section
  },
}

// ============ CSS 变量 ============
const cssVariables = {
  '--spacing-0': baseSpacing[0],
  '--spacing-1': baseSpacing[1],
  '--spacing-2': baseSpacing[2],
  '--spacing-3': baseSpacing[3],
  '--spacing-4': baseSpacing[4],
  '--spacing-5': baseSpacing[5],
  '--spacing-6': baseSpacing[6],
  '--spacing-8': baseSpacing[8],
  '--spacing-10': baseSpacing[10],
  '--spacing-12': baseSpacing[12],
  '--spacing-16': baseSpacing[16],
  '--spacing-20': baseSpacing[20],
  '--spacing-24': baseSpacing[24],
  '--spacing-32': baseSpacing[32],

  '--container-padding-xs': semanticSpacing.container.xs,
  '--container-padding-sm': semanticSpacing.container.sm,
  '--container-padding-md': semanticSpacing.container.md,
  '--container-padding-lg': semanticSpacing.container.lg,
  '--container-padding-xl': semanticSpacing.container.xl,

  '--component-gap-xs': semanticSpacing.component.xs,
  '--component-gap-sm': semanticSpacing.component.sm,
  '--component-gap-md': semanticSpacing.component.md,
  '--component-gap-lg': semanticSpacing.component.lg,
  '--component-gap-xl': semanticSpacing.component.xl,

  '--section-spacing-sm': semanticSpacing.section.sm,
  '--section-spacing-md': semanticSpacing.section.md,
  '--section-spacing-lg': semanticSpacing.section.lg,
  '--section-spacing-xl': semanticSpacing.section.xl,
}

// ============ Tailwind 配置导出 ============
const tailwindSpacing = {
  ...baseSpacing,
  container: semanticSpacing.container,
  component: semanticSpacing.component,
  layout: semanticSpacing.layout,
  section: semanticSpacing.section,
}

// ============ 导出 ============
export { baseSpacing, semanticSpacing, cssVariables }
export default tailwindSpacing
