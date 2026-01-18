/**
 * [INPUT]: 依赖 /api/research/* 获取项目数据、执行研究、对话
 * [OUTPUT]: 对外提供研究工作台主组件
 * [POS]: components/research 的核心工作台组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import {
  ArrowLeft,
  FileText,
  MessageSquare,
  Search,
  Upload,
  Trash2,
  Loader2,
  Send,
  BookOpen,
  Link as LinkIcon,
  Plus,
  X,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { fadeInUp } from '@/lib/motion'

// ============================================================
// 类型定义
// ============================================================

interface Project {
  id: string
  name: string
  description: string | null
  status: string
  source_count: number
  output_count: number
  created_at: string
  updated_at: string
}

interface Source {
  id: string
  project_id: string
  source_type: 'url' | 'pdf' | 'audio' | 'video' | 'text'
  title: string | null
  original_url: string | null
  processing_status: string
  created_at: string
}

interface Output {
  id: string
  output_type: string
  title: string
  created_at: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ResearchProgress {
  phase: string
  message: string
  progress: number
  data?: { output?: string }
}

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 工作台组件
// ============================================================

export default function Workspace({ projectId }: { projectId: string }) {
  const apiUrl = getApiUrl()

  // 状态
  const [project, setProject] = useState<Project | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [outputs, setOutputs] = useState<Output[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'sources' | 'research' | 'chat' | 'outputs'>('sources')

  // 研究状态
  const [researchQuery, setResearchQuery] = useState('')
  const [researching, setResearching] = useState(false)
  const [researchProgress, setResearchProgress] = useState<ResearchProgress | null>(null)
  const [researchResult, setResearchResult] = useState<string | null>(null)

  // 对话状态
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatting, setChatting] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // 源材料上传
  const [showAddSource, setShowAddSource] = useState(false)
  const [newSourceUrl, setNewSourceUrl] = useState('')
  const [newSourceText, setNewSourceText] = useState('')
  const [addingSource, setAddingSource] = useState(false)

  // ============================================================
  // 数据获取
  // ============================================================

  const fetchProject = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}`)
      if (res.ok) {
        const data = await res.json()
        setProject(data)
      }
    } catch (e) {
      console.error('Failed to fetch project:', e)
    }
  }, [apiUrl, projectId])

  const fetchSources = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/sources`)
      if (res.ok) {
        const data = await res.json()
        setSources(data)
      }
    } catch (e) {
      console.error('Failed to fetch sources:', e)
    }
  }, [apiUrl, projectId])

  const fetchOutputs = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/outputs`)
      if (res.ok) {
        const data = await res.json()
        setOutputs(data)
      }
    } catch (e) {
      console.error('Failed to fetch outputs:', e)
    }
  }, [apiUrl, projectId])

  useEffect(() => {
    Promise.all([fetchProject(), fetchSources(), fetchOutputs()])
      .finally(() => setLoading(false))
  }, [fetchProject, fetchSources, fetchOutputs])

  // ============================================================
  // 源材料管理
  // ============================================================

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault()
    setAddingSource(true)

    try {
      const body: { source_type: string; original_url?: string; content?: string; title?: string } = {
        source_type: newSourceUrl ? 'url' : 'text',
      }

      if (newSourceUrl) {
        body.original_url = newSourceUrl
        body.title = new URL(newSourceUrl).hostname
      } else if (newSourceText) {
        body.content = newSourceText
        body.title = newSourceText.substring(0, 50) + '...'
      }

      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (res.ok) {
        const source = await res.json()
        setSources(prev => [source, ...prev])
        setNewSourceUrl('')
        setNewSourceText('')
        setShowAddSource(false)
        fetchProject() // 刷新项目统计
      }
    } catch (e) {
      console.error('Failed to add source:', e)
    } finally {
      setAddingSource(false)
    }
  }

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm('确定要删除这个源材料吗？')) return

    try {
      const res = await fetch(`${apiUrl}/api/research/sources/${sourceId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        setSources(prev => prev.filter(s => s.id !== sourceId))
        fetchProject() // 刷新项目统计
      }
    } catch (e) {
      console.error('Failed to delete source:', e)
    }
  }

  // ============================================================
  // 研究功能 (SSE)
  // ============================================================

  const handleStartResearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!researchQuery.trim() || researching) return

    setResearching(true)
    setResearchProgress(null)
    setResearchResult(null)

    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: researchQuery,
          include_web_search: true,
          max_iterations: 5,
        }),
      })

      if (!res.ok) {
        throw new Error('Research request failed')
      }

      // SSE 流式读取
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
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
            const eventType = line.slice(7)
            continue
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.phase) {
                setResearchProgress(data)
              }

              if (data.output) {
                setResearchResult(data.output)
                fetchOutputs() // 刷新输出列表
              }

              if (data.error) {
                console.error('Research error:', data.error)
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (e) {
      console.error('Research failed:', e)
    } finally {
      setResearching(false)
    }
  }

  // ============================================================
  // 对话功能
  // ============================================================

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || chatting) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    }

    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setChatting(true)

    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setSessionId(data.session_id)

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
        }
        setChatMessages(prev => [...prev, assistantMessage])
      }
    } catch (e) {
      console.error('Chat failed:', e)
    } finally {
      setChatting(false)
    }
  }

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // ============================================================
  // 渲染
  // ============================================================

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">项目不存在</h2>
          <Link href="/research/projects" className="text-purple-600 hover:underline mt-2 inline-block">
            返回项目列表
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/research/projects"
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{project.name}</h1>
                <p className="text-sm text-gray-500">
                  {sources.length} 个源材料 · {outputs.length} 份输出
                </p>
              </div>
            </div>
          </div>

          {/* 标签栏 */}
          <div className="flex gap-1 mt-4 -mb-px">
            {[
              { key: 'sources', label: '源材料', icon: FileText },
              { key: 'research', label: '研究', icon: Search },
              { key: 'chat', label: '对话', icon: MessageSquare },
              { key: 'outputs', label: '输出', icon: BookOpen },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === key
                    ? 'bg-gray-50 text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* 内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <AnimatePresence mode="wait">
          {/* 源材料标签 */}
          {activeTab === 'sources' && (
            <motion.div
              key="sources"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">源材料</h2>
                <button
                  onClick={() => setShowAddSource(true)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  添加
                </button>
              </div>

              {sources.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">还没有源材料</h3>
                  <p className="text-gray-500 mb-4">添加 URL、文本或上传文件作为研究素材</p>
                  <button
                    onClick={() => setShowAddSource(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Plus className="w-5 h-5" />
                    添加源材料
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {sources.map((source) => (
                    <div
                      key={source.id}
                      className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                          {source.source_type === 'url' ? (
                            <LinkIcon className="w-5 h-5 text-purple-600" />
                          ) : (
                            <FileText className="w-5 h-5 text-purple-600" />
                          )}
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {source.title || '未命名'}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {source.source_type} · {source.processing_status}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteSource(source.id)}
                        className="p-2 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-5 h-5 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* 添加源材料弹窗 */}
              {showAddSource && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-semibold">添加源材料</h2>
                      <button
                        onClick={() => setShowAddSource(false)}
                        className="p-2 rounded-lg hover:bg-gray-100"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <form onSubmit={handleAddSource}>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            URL 链接
                          </label>
                          <input
                            type="url"
                            value={newSourceUrl}
                            onChange={(e) => setNewSourceUrl(e.target.value)}
                            placeholder="https://..."
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          />
                        </div>

                        <div className="text-center text-gray-500 text-sm">或</div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            文本内容
                          </label>
                          <textarea
                            value={newSourceText}
                            onChange={(e) => setNewSourceText(e.target.value)}
                            placeholder="粘贴文本内容..."
                            rows={4}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                          />
                        </div>
                      </div>

                      <div className="flex gap-3 mt-6">
                        <button
                          type="button"
                          onClick={() => setShowAddSource(false)}
                          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          取消
                        </button>
                        <button
                          type="submit"
                          disabled={addingSource || (!newSourceUrl && !newSourceText)}
                          className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                          {addingSource ? (
                            <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                          ) : (
                            '添加'
                          )}
                        </button>
                      </div>
                    </form>
                  </motion.div>
                </div>
              )}
            </motion.div>
          )}

          {/* 研究标签 */}
          {activeTab === 'research' && (
            <motion.div
              key="research"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4">发起研究</h2>

                <form onSubmit={handleStartResearch}>
                  <textarea
                    value={researchQuery}
                    onChange={(e) => setResearchQuery(e.target.value)}
                    placeholder="输入你想研究的问题，AI 将搜索项目材料和网络资源，生成深度研究报告..."
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    disabled={researching}
                  />

                  <button
                    type="submit"
                    disabled={researching || !researchQuery.trim()}
                    className="mt-4 w-full px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {researching ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        研究中...
                      </>
                    ) : (
                      <>
                        <Search className="w-5 h-5" />
                        开始研究
                      </>
                    )}
                  </button>
                </form>

                {/* 研究进度 */}
                {researchProgress && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      {researchProgress.phase === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      ) : (
                        <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                      )}
                      <span className="font-medium">{researchProgress.message}</span>
                    </div>
                    <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                      <motion.div
                        className="bg-purple-600 h-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${researchProgress.progress * 100}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  </div>
                )}

                {/* 研究结果 */}
                {researchResult && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">研究报告</h3>
                    <div className="prose prose-purple max-w-none p-4 bg-gray-50 rounded-lg">
                      <div dangerouslySetInnerHTML={{ __html: researchResult.replace(/\n/g, '<br>') }} />
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* 对话标签 */}
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col h-[calc(100vh-200px)]"
            >
              <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
                {/* 消息列表 */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatMessages.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p>开始对话，询问关于项目材料的问题</p>
                    </div>
                  ) : (
                    chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                            msg.role === 'user'
                              ? 'bg-purple-600 text-white rounded-br-md'
                              : 'bg-gray-100 text-gray-900 rounded-bl-md'
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))
                  )}
                  {chatting && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 px-4 py-2 rounded-2xl rounded-bl-md">
                        <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* 输入框 */}
                <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="输入消息..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      disabled={chatting}
                    />
                    <button
                      type="submit"
                      disabled={chatting || !chatInput.trim()}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          )}

          {/* 输出标签 */}
          {activeTab === 'outputs' && (
            <motion.div
              key="outputs"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <h2 className="text-lg font-semibold mb-6">研究输出</h2>

              {outputs.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                  <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">还没有研究输出</h3>
                  <p className="text-gray-500">发起研究后，AI 生成的报告会显示在这里</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {outputs.map((output) => (
                    <div
                      key={output.id}
                      className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                          <BookOpen className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">{output.title}</h4>
                          <p className="text-sm text-gray-500">
                            {output.output_type} · {new Date(output.created_at).toLocaleString('zh-CN')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
