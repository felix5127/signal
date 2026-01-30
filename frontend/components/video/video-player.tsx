/**
 * [INPUT]: 依赖 lucide-react, @/lib/utils
 * [OUTPUT]: 对外提供 VideoPlayer 组件
 * [POS]: video/ 的视频播放器组件，匹配 Pencil 设计稿
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useCallback } from 'react'
import { Play, Pause } from 'lucide-react'
import { cn } from '@/lib/utils'

interface VideoPlayerProps {
  videoUrl?: string
  thumbnailUrl?: string
  duration?: number
  className?: string
}

// 格式化时长
function formatDuration(seconds?: number): string {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export function VideoPlayer({
  videoUrl,
  thumbnailUrl,
  duration,
  className,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [showControls, setShowControls] = useState(true)

  const togglePlay = useCallback(() => {
    const video = videoRef.current
    if (!video) return

    if (isPlaying) {
      video.pause()
      setShowControls(true)
    } else {
      video.play()
      setShowControls(false)
    }
    setIsPlaying(!isPlaying)
  }, [isPlaying])

  const handleVideoClick = useCallback(() => {
    if (isPlaying) {
      setShowControls(prev => !prev)
    } else {
      togglePlay()
    }
  }, [isPlaying, togglePlay])

  return (
    <div
      className={cn(
        'relative w-full aspect-video rounded-2xl overflow-hidden bg-[#1E3A5F] cursor-pointer',
        className
      )}
      onClick={handleVideoClick}
    >
      {/* 视频元素或占位 */}
      {videoUrl ? (
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full object-cover"
          poster={thumbnailUrl}
          onEnded={() => {
            setIsPlaying(false)
            setShowControls(true)
          }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          {/* 占位背景 */}
        </div>
      )}

      {/* 播放按钮遮罩 */}
      {showControls && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation()
              togglePlay()
            }}
            className="w-20 h-20 rounded-full bg-white flex items-center justify-center shadow-lg hover:scale-105 transition-transform"
          >
            {isPlaying ? (
              <Pause className="w-8 h-8 text-[#1E3A5F]" />
            ) : (
              <Play className="w-8 h-8 text-[#1E3A5F] ml-1" />
            )}
          </button>
        </div>
      )}

      {/* 时长标签 */}
      {duration && (
        <div className="absolute bottom-4 right-4 px-2.5 py-1.5 rounded-md bg-black/50 text-white text-[13px] font-medium">
          {formatDuration(duration)}
        </div>
      )}
    </div>
  )
}
