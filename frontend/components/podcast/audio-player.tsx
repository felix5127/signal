/**
 * [INPUT]: 依赖 lucide-react, @/lib/utils, ./utils, ./audio-player-context
 * [OUTPUT]: 对外提供 AudioPlayer 组件, seekToTime 函数
 * [POS]: podcast/ 的音频播放器组件，支持时间戳跳转
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Play, Pause, Volume2, VolumeX, Download, SkipBack, SkipForward, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatTime } from './utils'
import { useAudioPlayer } from './audio-player-context'

interface AudioPlayerProps {
  audioUrl: string
  duration?: number // 总时长（秒）
  onTimeUpdate?: (currentTime: number) => void
  className?: string
}

// 速度选项
const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

export function AudioPlayer({
  audioUrl,
  duration: propDuration,
  onTimeUpdate,
  className,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const { registerSeekHandler, setCurrentTime: setContextTime, setIsPlaying: setContextPlaying } = useAudioPlayer()
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(propDuration || 0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
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
      const errorCode = audio.error?.code
      switch (errorCode) {
        case MediaError.MEDIA_ERR_ABORTED:
          setError('播放被中断')
          break
        case MediaError.MEDIA_ERR_NETWORK:
          setError('网络错误，无法加载音频')
          break
        case MediaError.MEDIA_ERR_DECODE:
          setError('音频解码失败')
          break
        case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          setError('不支持的音频格式')
          break
        default:
          setError('音频加载失败')
      }
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

  // 调节音量
  const handleVolumeChange = useCallback((newVolume: number) => {
    const audio = audioRef.current
    if (!audio) return
    audio.volume = newVolume
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }, [])

  // 静音切换
  const toggleMute = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    if (isMuted) {
      audio.volume = volume || 1
      setIsMuted(false)
    } else {
      audio.volume = 0
      setIsMuted(true)
    }
  }, [isMuted, volume])

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
    // 向后兼容：仍然挂载到 window
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

  // 错误状态显示
  if (error) {
    return (
      <div className={cn('rounded-xl p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800', className)}>
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-300">{error}</p>
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">请检查音频链接或稍后重试</p>
          </div>
          <a
            href={audioUrl}
            download
            className="px-3 py-1.5 text-sm rounded-lg bg-red-100 dark:bg-red-800/50 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
          >
            下载音频
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('rounded-xl p-4 bg-gray-50 dark:bg-gray-800', className)}>
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* 进度条 */}
      <div
        className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer mb-4 group"
        onClick={handleProgressClick}
      >
        <div
          className="absolute h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-md border-2 border-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: `calc(${progress}% - 8px)` }}
        />
      </div>

      {/* 时间显示 */}
      <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* 控制按钮 */}
      <div className="flex items-center justify-between">
        {/* 左侧：播放控制 */}
        <div className="flex items-center gap-2">
          {/* 后退 10 秒 */}
          <button
            onClick={() => skip(-10)}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="后退 10 秒"
          >
            <SkipBack className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>

          {/* 播放/暂停 */}
          <button
            onClick={togglePlay}
            disabled={isLoading}
            className={cn(
              'p-3 rounded-full transition-all',
              'bg-gradient-to-r from-indigo-500 to-purple-500 text-white',
              'hover:shadow-lg hover:scale-105 active:scale-95',
              isLoading && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isPlaying ? (
              <Pause className="w-6 h-6" />
            ) : (
              <Play className="w-6 h-6 ml-0.5" />
            )}
          </button>

          {/* 前进 30 秒 */}
          <button
            onClick={() => skip(30)}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="前进 30 秒"
          >
            <SkipForward className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* 中间：倍速 */}
        <button
          onClick={cyclePlaybackRate}
          className="px-3 py-1.5 rounded-lg bg-gray-200 dark:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          {playbackRate}x
        </button>

        {/* 右侧：音量和下载 */}
        <div className="flex items-center gap-2">
          {/* 音量 */}
          <div className="flex items-center gap-1">
            <button
              onClick={toggleMute}
              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              {isMuted ? (
                <VolumeX className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              ) : (
                <Volume2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              className="w-20 h-1 accent-indigo-500"
            />
          </div>

          {/* 下载 */}
          <a
            href={audioUrl}
            download
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="下载音频"
          >
            <Download className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </a>
        </div>
      </div>
    </div>
  )
}

/**
 * 全局跳转方法（向后兼容）
 * 推荐使用 useAudioPlayer().seekTo 代替
 * @deprecated 请使用 useAudioPlayer hook
 */
export function seekToTime(seconds: number) {
  // 保留 window 方式作为备选，确保向后兼容
  const seekTo = (window as any).__audioPlayerSeekTo
  if (seekTo) {
    seekTo(seconds)
  }
}

// 为了向后兼容，仍然挂载到 window（将在未来版本移除）
if (typeof window !== 'undefined') {
  // 动态注入，由 AudioPlayer 组件在挂载时设置
}
