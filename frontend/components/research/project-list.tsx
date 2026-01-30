/**
 * [INPUT]: 依赖 /api/research/projects 获取项目列表
 * [OUTPUT]: 对外提供 NotebookLM 风格研究项目列表组件
 * [POS]: components/research 的核心列表组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Plus,
  Loader2,
  MoreHorizontal,
  Trash2,
  Edit2,
  ChevronLeft,
  ChevronRight,
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

// 项目卡片背景色 (NotebookLM 风格浅色系)
const CARD_COLORS = [
  '#E8F4FD', // 浅蓝
  '#FEF3E8', // 浅橙
  '#F0FDF4', // 浅绿
  '#F8F9FA', // 浅灰
  '#FDF2F8', // 浅粉
  '#F5F3FF', // 浅紫
  '#ECFDF5', // 薄荷
  '#FFF7ED', // 奶油
]

// 项目 Emoji 图标
const PROJECT_EMOJIS = [
  '📊', '🔬', '📚', '💡', '🎯', '🚀', '🔍', '📈',
  '🧪', '📝', '🎨', '⚡', '🌟', '🔮', '🎓', '💎',
]

// ============================================================
// API 工具
// ============================================================

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ============================================================
// 子组件
// ============================================================

// 新建项目卡片
function NewProjectCard({ onClick }: { onClick: () => void }) {
  return (
    <motion.button
      onClick={onClick}
      className="group relative w-full h-[200px] rounded-2xl border border-dashed border-[#E8E5E0] hover:border-[#1E3A5F] bg-white hover:bg-[#F6F5F2] transition-all duration-200 flex flex-col items-center justify-center gap-4"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="w-12 h-12 rounded-full bg-[#F6F5F2] group-hover:bg-[#E8F4FD] flex items-center justify-center transition-colors">
        <Plus className="w-6 h-6 text-[#6B7280] group-hover:text-[#1E3A5F] transition-colors" />
      </div>
      <span className="text-sm font-medium text-[#6B7280] group-hover:text-[#1E3A5F] transition-colors">
        新建研究项目
      </span>
    </motion.button>
  )
}

// 分页组件
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  const pages = []
  const maxVisiblePages = 5

  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
  const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  return (
    <div className="flex items-center justify-center gap-2 py-6">
      {/* 上一页按钮 */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-[#6B6B6B] hover:bg-[#F5F3F0] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        <span>上一页</span>
      </button>

      {/* 页码 */}
      <div className="flex items-center gap-1">
        {startPage > 1 && (
          <>
            <button
              onClick={() => onPageChange(1)}
              className="w-9 h-9 rounded-lg text-sm text-[#6B6B6B] hover:bg-[#F5F3F0] transition-colors"
            >
              1
            </button>
            {startPage > 2 && (
              <span className="w-9 h-9 flex items-center justify-center text-[#9A9A9A]">
                ...
              </span>
            )}
          </>
        )}
        {pages.map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`w-9 h-9 rounded-lg text-sm transition-colors ${
              page === currentPage
                ? 'bg-[#1E3A5F] text-white'
                : 'text-[#6B6B6B] hover:bg-[#F5F3F0]'
            }`}
          >
            {page}
          </button>
        ))}
        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && (
              <span className="w-9 h-9 flex items-center justify-center text-[#9A9A9A]">
                ...
              </span>
            )}
            <button
              onClick={() => onPageChange(totalPages)}
              className="w-9 h-9 rounded-lg text-sm text-[#6B6B6B] hover:bg-[#F5F3F0] transition-colors"
            >
              {totalPages}
            </button>
          </>
        )}
      </div>

      {/* 下一页按钮 */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-[#6B6B6B] hover:bg-[#F5F3F0] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <span>下一页</span>
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}

// 项目卡片
function ProjectCard({
  project,
  onDelete,
}: {
  project: Project
  onDelete: (id: string, e: React.MouseEvent) => void
}) {
  const router = useRouter()
  const [showMenu, setShowMenu] = useState(false)

  // 根据项目 ID 生成稳定的颜色和 Emoji
  const colorIndex = project.id.charCodeAt(0) % CARD_COLORS.length
  const emojiIndex = project.id.charCodeAt(1) % PROJECT_EMOJIS.length
  const bgColor = CARD_COLORS[colorIndex]
  const emoji = PROJECT_EMOJIS[emojiIndex]

  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + '日'
  }

  const handleClick = () => {
    router.push(`/research/workspace/${project.id}`)
  }

  return (
    <motion.div
      variants={fadeInUp}
      className="relative group"
    >
      <motion.div
        className="w-full h-[200px] rounded-2xl p-5 flex flex-col justify-between overflow-hidden cursor-pointer"
        style={{ backgroundColor: bgColor }}
        onClick={handleClick}
        whileHover={{ scale: 1.02, y: -4 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      >
        {/* 顶部: Emoji + 菜单 */}
        <div className="flex items-start justify-between">
          <span className="text-[40px] leading-none">{emoji}</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
            className="p-1.5 rounded-lg hover:bg-white/50 transition-colors opacity-0 group-hover:opacity-100"
          >
            <MoreHorizontal className="w-5 h-5 text-[#6B7280]" />
          </button>
        </div>

        {/* 底部: 标题 + 元信息 */}
        <div className="space-y-2">
          <h3 className="text-base font-semibold text-[#1E3A5F] line-clamp-2 leading-snug">
            {project.name}
          </h3>
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <span>{formatDate(project.updated_at)}</span>
            <span className="w-1 h-1 rounded-full bg-[#A1A1A0]" />
            <span>{project.source_count} 个来源</span>
          </div>
        </div>

        {/* 下拉菜单 */}
        <AnimatePresence>
          {showMenu && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="absolute top-14 right-4 w-40 bg-white rounded-xl shadow-lg border border-[rgba(0,0,0,0.06)] overflow-hidden z-10"
              onClick={(e) => e.stopPropagation()}
            >
              <button className="w-full px-4 py-2.5 text-sm text-[#374151] hover:bg-[#F6F5F2] flex items-center gap-2.5 transition-colors">
                <Edit2 className="w-4 h-4" />
                重命名
              </button>
              <button
                onClick={(e) => {
                  setShowMenu(false)
                  onDelete(project.id, e)
                }}
                className="w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2.5 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                删除项目
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}

// ============================================================
// 常量
// ============================================================

const ITEMS_PER_PAGE = 20 // 每页 20 条

// ============================================================
// 主组件
// ============================================================

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const apiUrl = getApiUrl()

  // 分页计算
  const totalPages = Math.ceil(projects.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const paginatedProjects = projects.slice(startIndex, startIndex + ITEMS_PER_PAGE)

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
        setShowCreateModal(false)
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

  // 处理分页
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-[#FBFCFD]">
      {/* 创建项目弹窗 */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-semibold text-[#1E3A5F] mb-4">
                新建研究项目
              </h2>
              <form onSubmit={handleCreateProject}>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="输入项目名称..."
                  className="w-full px-4 py-3 bg-[#F6F5F2] border border-[rgba(0,0,0,0.06)] rounded-xl text-[#272735] placeholder:text-[#A1A1A0] focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]/20 focus:border-[#1E3A5F] transition-all"
                  autoFocus
                />
                <div className="flex gap-3 mt-5">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-4 py-2.5 border border-[rgba(0,0,0,0.1)] rounded-xl text-[#6B7280] hover:bg-[#F6F5F2] transition-colors font-medium"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    disabled={creating || !newProjectName.trim()}
                    className="flex-1 px-4 py-2.5 bg-[#1E3A5F] text-white rounded-xl hover:bg-[#2D5A8F] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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
          </motion.div>
        )}
      </AnimatePresence>

      {/* 主内容区 - 设计稿: padding [48, 80] */}
      <main className="flex-1 py-12 px-4 sm:px-6 lg:px-20">
        {/* 页面标题 */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-medium text-[#272735]">
            最近打开过的研究项目
          </h1>
          <button className="flex items-center gap-1 text-sm text-[#6B6B6B] hover:text-[#1E3A5F] transition-colors">
            <span>查看全部</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* 项目网格 */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#1E3A5F]" />
          </div>
        ) : (
          <>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
            >
              {/* 新建卡片 (仅第一页显示) */}
              {currentPage === 1 && (
                <motion.div variants={fadeInUp}>
                  <NewProjectCard onClick={() => setShowCreateModal(true)} />
                </motion.div>
              )}

              {/* 项目卡片 */}
              {paginatedProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onDelete={handleDeleteProject}
                />
              ))}
            </motion.div>

            {/* 分页控件 */}
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </>
        )}

        {/* 空状态 (仅当没有项目时显示额外提示) */}
        {!loading && projects.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center mt-8"
          >
            <p className="text-[#6B7280]">
              点击上方卡片创建你的第一个研究项目
            </p>
          </motion.div>
        )}
      </main>
    </div>
  )
}
