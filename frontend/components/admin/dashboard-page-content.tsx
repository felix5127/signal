/**
 * [INPUT]: 依赖 dashboard/ 目录下的所有组件和 Hook
 * [OUTPUT]: 对外提供管理后台统计仪表板页面
 * [POS]: admin/ 的数据统计总览页面，展示系统健康/Pipeline状态/采集漏斗/数据质量
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 从新的 dashboard 目录导入完整的仪表板组件
import AdminDashboard from './dashboard'

export default function DashboardPageContent() {
  return <AdminDashboard />
}
