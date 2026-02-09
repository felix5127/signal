/**
 * [INPUT]: 依赖 projectId, messages 数组, 回调函数, useSSE Hook
 * [OUTPUT]: 对外提供 ChatPanel 组件 (NotebookLM 风格中间对话面板)
 * [POS]: components/research/panels 的中间对话面板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  MessageSquare,
  ArrowRight,
  Loader2,
  Bookmark,
  BookmarkCheck,
  Copy,
  Sparkles,
  Search,
  ExternalLink,
} from 'lucide-react'
import { useSSE } from '@/hooks/use-sse'

// ============================================================
// 类型定义
// ============================================================

export interface ChatMessage {
  id?: string
  role: 'user' | 'assistant'
  content: string
  starred?: boolean
  references?: Array<{ title: string; url: string }>
  created_at: string
}

export interface ChatPanelProps {
  projectId: string
  projectName: string
  sourceCount: number
  messages: ChatMessage[]
  onMessagesChange: (messages: ChatMessage[]) => void
  onRefreshMessages: () => Promise<void>
}

// ============================================================
// API 配置
// ============================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SUGGESTED_QUESTIONS = [
  '总结这些来源的核心观点',
  '这些内容之间有什么关联？',
  '找出最重要的3个洞见',
]

// ============================================================
// 工具名称映射
// ============================================================

const TOOL_LABELS: Record<string, string> = {
  search_vectors: '搜索项目材料',
  search_fulltext: '全文搜索',
  tavily_search: '搜索网络',
  read_source_content: '阅读来源',
}

// ============================================================
// 子组件: 建议问题卡片
// ============================================================

function ExpandableQuestion({ question, onClick }: { question: string; onClick: () => void }) {
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
// 子组件: 工具调用指示器
// ============================================================

function ToolIndicator({ tools }: { tools: string[] }) {
  if (tools.length === 0) return null

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-[#F0FDF4] rounded-lg border border-green-200 mb-2">
      <Search className="w-3.5 h-3.5 text-green-600 animate-pulse" />
      <span className="text-xs text-green-700">
        {tools.map(t => TOOL_LABELS[t] || t).join('、')}
      </span>
    </div>
  )
}

// ============================================================
// 子组件: 参考来源列表
// ============================================================

function ReferenceList({ references }: { references: Array<{ title: string; url: string }> }) {
  if (references.length === 0) return null

  return (
    <div className="mt-3 px-3 py-2 bg-gray-50 rounded-lg border border-gray-100">
      <p className="text-xs font-medium text-gray-500 mb-2">参考来源</p>
      <div className="space-y-1">
        {references.map((ref, i) => (
          <a
            key={i}
            href={ref.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-[#1E3A5F] hover:underline"
          >
            <ExternalLink className="w-3 h-3 shrink-0" />
            <span className="line-clamp-1">{ref.title}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// 子组件: 消息气泡
// ============================================================

function MessageBubble({
  message,
  isStreaming = false,
  activeTools = [],
  onStar,
  onCopy,
}: {
  message: ChatMessage
  isStreaming?: boolean
  activeTools?: string[]
  onStar?: () => void
  onCopy?: () => void
}) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[85%] ${isUser ? '' : 'space-y-1'}`}>
        {/* 工具调用指示 */}
        {!isUser && <ToolIndicator tools={activeTools} />}

        <div
          className={`
            px-4 py-3 rounded-2xl
            ${isUser
              ? 'bg-[#1E3A5F] text-white rounded-br-md'
              : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md shadow-sm'
            }
          `}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap" style={{ lineHeight: '1.6' }}>
              {message.content}
            </p>
          ) : (
            <div
              className="prose prose-sm max-w-none
                prose-headings:text-[#272735] prose-headings:font-semibold
                prose-p:text-gray-700 prose-p:leading-[1.8]
                prose-a:text-[#1E3A5F] prose-a:no-underline hover:prose-a:underline
                prose-code:text-[#1E3A5F] prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded
                prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200
                prose-li:text-gray-700 prose-strong:text-[#272735]"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-1.5 h-4 bg-[#1E3A5F] animate-pulse rounded-sm ml-0.5" />
              )}
            </div>
          )}
        </div>

        {/* 参考来源 */}
        {!isUser && !isStreaming && message.references && message.references.length > 0 && (
          <ReferenceList references={message.references} />
        )}

        {/* 操作按钮 */}
        {!isUser && !isStreaming && message.content && (
          <div className="flex items-center gap-2 px-1 pt-1">
            {message.id && (
              <button
                onClick={onStar}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500
                  hover:text-[#1E3A5F] hover:bg-gray-100 rounded-lg transition-colors"
              >
                {message.starred ? (
                  <BookmarkCheck className="w-3.5 h-3.5 text-[#8B5CF6]" />
                ) : (
                  <Bookmark className="w-3.5 h-3.5" />
                )}
                {message.starred ? '已收藏' : '收藏'}
              </button>
            )}
            <button
              onClick={onCopy}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500
                hover:text-[#1E3A5F] hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              复制
            </button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

// ============================================================
// 主组件: ChatPanel
// ============================================================

export default function ChatPanel({
  projectId,
  projectName,
  sourceCount,
  messages,
  onMessagesChange,
  onRefreshMessages,
}: ChatPanelProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wasStreamingRef = useRef(false)

  const sendingRef = useRef(false)
  const sse = useSSE()

  // ============================================================
  // 自动滚动到最新消息
  // ============================================================

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, sse.content, scrollToBottom])

  // ============================================================
  // 流式结束处理: 刷新消息获取服务端 ID
  // ============================================================

  useEffect(() => {
    const wasStreaming = wasStreamingRef.current
    wasStreamingRef.current = sse.isStreaming

    if (wasStreaming && !sse.isStreaming) {
      sendingRef.current = false
      onRefreshMessages()
    }
  }, [sse.isStreaming, onRefreshMessages])

  // ============================================================
  // 发送消息
  // ============================================================

  const handleSendMessage = async (content?: string) => {
    const text = content || inputValue.trim()
    if (!text || sse.isStreaming || sendingRef.current) return

    // 防止双击重复发送
    sendingRef.current = true

    // 乐观添加用户消息
    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    onMessagesChange([...messages, userMessage])
    setInputValue('')

    // 启动 SSE 流式对话
    sse.start(`${API_URL}/api/research/projects/${projectId}/chat`, {
      message: text,
    })
  }

  // ============================================================
  // 收藏消息
  // ============================================================

  const handleStarMessage = async (messageId: string) => {
    try {
      const res = await fetch(
        `${API_URL}/api/research/projects/${projectId}/messages/${messageId}/star`,
        { method: 'POST' }
      )
      if (res.ok) {
        const updated = await res.json()
        onMessagesChange(
          messages.map(m =>
            m.id === messageId ? { ...m, starred: updated.starred } : m
          )
        )
      }
    } catch {
      // 收藏为非关键操作，静默失败
    }
  }

  // ============================================================
  // 复制消息内容
  // ============================================================

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
    } catch {
      // 剪贴板在非安全上下文中不可用，静默失败
    }
  }

  // ============================================================
  // 渲染
  // ============================================================

  return (
    <div className="flex-1 flex flex-col h-full bg-[#FBFCFD] overflow-hidden">
      {/* Header */}
      <div className="px-10 pt-8 pb-0 bg-[#FBFCFD]">
        <h2 className="font-semibold text-[#272735] text-base">对话</h2>
      </div>

      {/* 消息列表区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && !sse.isStreaming ? (
          /* 空状态 — 欢迎界面 */
          <div className="h-full flex flex-col items-center pt-6 max-w-2xl mx-auto">
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

            <div className="w-full space-y-3">
              <p className="text-sm text-[#9A9A9A] text-center mb-4">试着问问这些问题</p>
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <ExpandableQuestion key={i} question={q} onClick={() => handleSendMessage(q)} />
              ))}
            </div>
          </div>
        ) : (
          /* 消息列表 + 流式消息 */
          <div className="space-y-6 max-w-3xl mx-auto">
            {/* 已持久化的消息 */}
            {messages.map((msg, i) => (
              <MessageBubble
                key={msg.id || i}
                message={msg}
                onStar={msg.id ? () => handleStarMessage(msg.id!) : undefined}
                onCopy={() => handleCopyMessage(msg.content)}
              />
            ))}

            {/* 流式 AI 回复 — 不在 messages 数组中，避免 ID 管理复杂性 */}
            {sse.isStreaming && (
              sse.content ? (
                <MessageBubble
                  message={{
                    role: 'assistant',
                    content: sse.content,
                    references: sse.references,
                    created_at: '',
                  }}
                  isStreaming
                  activeTools={sse.activeTools}
                />
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                    <div className="flex items-center gap-2">
                      {sse.activeTools.length > 0 ? (
                        <>
                          <Search className="w-4 h-4 text-green-600 animate-pulse" />
                          <span className="text-sm text-gray-500">
                            {sse.activeTools.map(t => TOOL_LABELS[t] || t).join('、')}...
                          </span>
                        </>
                      ) : (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-[#1E3A5F]" />
                          <span className="text-sm text-gray-500">正在思考...</span>
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            )}

            {/* 错误提示 — 内联显示，非持久化 */}
            {sse.error && !sse.isStreaming && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-red-50 border border-red-200 px-4 py-3 rounded-2xl rounded-bl-md">
                  <p className="text-sm text-red-600">抱歉，发生了错误。请稍后重试。</p>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
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
              disabled={sse.isStreaming}
              className="flex-1 bg-transparent outline-none text-[#272735] text-[15px]
                disabled:opacity-50 disabled:cursor-not-allowed
                placeholder:text-[#9A9A9A]"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={sse.isStreaming || !inputValue.trim()}
              className="ml-3 w-8 h-8 rounded-full bg-[#1E3A5F] text-white
                flex items-center justify-center shrink-0
                hover:bg-[#1E3A5F]/90 transition-colors
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sse.isStreaming ? (
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
