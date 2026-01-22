/**
 * [INPUT]: 依赖 React Context API
 * [OUTPUT]: 对外提供 AudioPlayerProvider, useAudioPlayer
 * [POS]: podcast/ 的音频播放器上下文，替代全局 window 对象
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

// ============================================================================
// 类型定义
// ============================================================================

interface AudioPlayerContextValue {
  /** 跳转到指定时间 */
  seekTo: (seconds: number) => void
  /** 注册 seekTo 回调（由 AudioPlayer 调用） */
  registerSeekHandler: (handler: (seconds: number) => void) => void
  /** 当前播放时间 */
  currentTime: number
  /** 更新当前播放时间 */
  setCurrentTime: (time: number) => void
  /** 是否正在播放 */
  isPlaying: boolean
  /** 设置播放状态 */
  setIsPlaying: (playing: boolean) => void
}

// ============================================================================
// Context 定义
// ============================================================================

const AudioPlayerContext = createContext<AudioPlayerContextValue | null>(null)

// ============================================================================
// Provider 组件
// ============================================================================

interface AudioPlayerProviderProps {
  children: ReactNode
}

export function AudioPlayerProvider({ children }: AudioPlayerProviderProps) {
  const [seekHandler, setSeekHandler] = useState<((seconds: number) => void) | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const registerSeekHandler = useCallback((handler: (seconds: number) => void) => {
    setSeekHandler(() => handler)
  }, [])

  const seekTo = useCallback((seconds: number) => {
    if (seekHandler) {
      seekHandler(seconds)
    }
  }, [seekHandler])

  return (
    <AudioPlayerContext.Provider
      value={{
        seekTo,
        registerSeekHandler,
        currentTime,
        setCurrentTime,
        isPlaying,
        setIsPlaying,
      }}
    >
      {children}
    </AudioPlayerContext.Provider>
  )
}

// ============================================================================
// Hook
// ============================================================================

export function useAudioPlayer() {
  const context = useContext(AudioPlayerContext)
  if (!context) {
    // 返回 no-op 实现，避免在 Provider 外部使用时报错
    return {
      seekTo: () => {},
      registerSeekHandler: () => {},
      currentTime: 0,
      setCurrentTime: () => {},
      isPlaying: false,
      setIsPlaying: () => {},
    }
  }
  return context
}
