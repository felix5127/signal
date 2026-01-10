/**
 * Web 风格设计系统 - 颜色 Tokens
 * 使用 CSS 变量支持主题切换
 */

export const themes = {
  dark: {
    '--ds-bg': '#000000',
    '--ds-surface': 'rgba(0, 0, 0, 0.80)',
    '--ds-surface-2': 'rgba(255, 255, 255, 0.04)',
    '--ds-border': 'rgba(255, 255, 255, 0.10)',
    '--ds-border-2': 'rgba(255, 255, 255, 0.16)',
    '--ds-fg': '#EAF2FF',
    '--ds-muted': 'rgba(234, 242, 255, 0.72)',
    '--ds-subtle': 'rgba(234, 242, 255, 0.52)',
    '--ds-accent': '#34F0A1',
    '--ds-accent-2': '#22D3EE',
    '--ds-danger': '#FB7185',
    '--ds-ring': 'rgba(52, 240, 161, 0.35)',
  },
  light: {
    '--ds-bg': '#FFFFFF',
    '--ds-surface': 'rgba(0, 0, 0, 0.02)',
    '--ds-surface-2': 'rgba(0, 0, 0, 0.04)',
    '--ds-border': 'rgba(0, 0, 0, 0.10)',
    '--ds-border-2': 'rgba(0, 0, 0, 0.16)',
    '--ds-fg': '#0B1220',
    '--ds-muted': 'rgba(11, 18, 32, 0.74)',
    '--ds-subtle': 'rgba(11, 18, 32, 0.52)',
    '--ds-accent': '#6258FF',
    '--ds-accent-2': '#CDCBFF',
    '--ds-danger': '#E11D48',
    '--ds-ring': 'rgba(98, 88, 255, 0.35)',
  },
}

export function getThemeVars(theme: keyof typeof themes = 'light') {
  return themes[theme] ?? themes.light
}
