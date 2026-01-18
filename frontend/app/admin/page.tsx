/**
 * [INPUT]: 无
 * [OUTPUT]: Admin 入口页面，重定向到 Dashboard
 * [POS]: admin/ 的入口路由，自动跳转到仪表板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { redirect } from 'next/navigation'

export default function AdminPage() {
  redirect('/admin/dashboard')
}
