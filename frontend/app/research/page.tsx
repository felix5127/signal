/**
 * [INPUT]: 依赖 useEffect/useState 轮询 /api/tasks 接口
 * [OUTPUT]: 对外提供深度研究任务列表页面，展示任务进度和状态
 * [POS]: app/research/ 的根路由页面，展示所有深度研究任务
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, CheckCircle2, XCircle, Clock, Loader2, Trash2, Eye, Pause, Play, Search } from 'lucide-react'
import Link from 'next/link'
import { fadeInUp, staggerContainer } from '@/lib/motion'

interface LogEntry {
  step: string
  time: string
}

interface Task {
  id: number
  task_id: string
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_items: number
  processed_items: number
  failed_items: number
  result: {
    content?: string
    sources?: string[]
    tokens_used?: number
    cost_usd?: number
  } | null
  error: string | null
  logs: LogEntry[] | null
  started_at: string | null
  completed_at: string | null
  created_at: string | null
  meta: {
    resource_id: number
    resource_title: string
    resource_type?: string
    strategy?: string
  } | null
}

// API URL helper
const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ResearchPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null)
  const apiUrl = getApiUrl()

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/tasks?task_type=deep_research&limit=20`)
      if (res.ok) {
        const data = await res.json()
        setTasks(data.tasks || [])
      }
    } catch (e) {
      console.error('Failed to fetch tasks:', e)
    } finally {
      setLoading(false)
    }
  }

  // 删除任务
  const handleDeleteTask = async (taskId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('确定要删除这个任务吗？')) {
      return
    }

    try {
      const res = await fetch(`${apiUrl}/api/tasks/${taskId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        setTasks(prev => prev.filter(task => task.task_id !== taskId))
      } else {
        console.error('Failed to delete task')
      }
    } catch (e) {
      console.error('Failed to delete task:', e)
    }
  }

  // 暂停/恢复任务
  const handleTogglePause = async (taskId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    try {
      const res = await fetch(`${apiUrl}/api/tasks/${taskId}/toggle-pause`, {
        method: 'POST',
      })

      if (res.ok) {
        // 刷新任务列表
        fetchTasks()
      }
    } catch (e) {
      console.error('Failed to toggle task:', e)
    }
  }

  // 查看任务详情
  const handleToggleDetails = (taskId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId)
  }

  useEffect(() => {
    fetchTasks()
    // 5秒轮询刷新
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            深度研究
          </h1>
          <p className="text-lg text-gray-600">
            查看您发起的深度研究报告任务，实时跟踪研究进度
          </p>
        </div>
      </section>

      {/* 任务列表 */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : tasks.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 bg-white rounded-2xl border border-gray-200"
          >
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              暂无研究任务
            </h3>
            <p className="text-gray-500 mb-6">
              去资源详情页启动深度研究，AI 将为您生成深度分析报告
            </p>
            <Link
              href="/articles"
              className="inline-flex items-center text-purple-600 font-medium hover:text-purple-700"
            >
              浏览文章
              <ArrowRight className="ml-2 w-4 h-4" />
            </Link>
          </motion.div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-4"
          >
            {tasks.map((task) => (
              <motion.div
                key={task.task_id}
                variants={fadeInUp}
                className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                onClick={(e) => handleToggleDetails(task.task_id, e)}
              >
                {/* 任务头部 */}
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900 mb-1">
                      {task.meta?.resource_title || '未知资源'}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {new Date(task.created_at || '').toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={task.status} />
                    {/* 操作按钮 */}
                    <div className="flex gap-1">
                      {/* 暂停/恢复按钮 */}
                      {task.status === 'running' && (
                        <button
                          onClick={(e) => handleTogglePause(task.task_id, e)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                          title="暂停任务"
                        >
                          <Pause className="w-4 h-4 text-gray-600" />
                        </button>
                      )}
                      {task.status === 'pending' && (
                        <button
                          onClick={(e) => handleTogglePause(task.task_id, e)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                          title="开始任务"
                        >
                          <Play className="w-4 h-4 text-gray-600" />
                        </button>
                      )}
                      {/* 删除按钮 */}
                      <button
                        onClick={(e) => handleDeleteTask(task.task_id, e)}
                        className="p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                        title="删除任务"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* 当前步骤（运行中） */}
                {task.status === 'running' && task.logs && task.logs.length > 0 && (
                  <div className="flex items-center gap-2 text-sm text-blue-600 mb-4">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    <span>{task.logs[task.logs.length - 1].step}</span>
                  </div>
                )}

                {/* 进度条 */}
                {task.status === 'running' && (
                  <div className="w-full bg-gray-200 h-2 rounded-full mb-4 overflow-hidden">
                    <motion.div
                      className="bg-blue-600 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${task.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}

                {/* 错误信息 */}
                {task.status === 'failed' && task.error && (
                  <div className="text-red-500 text-sm bg-red-50 rounded-lg p-3 mb-4">
                    {task.error}
                  </div>
                )}

                {/* 完成后统计 */}
                {task.status === 'completed' && task.result && (
                  <div className="flex items-center gap-6 text-sm text-gray-600 mb-4">
                    {task.result.tokens_used && (
                      <span>Tokens: {task.result.tokens_used.toLocaleString()}</span>
                    )}
                    {task.result.cost_usd && (
                      <span>成本: ${task.result.cost_usd.toFixed(4)}</span>
                    )}
                  </div>
                )}

                {/* 任务详情（展开时显示） */}
                {expandedTaskId === task.task_id && (
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    {/* 任务元数据 */}
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="font-medium text-gray-700">任务ID：</span>
                        <span className="text-gray-600">{task.task_id}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">资源ID：</span>
                        <span className="text-gray-600">{task.meta?.resource_id}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">策略：</span>
                        <span className="text-gray-600">{task.meta?.strategy || 'default'}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">类型：</span>
                        <span className="text-gray-600">{task.meta?.resource_type || 'unknown'}</span>
                      </div>
                    </div>

                    {/* 任务日志 */}
                    {task.logs && task.logs.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">执行日志：</h4>
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                          {task.logs.map((log, index) => (
                            <div key={index} className="text-xs text-gray-600 font-mono">
                              <span className="text-gray-400">{log.time}</span> {log.step}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 完成结果 */}
                    {task.status === 'completed' && task.result?.content && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">报告预览：</h4>
                        <div className="text-sm text-gray-600 max-h-32 overflow-y-auto line-clamp-4">
                          {task.result.content.substring(0, 300)}...
                        </div>
                      </div>
                    )}

                    {/* 操作按钮 */}
                    <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                      {task.status === 'completed' && task.meta?.resource_id && (
                        <Link
                          href={`/resources/${task.meta.resource_id}`}
                          className="inline-flex items-center text-sm font-medium text-purple-600 hover:text-purple-700"
                        >
                          查看完整报告
                          <ArrowRight className="ml-1 w-4 h-4" />
                        </Link>
                      )}
                      {task.status === 'failed' && task.meta?.resource_id && (
                        <Link
                          href={`/resources/${task.meta.resource_id}`}
                          className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-700"
                        >
                          返回资源页
                          <ArrowRight className="ml-1 w-4 h-4" />
                        </Link>
                      )}
                    </div>
                  </div>
                )}

                {/* 展开指示器 */}
                <div className="flex justify-center mt-4">
                  <Eye className={`w-4 h-4 text-gray-400 transition-transform ${expandedTaskId === task.task_id ? 'rotate-90' : ''}`} />
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    pending: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    cancelled: "bg-gray-100 text-gray-500",
  }

  const labels = {
    pending: "等待中",
    running: "研究中",
    completed: "已完成",
    failed: "失败",
    cancelled: "已取消",
  }

  const icons = {
    pending: <Clock className="w-3 h-3" />,
    running: <Loader2 className="w-3 h-3 animate-spin" />,
    completed: <CheckCircle2 className="w-3 h-3" />,
    failed: <XCircle className="w-3 h-3" />,
    cancelled: <XCircle className="w-3 h-3" />,
  }

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles]}`}>
      {icons[status as keyof typeof icons]}
      {labels[status as keyof typeof labels]}
    </span>
  )
}
