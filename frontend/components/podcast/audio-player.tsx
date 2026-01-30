/**
 * [INPUT]: 依赖 lucide-react, @/lib/utils, ./utils, ./audio-player-context
 * [OUTPUT]: 对外提供 AudioPlayer 组件, seekToTime 函数
 * [POS]: podcast/ 的音频播放器组件，匹配 Pencil 设计稿
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Play, Pause, Download, SkipBack, SkipForward, Mic, Share2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatTime } from './utils'
import { useAudioPlayer } from './audio-player-context'

interface AudioPlayerProps {
  audioUrl: string
  title?: string
  description?: string
  duration?: number // 总时长（秒）
  onTimeUpdate?: (currentTime: number) => void
  className?: string
}

// 速度选项
const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

export function AudioPlayer({
  audioUrl,
  title = '与 Andrej Karpathy 对话',
  description = 'AI 教育的未来与编程新范式',
  duration: propDuration,
  onTimeUpdate,
  className,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const { registerSeekHandler, setCurrentTime: setContextTime, setIsPlaying: setContextPlaying } = useAudioPlayer()
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(propDuration || 0)
  const [playbackRate, setPlaybackRate] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 加载音频元数据
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
      setIsLoading(false)
      setError(null)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
      onTimeUpdate?.(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
    }

    const handleError = () => {
      setIsLoading(false)
      setIsPlaying(false)
      setError('音频加载失败')
    }

    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
    }
  }, [onTimeUpdate])

  // 播放/暂停
  const togglePlay = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
    setIsPlaying(!isPlaying)
  }, [isPlaying])

  // 跳转到指定时间
  const seekTo = useCallback((time: number) => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = time
    setCurrentTime(time)
  }, [])

  // 跳转（前进/后退）
  const skip = useCallback((seconds: number) => {
    const audio = audioRef.current
    if (!audio) return
    const newTime = Math.max(0, Math.min(audio.currentTime + seconds, duration))
    audio.currentTime = newTime
    setCurrentTime(newTime)
  }, [duration])

  // 切换倍速
  const cyclePlaybackRate = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    const currentIndex = PLAYBACK_RATES.indexOf(playbackRate)
    const nextIndex = (currentIndex + 1) % PLAYBACK_RATES.length
    const newRate = PLAYBACK_RATES[nextIndex]
    audio.playbackRate = newRate
    setPlaybackRate(newRate)
  }, [playbackRate])

  // 进度条点击
  const handleProgressClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    const newTime = percent * duration
    seekTo(newTime)
  }, [duration, seekTo])

  // 注册 seekTo 方法到 Context + window（向后兼容）
  useEffect(() => {
    registerSeekHandler(seekTo)
    ;(window as any).__audioPlayerSeekTo = seekTo
    return () => {
      delete (window as any).__audioPlayerSeekTo
    }
  }, [seekTo, registerSeekHandler])

  // 同步播放状态到 Context
  useEffect(() => {
    setContextPlaying(isPlaying)
  }, [isPlaying, setContextPlaying])

  // 同步当前时间到 Context
  useEffect(() => {
    setContextTime(currentTime)
  }, [currentTime, setContextTime])

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0
  const displayDuration = propDuration || duration

  return (
    <div className={cn(
      'rounded-2xl p-6 bg-white border border-[#E8E5E0]',
      className
    )}>
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* 顶部：封面 + 信息 + 控制 */}
      <div className="flex items-center gap-5 mb-5">
        {/* 封面艺术 */}
        <div className="w-20 h-20 rounded-xl bg-[#1E3A5F] flex items-center justify-center flex-shrink-0">
          <Mic className="w-8 h-8 text-white" />
        </div>

        {/* 播放信息 */}
        <div className="flex-1 min-w-0">
          <h3 className="text-[15px] font-medium text-[#272735] truncate">{title}</h3>
          <p className="text-[14px] text-[#6B6B6B] mt-1 truncate">{description}</p>
        </div>

        {/* 控制按钮 */}
        <div className="flex items-center gap-3">
          {/* 后退 */}
          <button
            onClick={() => skip(-10)}
            className="p-2 rounded-lg hover:bg-[#F5F3F0] transition-colors"
            title="后退 10 秒"
          >
            <SkipBack className="w-5 h-5 text-[#6B6B6B]" />
          </button>

          {/* 播放/暂停 */}
          <button
            onClick={togglePlay}
            disabled={isLoading && !error}
            className={cn(
              'w-12 h-12 rounded-full flex items-center justify-center transition-all',
              'bg-[#1E3A5F] text-white',
              'hover:bg-[#152840]',
              (isLoading && !error) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          {/* 前进 */}
          <button
            onClick={() => skip(30)}
            className="p-2 rounded-lg hover:bg-[#F5F3F0] transition-colors"
            title="前进 30 秒"
          >
            <SkipForward className="w-5 h-5 text-[#6B6B6B]" />
          </button>
        </div>
      </div>

      {/* 进度条行 */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-[13px] text-[#6B6B6B] w-12 text-right">
          {formatTime(currentTime)}
        </span>
        <div
          className="flex-1 h-1.5 bg-[#E8E5E0] rounded-full cursor-pointer relative"
          onClick={handleProgressClick}
        >
          <div
            className="absolute h-full bg-[#1E3A5F] rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-[13px] text-[#6B6B6B] w-12">
          {formatTime(displayDuration)}
        </span>
      </div>

      {/* 额外控制 */}
      <div className="flex items-center justify-between">
        {/* 倍速按钮 */}
        <button
          onClick={cyclePlaybackRate}
          className="px-3 py-1.5 rounded-md bg-[#F5F3F0] text-[13px] font-medium text-[#272735] hover:bg-[#E8E5E0] transition-colors"
        >
          {playbackRate}x
        </button>

        {/* 右侧按钮 */}
        <div className="flex items-center gap-2">
          <button
            className="p-2 rounded-lg hover:bg-[#F5F3F0] transition-colors"
            title="分享"
          >
            <Share2 className="w-4 h-4 text-[#6B6B6B]" />
          </button>
          <a
            href={audioUrl}
            download
            className="p-2 rounded-lg hover:bg-[#F5F3F0] transition-colors"
            title="下载音频"
          >
            <Download className="w-4 h-4 text-[#6B6B6B]" />
          </a>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mt-4 text-center text-[13px] text-[#9A9A9A]">
          {error} - 点击播放按钮重试
        </div>
      )}
    </div>
  )
}

/**
 * 全局跳转方法（向后兼容）
 * @deprecated 请使用 useAudioPlayer hook
 */
export function seekToTime(seconds: number) {
  const seekTo = (window as any).__audioPlayerSeekTo
  if (seekTo) {
    seekTo(seconds)
  }
}
