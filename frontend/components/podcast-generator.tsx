/**
 * [INPUT]: 依赖 React useState/useEffect、lucide-react 图标、framer-motion 动画
 * [OUTPUT]: 对外提供播客生成组件，支持 SSE 进度流和音频播放
 * [POS]: components/ 的播客生成交互组件，可被 resource-detail.tsx 或研究工作台消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  Loader2,
  Play,
  Pause,
  CheckCircle2,
  AlertCircle,
  Volume2,
  Download,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

interface PodcastGeneratorProps {
  content: string
  title?: string
  outputId?: string  // 用于从研究输出生成
  targetDuration?: number
  onComplete?: (audioUrl: string) => void
}

interface Voice {
  id: string
  name: string
  gender: 'male' | 'female'
  language: string
  description: string
}

interface ProgressEvent {
  phase: string
  message: string
  progress: number
  title?: string
  sections?: number
  turns?: number
  word_count?: number
  audio_path?: string
  duration_seconds?: number
}

type GeneratorStatus = 'idle' | 'loading' | 'generating' | 'completed' | 'error'

// ============================================================
// 常量配置
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const DEFAULT_VOICES: Voice[] = [
  { id: 'longxiaochun', name: '龙小淳', gender: 'male', language: 'zh', description: '温和男声' },
  { id: 'longlaotie', name: '龙老铁', gender: 'male', language: 'zh', description: '成熟男声' },
  { id: 'longxiaoxia', name: '龙小夏', gender: 'female', language: 'zh', description: '温柔女声' },
  { id: 'longwan', name: '龙婉', gender: 'female', language: 'zh', description: '甜美女声' },
  { id: 'kenny', name: 'Kenny', gender: 'male', language: 'en', description: '美式男声' },
  { id: 'rosa', name: 'Rosa', gender: 'female', language: 'en', description: '美式女声' },
]

const buttonStyles = {
  default: {
    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
    hoverBoxShadow: '0 6px 20px rgba(139, 92, 246, 0.45), inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -1px 0 rgba(0,0,0,0.15)',
  },
  loading: {
    background: '#9ca3af',
    boxShadow: '0 4px 12px rgba(156, 163, 175, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
  success: {
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.35), inset 0 1px 0 rgba(255,255,255,0.2), inset 0 -1px 0 rgba(0,0,0,0.1)',
  },
}

// ============================================================
// 播客生成组件
// ============================================================

export default function PodcastGenerator({
  content,
  title,
  outputId,
  targetDuration = 600,
  onComplete,
}: PodcastGeneratorProps) {
  // 状态管理
  const [status, setStatus] = useState<GeneratorStatus>('idle')
  const [progress, setProgress] = useState<ProgressEvent | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  // 音色选择
  const [hostVoice, setHostVoice] = useState('longxiaochun')
  const [guestVoice, setGuestVoice] = useState('longxiaoxia')

  // 音频引用
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // ============================================================
  // SSE 流式生成
  // ============================================================

  const generatePodcast = useCallback(async () => {
    setStatus('loading')
    setError(null)
    setProgress(null)

    try {
      const response = await fetch(`${API_URL}/api/podcast/generate/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          title,
          target_duration: targetDuration,
          host_voice: hostVoice,
          guest_voice: guestVoice,
        }),
      })

      if (!response.ok) {
        throw new Error(`生成失败 (${response.status})`)
      }

      setStatus('generating')

      // 读取 SSE 流
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim()
            continue
          }

          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.error) {
                setError(data.error)
                setStatus('error')
                return
              }

              // 更新进度
              setProgress(data)

              // 检查完成
              if (data.phase === 'completed' && data.audio_path) {
                // 等待 result 事件获取 URL
              }
            } catch (e) {
              console.error('解析 SSE 数据失败:', e)
            }
          }
        }
      }

      // 如果有音频 URL，设置完成状态
      if (progress?.audio_path) {
        setAudioUrl(progress.audio_path)
        setStatus('completed')
        onComplete?.(progress.audio_path)
      }

    } catch (e: any) {
      console.error('播客生成失败:', e)
      setError(e.message || '生成失败，请重试')
      setStatus('error')
    }
  }, [content, title, targetDuration, hostVoice, guestVoice, onComplete, progress])

  // ============================================================
  // 音频控制
  // ============================================================

  const togglePlay = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleAudioEnded = () => {
    setIsPlaying(false)
  }

  // ============================================================
  // 渲染
  // ============================================================

  const baseButtonClass = "inline-flex items-center gap-2 px-6 py-3 rounded-xl border-none font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.97]"

  return (
    <div className="space-y-4">
      {/* 主按钮 */}
      {status === 'idle' && (
        <div>
          <button
            onClick={generatePodcast}
            className={`${baseButtonClass} text-white cursor-pointer`}
            style={buttonStyles.default}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = buttonStyles.default.hoverBoxShadow
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = buttonStyles.default.boxShadow
            }}
          >
            <Mic className="w-4 h-4" />
            生成播客
          </button>

          {/* 设置展开按钮 */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="ml-3 text-gray-500 hover:text-gray-700 transition-colors"
          >
            {showSettings ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      )}

      {/* 音色设置 */}
      <AnimatePresence>
        {showSettings && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-50 rounded-xl p-4 space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              {/* 主持人音色 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  主持人音色
                </label>
                <select
                  value={hostVoice}
                  onChange={(e) => setHostVoice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {DEFAULT_VOICES.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} - {voice.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* 嘉宾音色 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  嘉宾音色
                </label>
                <select
                  value={guestVoice}
                  onChange={(e) => setGuestVoice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {DEFAULT_VOICES.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} - {voice.description}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 加载状态 */}
      {status === 'loading' && (
        <button
          disabled
          className={`${baseButtonClass} text-white cursor-not-allowed`}
          style={buttonStyles.loading}
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          准备生成...
        </button>
      )}

      {/* 生成中进度 */}
      {status === 'generating' && progress && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          {/* 进度头部 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-gray-700">
                {progress.message}
              </span>
            </div>
            <span className="text-sm text-gray-500">
              {Math.round(progress.progress * 100)}%
            </span>
          </div>

          {/* 进度条 */}
          <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
            <motion.div
              className="bg-purple-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress.progress * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* 阶段信息 */}
          <div className="flex flex-wrap gap-4 text-xs text-gray-500">
            {progress.title && (
              <span>标题: {progress.title}</span>
            )}
            {progress.sections && (
              <span>章节: {progress.sections}</span>
            )}
            {progress.turns && (
              <span>对话轮次: {progress.turns}</span>
            )}
            {progress.word_count && (
              <span>字数: {progress.word_count}</span>
            )}
          </div>
        </div>
      )}

      {/* 完成状态 - 音频播放器 */}
      {status === 'completed' && audioUrl && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-purple-700">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-semibold">播客生成完成</span>
            </div>
            {progress?.duration_seconds && (
              <span className="text-sm text-gray-500">
                时长: {Math.floor(progress.duration_seconds / 60)}分{progress.duration_seconds % 60}秒
              </span>
            )}
          </div>

          {/* 音频播放器 */}
          <div className="flex items-center gap-4">
            <button
              onClick={togglePlay}
              className="w-12 h-12 bg-purple-600 hover:bg-purple-700 text-white rounded-full flex items-center justify-center transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5 ml-0.5" />
              )}
            </button>

            <div className="flex-1">
              <audio
                ref={audioRef}
                src={audioUrl}
                onEnded={handleAudioEnded}
                className="w-full"
                controls
              />
            </div>

            <a
              href={audioUrl}
              download
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              title="下载播客"
            >
              <Download className="w-5 h-5" />
            </a>
          </div>

          {/* 重新生成按钮 */}
          <div className="mt-4 pt-4 border-t border-purple-200">
            <button
              onClick={() => {
                setStatus('idle')
                setAudioUrl(null)
                setProgress(null)
              }}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              重新生成
            </button>
          </div>
        </div>
      )}

      {/* 错误状态 */}
      {status === 'error' && error && (
        <div className="bg-red-50 rounded-xl border border-red-200 p-4">
          <div className="flex items-center gap-2 text-red-700 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">生成失败</span>
          </div>
          <p className="text-sm text-red-600 mb-3">{error}</p>
          <button
            onClick={() => {
              setStatus('idle')
              setError(null)
            }}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            重试
          </button>
        </div>
      )}
    </div>
  )
}
