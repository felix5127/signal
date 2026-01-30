/**
 * [INPUT]: 依赖 lucide-react 图标
 * [OUTPUT]: 对外提供 AIAssistantCard 组件
 * [POS]: detail/ 的 AI 研究助手卡片，提供问题列表和输入框
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState } from 'react'
import { Bot, Send, ChevronRight } from 'lucide-react'

interface MainPoint {
  point: string
  explanation: string
}

interface AIAssistantCardProps {
  mainPoints?: MainPoint[]
  className?: string
  onAskQuestion?: (question: string) => void
}

// 默认问题列表
const DEFAULT_QUESTIONS = [
  '这篇文章的核心观点是什么？',
  '有哪些值得关注的技术细节？',
  '对我的工作有什么启发？',
]

export function AIAssistantCard({
  mainPoints,
  className,
  onAskQuestion,
}: AIAssistantCardProps) {
  const [inputValue, setInputValue] = useState('')

  // 从主要观点生成问题，或使用默认问题
  const questions = mainPoints && mainPoints.length > 0
    ? mainPoints.slice(0, 3).map(p => p.point)
    : DEFAULT_QUESTIONS

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && onAskQuestion) {
      onAskQuestion(inputValue.trim())
      setInputValue('')
    }
  }

  const handleQuestionClick = (question: string) => {
    if (onAskQuestion) {
      onAskQuestion(question)
    }
  }

  return (
    <div
      className={`rounded-2xl p-5 w-full bg-white border border-[rgba(0,0,0,0.06)] ${className || ''}`}
    >
      {/* 标题行 */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-[15px] font-semibold text-[#272735]">
          AI 研究助手
        </h3>
      </div>

      {/* 问题列表 */}
      <div className="space-y-2 mb-4">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => handleQuestionClick(question)}
            className="w-full text-left px-3 py-2.5 rounded-xl bg-[#FBFCFD] border border-[rgba(0,0,0,0.04)] text-[13px] text-[#6B6B6B] leading-[1.5] hover:bg-[#F6F5F2] hover:text-[#272735] transition-colors duration-200 flex items-center justify-between gap-2 group"
          >
            <span className="line-clamp-2">{question}</span>
            <ChevronRight className="w-4 h-4 flex-shrink-0 text-[#9A9A9A] group-hover:text-[#272735] transition-colors" />
          </button>
        ))}
      </div>

      {/* 输入框 */}
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="问我任何问题..."
          className="w-full px-4 py-3 pr-12 rounded-xl bg-[#FBFCFD] border border-[rgba(0,0,0,0.06)] text-[14px] text-[#272735] placeholder:text-[#9A9A9A] focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]/20 focus:border-[#1E3A5F] transition-all duration-200"
        />
        <button
          type="submit"
          disabled={!inputValue.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg flex items-center justify-center bg-[#1E3A5F] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#2A4A6F] transition-colors duration-200"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
