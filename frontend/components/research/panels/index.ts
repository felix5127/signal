/**
 * [INPUT]: 依赖 panels 目录下所有组件
 * [OUTPUT]: 统一导出 ResearchPanel, ChatPanel, SourcesPanel 面板组件
 * [POS]: components/research/panels 的模块导出入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

export { default as ResearchPanel } from './ResearchPanel'
export { default as ChatPanel } from './ChatPanel'
export { default as SourcesPanel, type Source } from './SourcesPanel'
