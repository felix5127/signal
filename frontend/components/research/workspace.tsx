/**
 * [INPUT]: 依赖 /api/research/* 获取项目数据，panels 子组件
 * [OUTPUT]: 对外提供研究工作台主组件（NotebookLM 风格三栏布局）
 * [POS]: components/research 的核心工作台组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Loader2,
  AlertCircle,
  Menu,
  X,
} from 'lucide-react'
import Navbar from '@/components/navbar'
import { SourcesPanel, ChatPanel, StudioPanel, type Source } from './panels'

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
// Mercury 风格颜色
// ============================================================

const COLORS = {
  background: '#FBFCFD',
  primary: '#1E3A5F',
  border: 'rgba(0, 0, 0, 0.06)',
}

// ============================================================
// 工作台组件 - NotebookLM 风格三栏布局
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

  // 选中的来源
  const [selectedSources, setSelectedSources] = useState<string[]>([])

  // 对话状态
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)

  // 面板折叠状态
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

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
        // 默认全选所有来源
        setSelectedSources(data.map((s: Source) => s.id))
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
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: COLORS.background }}>
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4" style={{ color: COLORS.primary }} />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: COLORS.background }}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2" style={{ color: COLORS.primary }}>项目不存在</h2>
          <Link href="/research" className="text-[#8B5CF6] hover:underline">
            返回项目列表
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: COLORS.background }}>
      {/* ================================================================ */}
      {/* 全局 Navbar - 设计稿要求 */}
      {/* ================================================================ */}
      <Navbar />

      {/* ================================================================ */}
      {/* 三栏主体 */}
      {/* ================================================================ */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* ============================================================ */}
        {/* 左侧面板 - 来源 (300px) */}
        {/* ============================================================ */}

        {/* 移动端遮罩 */}
        <AnimatePresence>
          {leftPanelOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
              onClick={() => setLeftPanelOpen(false)}
            />
          )}
        </AnimatePresence>

        {/* 左侧面板 */}
        <aside
          className={`
            fixed lg:relative inset-y-0 left-0 z-40
            transform transition-transform duration-300 ease-out
            lg:transform-none lg:flex-shrink-0
            ${leftPanelOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          {/* 移动端关闭按钮 */}
          <button
            onClick={() => setLeftPanelOpen(false)}
            className="lg:hidden absolute top-3 right-3 p-2 rounded-lg hover:bg-gray-200 z-50 bg-white shadow-md"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>

          <div className="h-full pt-12 lg:pt-0">
            <SourcesPanel
              projectId={projectId}
              sources={sources}
              onSourcesChange={handleSourcesChange}
              selectedSources={selectedSources}
              onSelectedSourcesChange={setSelectedSources}
              isCollapsed={leftPanelCollapsed}
              onToggleCollapse={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
            />
          </div>
        </aside>

        {/* ============================================================ */}
        {/* 中间面板 - 对话 (flex-1) */}
        {/* ============================================================ */}
        <main className="flex-1 min-w-0 flex flex-col">
          <ChatPanel
            projectId={projectId}
            projectName={project.name}
            sourceCount={sources.length}
            messages={chatMessages}
            onMessagesChange={setChatMessages}
            sessionId={sessionId}
            onSessionIdChange={setSessionId}
          />
        </main>

        {/* ============================================================ */}
        {/* 右侧面板 - Studio (320px) */}
        {/* ============================================================ */}

        {/* 移动端遮罩 */}
        <AnimatePresence>
          {rightPanelOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
              onClick={() => setRightPanelOpen(false)}
            />
          )}
        </AnimatePresence>

        {/* 右侧面板 */}
        <aside
          className={`
            fixed lg:relative inset-y-0 right-0 z-40
            transform transition-transform duration-300 ease-out
            lg:transform-none lg:flex-shrink-0
            ${rightPanelOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          `}
        >
          {/* 移动端关闭按钮 */}
          <button
            onClick={() => setRightPanelOpen(false)}
            className="lg:hidden absolute top-3 left-3 p-2 rounded-lg hover:bg-gray-200 z-50 bg-white shadow-md"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>

          <div className="h-full pt-12 lg:pt-0">
            <StudioPanel
              projectId={projectId}
              outputs={outputs}
              onOutputsChange={handleOutputsChange}
              isCollapsed={rightPanelCollapsed}
              onToggleCollapse={() => setRightPanelCollapsed(!rightPanelCollapsed)}
            />
          </div>
        </aside>
      </div>
    </div>
  )
}
