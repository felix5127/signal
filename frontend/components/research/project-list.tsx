/**
 * [INPUT]: 依赖 /api/research/projects 获取项目列表
 * [OUTPUT]: 对外提供研究项目列表组件
 * [POS]: components/research 的核心列表组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  Plus,
  FolderOpen,
  FileText,
  Trash2,
  Loader2,
  Calendar,
  ArrowRight
} from 'lucide-react'
import { fadeInUp, staggerContainer } from '@/lib/motion'

// ============================================================
// 类型定义
// ============================================================

interface Project {
  id: string
  name: string
  description: string | null
  status: 'active' | 'archived'
  source_count: number
  output_count: number
  created_at: string
  updated_at: string
}

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 主组件
// ============================================================

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const apiUrl = getApiUrl()

  // 获取项目列表
  const fetchProjects = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/research/projects`)
      if (res.ok) {
        const data = await res.json()
        setProjects(data)
      }
    } catch (e) {
      console.error('Failed to fetch projects:', e)
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  // 创建项目
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return

    setCreating(true)
    try {
      const res = await fetch(`${apiUrl}/api/research/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProjectName.trim() }),
      })

      if (res.ok) {
        const project = await res.json()
        setProjects(prev => [project, ...prev])
        setNewProjectName('')
        setShowCreateForm(false)
      }
    } catch (e) {
      console.error('Failed to create project:', e)
    } finally {
      setCreating(false)
    }
  }

  // 删除项目
  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('确定要删除这个项目吗？所有相关的源材料和研究结果都将被删除。')) {
      return
    }

    try {
      const res = await fetch(`${apiUrl}/api/research/projects/${projectId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        setProjects(prev => prev.filter(p => p.id !== projectId))
      }
    } catch (e) {
      console.error('Failed to delete project:', e)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                研究助手
              </h1>
              <p className="text-lg text-gray-600">
                创建研究项目，上传材料，让 AI 帮你深度分析和总结
              </p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              新建项目
            </button>
          </div>
        </div>
      </section>

      {/* 创建项目表单 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl"
          >
            <h2 className="text-xl font-semibold mb-4">新建研究项目</h2>
            <form onSubmit={handleCreateProject}>
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="输入项目名称..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                autoFocus
              />
              <div className="flex gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={creating || !newProjectName.trim()}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                  {creating ? (
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  ) : (
                    '创建'
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* 项目列表 */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : projects.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 bg-white rounded-2xl border border-gray-200"
          >
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FolderOpen className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              还没有研究项目
            </h3>
            <p className="text-gray-500 mb-6">
              创建你的第一个研究项目，开始深度探索
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              新建项目
            </button>
          </motion.div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid gap-4"
          >
            {projects.map((project) => (
              <motion.div key={project.id} variants={fadeInUp}>
                <Link href={`/research/workspace/${project.id}`}>
                  <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer group">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
                          {project.name}
                        </h3>
                        {project.description && (
                          <p className="text-gray-600 mt-1 line-clamp-2">
                            {project.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            {project.source_count} 个源材料
                          </span>
                          <span className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            {project.output_count} 份输出
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(project.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => handleDeleteProject(project.id, e)}
                          className="p-2 rounded-lg hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
                          title="删除项目"
                        >
                          <Trash2 className="w-5 h-5 text-red-500" />
                        </button>
                        <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-purple-600 transition-colors" />
                      </div>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>
    </div>
  )
}
