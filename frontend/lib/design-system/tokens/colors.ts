// Input: Figma设计稿提取的颜色值
// Output: 标准化的颜色 Tokens 对象
// Position: 设计系统核心颜色定义，用于所有组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

/**
 * Figma 设计稿颜色提取
 * 来源: signal Figma file
 *
 * 主色调:
 * - 背景: #FFFFFF (纯白), #F8F9F7 (浅灰), #161818 (深黑)
 * - 文字: #CDCBFF (淡紫标题), #544A2E (深棕), #68706F (灰绿辅助)
 * - 边框: rgba(186, 196, 192, 0.2)
 * - 辅助: #CDEED3 (淡绿), #E1E3E3 (浅灰)
 */

// ============ 基础颜色 ============
const baseColors = {
  // 中性色（灰度系统）
  white: '#FFFFFF',
  black: '#000000',

  // 灰度色阶
  gray: {
    50: '#F9F9F7',   // fill_MMTE0S
    100: '#F3F4F2',  // fill_T5BREO
    200: '#EBECEB',  // fill_QWT9U9
    300: '#E1E3E3',  // fill_JCUNOZ
    400: '#BAC4C0',  // stroke base
    500: '#68706F',  // fill_ZNWYSI - 辅助文字
    600: '#544A2E',  // fill_2VS8X0 - 深色文字
    700: '#161818',  // fill_RDC7YP - 深色背景
    800: '#001D21',  // fill_0UIH86
    900: '#002B31',  // fill_3EMP9I
  },

  // 品牌色
  primary: {
    50: '#F3F2FF',
    100: '#E9E7FF',
    200: '#CDCBFF',  // fill_5ZN3AI - 品牌淡紫
    300: '#BDBBFF',  // fill_Z9UWNI
    400: '#A9A5FF',
    500: '#6258FF',  // 渐变起始色
    600: '#5247DB',
    700: '#4337B7',
    800: '#342793',
    900: '#25176F',
  },

  // 辅助色 - 绿色系
  success: {
    50: '#F0FDF4',
    100: '#CDEED3',  // fill_PBVEFM, stroke_0PW6FR
    200: '#A5DBC0',
    300: '#75C9AD',
    400: '#4CB99A',
    500: '#25A987',
    600: '#1B9A7A',
    700: '#138069',
    800: '#0D6654',
    900: '#064C3F',
  },

  // 语义色
  semantic: {
    info: '#CDEED3',
    warning: '#FEF3C7',
    error: '#FEE2E2',
    critical: '#FECACA',
  },
}

// ============ 语义映射 ============
const semanticColors = {
  // 背景色
  background: {
    DEFAULT: baseColors.white,
    primary: baseColors.primary[50],
    secondary: baseColors.gray[50],
    dark: baseColors.gray[700],
    darker: baseColors.gray[900],
  },

  // 文字色
  text: {
    DEFAULT: baseColors.gray[600],      // 主要文字
    primary: baseColors.primary[200],   // 品牌色文字（标题）
    secondary: baseColors.gray[500],    // 次要文字
    muted: baseColors.gray[400],        // 弱化文字
    inverse: baseColors.white,          // 反色文字
  },

  // 边框色
  border: {
    DEFAULT: 'rgba(186, 196, 192, 0.2)',  // stroke_IGZ696, stroke_KT23JK
    subtle: 'rgba(186, 196, 192, 0.1)',
    strong: baseColors.gray[300],
    focus: baseColors.primary[300],
  },

  // 交互状态
  interaction: {
    hover: baseColors.gray[100],
    active: baseColors.gray[200],
    disabled: baseColors.gray[50],
  },

  // 渐变
  gradient: {
    primary: 'linear-gradient(181deg, #6258FF 0%, #E06AB2 33%, #FB8569 66%, #FFB1B1 90%)',
    subtle: 'linear-gradient(135deg, #CDCBFF 0%, #BDBBFF 100%)',
    dark: 'linear-gradient(180deg, #161818 0%, #002B31 100%)',
  },
}

// ============ CSS 变量导出 ============
const cssVariables = {
  // 基础色
  '--color-white': baseColors.white,
  '--color-black': baseColors.black,

  // 灰度
  '--color-gray-50': baseColors.gray[50],
  '--color-gray-100': baseColors.gray[100],
  '--color-gray-200': baseColors.gray[200],
  '--color-gray-300': baseColors.gray[300],
  '--color-gray-400': baseColors.gray[400],
  '--color-gray-500': baseColors.gray[500],
  '--color-gray-600': baseColors.gray[600],
  '--color-gray-700': baseColors.gray[700],
  '--color-gray-800': baseColors.gray[800],
  '--color-gray-900': baseColors.gray[900],

  // 品牌色
  '--color-primary-50': baseColors.primary[50],
  '--color-primary-100': baseColors.primary[100],
  '--color-primary-200': baseColors.primary[200],
  '--color-primary-300': baseColors.primary[300],
  '--color-primary-400': baseColors.primary[400],
  '--color-primary-500': baseColors.primary[500],
  '--color-primary-600': baseColors.primary[600],

  // 辅助色
  '--color-success-100': baseColors.success[100],

  // 语义色
  '--color-bg-default': semanticColors.background.DEFAULT,
  '--color-bg-secondary': semanticColors.background.secondary,
  '--color-bg-dark': semanticColors.background.dark,

  '--color-text-default': semanticColors.text.DEFAULT,
  '--color-text-primary': semanticColors.text.primary,
  '--color-text-secondary': semanticColors.text.secondary,
  '--color-text-muted': semanticColors.text.muted,

  '--color-border-default': semanticColors.border.DEFAULT,
  '--color-border-subtle': semanticColors.border.subtle,

  // 渐变
  '--gradient-primary': semanticColors.gradient.primary,
  '--gradient-subtle': semanticColors.gradient.subtle,
}

// ============ Tailwind 配置导出 ============
const tailwindColors = {
  ...baseColors,
  background: semanticColors.background,
  text: semanticColors.text,
  border: semanticColors.border,
}

// ============ 导出 ============
export { baseColors, semanticColors, cssVariables }
export default tailwindColors
