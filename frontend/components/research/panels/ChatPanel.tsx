/**
 * [INPUT]: 依赖 projectId, messages 数组, sessionId, 回调函数
 * [OUTPUT]: 对外提供 ChatPanel 组件
 * [POS]: components/research/panels 的中间对话面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { MessageSquare, Send, Loader2 } from 'lucide-react'

// ============================================================
// 类型定义
// ============================================================

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ChatPanelProps {
  projectId: string
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
// ChatPanel 组件
// ============================================================

export default function ChatPanel({
  projectId,
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

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedInput = inputValue.trim()
    if (!trimmedInput || isSending) return

    // 创建用户消息
    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedInput,
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
          message: trimmedInput,
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
  // 键盘事件处理
  // ============================================================

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Ctrl/Cmd + Enter 发送消息
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSendMessage(e)
    }
  }

  // ============================================================
  // 渲染
  // ============================================================

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* 消息列表区域 */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 ? (
          /* 空状态 */
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <MessageSquare className="w-12 h-12 text-gray-400 mb-4" />
            <p className="text-center">开始对话，询问关于项目材料的问题</p>
          </div>
        ) : (
          /* 消息列表 */
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2 whitespace-pre-wrap ${
                    message.role === 'user'
                      ? 'bg-purple-600 text-white rounded-2xl rounded-br-md'
                      : 'bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {/* 发送中加载状态 */}
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-2xl rounded-bl-md">
                  <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
                </div>
              </div>
            )}

            {/* 滚动锚点 */}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <form
        onSubmit={handleSendMessage}
        className="p-4 border-t border-gray-200 bg-gray-50"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={isSending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={isSending || !inputValue.trim()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          按 Enter 发送，Ctrl/Cmd + Enter 快速发送
        </p>
      </form>
    </div>
  )
}
