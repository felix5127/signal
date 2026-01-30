// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

/**
 * VideosPage - 视频列表页
 * 设计规范: Mercury.com 浅色系
 * - 背景色: #FBFCFD
 * - 主色调: #1E3A5F (深海军蓝)
 * - 文字色: #272735, #6B6B6B, #9A9A9A
 * - 圆角: 16px
 * - 视频卡片: 3列网格，带彩色缩略图和播放按钮
 */

import { ResourceListPage } from '@/components/resource-list-page'
import { VideoCard } from '@/components/video-card'

export default function VideosPage() {
  return (
    <ResourceListPage
      resourceType="video"
      CardComponent={VideoCard}
      pageTitle="视频"
      pageSubtitle="观看技术教程与会议演讲"
      wideLayout
    />
  )
}

export const metadata = {
  title: '技术视频 - Signal Hunter',
  description: '精选技术视频与教程，涵盖人工智能、软件工程等领域',
}
