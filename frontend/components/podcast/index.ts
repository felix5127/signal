/**
 * [INPUT]: 依赖 podcast/ 目录下的所有组件
 * [OUTPUT]: 统一导出 podcast 子组件
 * [POS]: podcast/ 的入口文件，简化导入路径
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

// Context Provider（需要包裹播客详情页）
export { AudioPlayerProvider, useAudioPlayer } from './audio-player-context'

// 组件
export { AudioPlayer, seekToTime } from './audio-player'
export { ChapterOverview } from './chapter-overview'
export type { Chapter } from './chapter-overview'
export { TranscriptView } from './transcript-view'
export { QARecap } from './qa-recap'
export type { QAPair } from './qa-recap'
export { ContentTabs } from './content-tabs'
export type { TabKey } from './content-tabs'
export { PodcastDetail } from './podcast-detail'
export type { PodcastResource } from './podcast-detail'

// 工具函数
export { formatTime, formatDuration } from './utils'
