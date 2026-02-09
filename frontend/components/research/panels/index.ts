/**
 * [INPUT]: 依赖 panels 目录下所有组件
 * [OUTPUT]: 统一导出 StudioPanel, ChatPanel, SourcesPanel 面板组件及类型
 * [POS]: components/research/panels 的模块导出入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

export { default as StudioPanel } from './StudioPanel'
export { default as ChatPanel, type ChatMessage } from './ChatPanel'
export { default as SourcesPanel, type Source } from './SourcesPanel'

// 保留旧的导出名称以兼容
export { default as ResearchPanel } from './StudioPanel'
