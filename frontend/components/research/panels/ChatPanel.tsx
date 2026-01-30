/**
 * [INPUT]: 依赖 projectId, messages 数组, sessionId, 回调函数
 * [OUTPUT]: 对外提供 ChatPanel 组件 (NotebookLM 风格中间对话面板)
 * [POS]: components/research/panels 的中间对话面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare,
  ArrowRight,
  Loader2,
  Bookmark,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Map,
} from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  saved?: boolean
}

export interface ChatPanelProps {
  projectId: string
  projectName: string
  sourceCount: number
  messages: ChatMessage[]
  onMessagesChange: (messages: ChatMessage[]) => void
  sessionId: string | null
  onSessionIdChange: (id: string | null) => void
}

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 可展开问题卡片
// ============================================================

interface ExpandableQuestionProps {
  question: string
  onClick: () => void
}

function ExpandableQuestion({ question, onClick }: ExpandableQuestionProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 bg-white rounded-xl border border-gray-200
        hover:border-[#1E3A5F]/30 hover:shadow-sm transition-all group"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#1E3A5F]/5 flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-[#1E3A5F]" />
        </div>
        <p className="text-sm text-gray-700 group-hover:text-[#1E3A5F] transition-colors line-clamp-2">
          {question}
        </p>
      </div>
    </button>
  )
}

// ============================================================
// 消息气泡组件
// ============================================================

interface MessageBubbleProps {
  message: ChatMessage
  onSave?: () => void
  onCopy?: () => void
  onLike?: () => void
}

function MessageBubble({ message, onSave, onCopy, onLike }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[85%] ${isUser ? '' : 'space-y-3'}`}>
        <div
          className={`
            px-4 py-3 rounded-2xl whitespace-pre-wrap leading-relaxed
            ${isUser
              ? 'bg-[#1E3A5F] text-white rounded-br-md'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md shadow-sm'
            }
          `}
          style={{ lineHeight: isUser ? '1.6' : '1.8' }}
        >
          {message.content}
        </div>

        {/* AI 消息操作按钮 */}
        {!isUser && (
          <div className="flex items-center gap-2 px-1">
            <button
              onClick={onSave}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500
                hover:text-[#1E3A5F] hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Bookmark className="w-3.5 h-3.5" />
              保存到笔记
            </button>
            <button
              onClick={onCopy}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500
                hover:text-[#1E3A5F] hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              复制
            </button>
            <button
              onClick={onLike}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500
                hover:text-[#1E3A5F] hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              点赞
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

// ============================================================
// ChatPanel 组件
// ============================================================

export default function ChatPanel({
  projectId,
  projectName,
  sourceCount,
  messages,
  onMessagesChange,
  sessionId,
  onSessionIdChange,
}: ChatPanelProps) {
  const apiUrl = getApiUrl()

  // 本地状态
  const [inputValue, setInputValue] = useState('')
  const [isSending, setIsSending] = useState(false)

  // 滚动控制
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // 建议问题
  const suggestedQuestions = [
    '总结这些来源的核心观点',
    '这些内容之间有什么关联？',
    '找出最重要的3个洞见',
  ]

  // ============================================================
  // 自动滚动到最新消息
  // ============================================================

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // ============================================================
  // 发送消息
  // ============================================================

  const handleSendMessage = async (content?: string) => {
    const messageContent = content || inputValue.trim()
    if (!messageContent || isSending) return

    // 创建用户消息
    const userMessage: ChatMessage = {
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
    }

    // 更新消息列表
    const updatedMessages = [...messages, userMessage]
    onMessagesChange(updatedMessages)

    // 清空输入框
    setInputValue('')
    setIsSending(true)

    try {
      const response = await fetch(`${apiUrl}/api/research/projects/${projectId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageContent,
          session_id: sessionId,
        }),
      })

      if (response.ok) {
        const data = await response.json()

        // 更新 session ID
        if (data.session_id) {
          onSessionIdChange(data.session_id)
        }

        // 创建 AI 回复消息
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
        }

        // 添加 AI 回复到消息列表
        onMessagesChange([...updatedMessages, assistantMessage])
      } else {
        // 请求失败，添加错误消息
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content: '抱歉，发生了错误。请稍后重试。',
          timestamp: new Date().toISOString(),
        }
        onMessagesChange([...updatedMessages, errorMessage])
      }
    } catch (error) {
      console.error('Chat request failed:', error)

      // 网络错误，添加错误消息
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '网络连接失败，请检查网络后重试。',
        timestamp: new Date().toISOString(),
      }
      onMessagesChange([...updatedMessages, errorMessage])
    } finally {
      setIsSending(false)
    }
  }

  // ============================================================
  // 复制消息
  // ============================================================

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
  }

  // ============================================================
  // 键盘事件处理
  // ============================================================

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter 发送，Shift+Enter 换行
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // ============================================================
  // 渲染
  // ============================================================

  return (
    <div className="flex-1 flex flex-col h-full bg-[#FBFCFD] overflow-hidden">
      {/* Header - 设计稿: 只有标题，无图标 */}
      <div className="px-10 pt-8 pb-0 bg-[#FBFCFD]">
        <h2 className="font-semibold text-[#272735] text-base">对话</h2>
      </div>

      {/* 消息列表区域 */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-6 py-6"
      >
        {messages.length === 0 ? (
          /* 空状态 - 欢迎界面 */
          <div className="h-full flex flex-col items-center pt-6 max-w-2xl mx-auto">
            {/* 标题区 */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-[#1E3A5F]
                flex items-center justify-center mx-auto mb-5">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-[#272735] mb-2">
                {projectName.startsWith('研究:') ? projectName : `研究: "${projectName}"`}
              </h3>
              <p className="text-[#9A9A9A]">
                {sourceCount > 0 ? `已添加 ${sourceCount} 个来源` : '添加来源开始研究'}
              </p>
            </div>

            {/* 建议问题 */}
            <div className="w-full space-y-3">
              <p className="text-sm text-[#9A9A9A] text-center mb-4">
                试着问问这些问题
              </p>
              {suggestedQuestions.map((question, index) => (
                <ExpandableQuestion
                  key={index}
                  question={question}
                  onClick={() => handleSendMessage(question)}
                />
              ))}
            </div>
          </div>
        ) : (
          /* 消息列表 */
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message, index) => (
              <MessageBubble
                key={index}
                message={message}
                onCopy={() => handleCopyMessage(message.content)}
              />
            ))}

            {/* 发送中加载状态 */}
            {isSending && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-[#1E3A5F]" />
                    <span className="text-sm text-gray-500">正在思考...</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 滚动锚点 */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 - 设计稿: 圆角24px, placeholder "开始输入...", 右箭头图标 */}
      <div className="px-10 py-5 bg-[#FBFCFD]">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-center bg-white border border-[#E8E5E0] rounded-3xl px-5 py-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder="开始输入..."
              disabled={isSending}
              className="flex-1 bg-transparent outline-none text-[#272735] text-[15px]
                disabled:opacity-50 disabled:cursor-not-allowed
                placeholder:text-[#9A9A9A]"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isSending || !inputValue.trim()}
              className="ml-3 w-8 h-8 rounded-full bg-[#1E3A5F] text-white
                flex items-center justify-center shrink-0
                hover:bg-[#1E3A5F]/90 transition-colors
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
