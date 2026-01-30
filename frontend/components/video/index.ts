/**
 * [INPUT]: 依赖 video/ 目录下的组件
 * [OUTPUT]: 统一导出入口
 * [POS]: video/ 的模块导出
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

export { VideoPlayer } from './video-player'
export { VideoDetail } from './video-detail'
export type { VideoResource } from './video-detail'
