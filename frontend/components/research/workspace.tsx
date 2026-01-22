/**
 * [INPUT]: 依赖 /api/research/* 获取项目数据，panels 子组件
 * [OUTPUT]: 对外提供研究工作台主组件（三面板布局）
 * [POS]: components/research 的核心工作台组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, Menu, X } from 'lucide-react'
import { SourcesPanel, ChatPanel, ResearchPanel, type Source } from './panels'

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

interface Output {
  id: string
  output_type: string
  title: string
  content?: string
  created_at: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 工作台组件 - 三面板布局
// ============================================================

export default function Workspace({ projectId }: { projectId: string }) {
  const apiUrl = getApiUrl()

  // ============================================================
  // 核心状态
  // ============================================================
  const [project, setProject] = useState<Project | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [outputs, setOutputs] = useState<Output[]>([])
  const [loading, setLoading] = useState(true)

  // 对话状态
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)

  // 移动端侧边栏状态
  const [leftPanelOpen, setLeftPanelOpen] = useState(false)
  const [rightPanelOpen, setRightPanelOpen] = useState(false)

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
  // 状态变更回调
  // ============================================================

  const handleSourcesChange = useCallback((newSources: Source[]) => {
    setSources(newSources)
    fetchProject() // 刷新项目统计
  }, [fetchProject])

  const handleOutputsChange = useCallback((newOutputs: Output[]) => {
    setOutputs(newOutputs)
    fetchProject() // 刷新项目统计
  }, [fetchProject])

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
    <div className="h-screen flex flex-col bg-gray-50">
      {/* ================================================================ */}
      {/* 头部导航栏 */}
      {/* ================================================================ */}
      <header className="bg-white border-b border-gray-200 flex-shrink-0 z-20">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* 移动端：左侧面板切换 */}
            <button
              onClick={() => setLeftPanelOpen(!leftPanelOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Menu className="w-5 h-5 text-gray-600" />
            </button>

            <Link
              href="/research/projects"
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>

            <div>
              <h1 className="text-lg font-semibold text-gray-900 truncate max-w-[200px] sm:max-w-none">
                {project.name}
              </h1>
              <p className="text-xs text-gray-500">
                {sources.length} 个源材料 · {outputs.length} 份输出
              </p>
            </div>
          </div>

          {/* 移动端：右侧面板切换 */}
          <button
            onClick={() => setRightPanelOpen(!rightPanelOpen)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </header>

      {/* ================================================================ */}
      {/* 三面板主体 */}
      {/* ================================================================ */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* ============================================================ */}
        {/* 左侧面板 - 源材料 */}
        {/* ============================================================ */}

        {/* 移动端遮罩 */}
        {leftPanelOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setLeftPanelOpen(false)}
          />
        )}

        {/* 左侧面板 */}
        <aside
          className={`
            fixed lg:relative inset-y-0 left-0 z-40
            w-72 bg-gray-50 border-r border-gray-200
            transform transition-transform duration-300 ease-in-out
            lg:transform-none lg:flex-shrink-0
            ${leftPanelOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          {/* 移动端关闭按钮 */}
          <button
            onClick={() => setLeftPanelOpen(false)}
            className="lg:hidden absolute top-3 right-3 p-2 rounded-lg hover:bg-gray-200 z-50"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>

          <div className="h-full overflow-y-auto pt-12 lg:pt-0">
            <SourcesPanel
              projectId={projectId}
              sources={sources}
              onSourcesChange={handleSourcesChange}
            />
          </div>
        </aside>

        {/* ============================================================ */}
        {/* 中间面板 - 对话 */}
        {/* ============================================================ */}
        <main className="flex-1 min-w-0 flex flex-col">
          <ChatPanel
            projectId={projectId}
            messages={chatMessages}
            onMessagesChange={setChatMessages}
            sessionId={sessionId}
            onSessionIdChange={setSessionId}
          />
        </main>

        {/* ============================================================ */}
        {/* 右侧面板 - 研究 */}
        {/* ============================================================ */}

        {/* 移动端遮罩 */}
        {rightPanelOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setRightPanelOpen(false)}
          />
        )}

        {/* 右侧面板 */}
        <aside
          className={`
            fixed lg:relative inset-y-0 right-0 z-40
            w-80 bg-gray-50 border-l border-gray-200
            transform transition-transform duration-300 ease-in-out
            lg:transform-none lg:flex-shrink-0
            ${rightPanelOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          `}
        >
          {/* 移动端关闭按钮 */}
          <button
            onClick={() => setRightPanelOpen(false)}
            className="lg:hidden absolute top-3 left-3 p-2 rounded-lg hover:bg-gray-200 z-50"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>

          <div className="h-full overflow-y-auto pt-12 lg:pt-0">
            <ResearchPanel
              projectId={projectId}
              outputs={outputs}
              onOutputsChange={handleOutputsChange}
            />
          </div>
        </aside>
      </div>
    </div>
  )
}
