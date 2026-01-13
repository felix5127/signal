/**
 * [INPUT]: 无
 * [OUTPUT]: 对外提供 POST /api/admin/logout
 * [POS]: admin API 的登出端点
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

// ========== POST: 清除认证 Cookie ==========

export async function POST() {
  try {
    const cookieStore = await cookies()
    cookieStore.delete('admin_auth')

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { success: false, message: '登出失败' },
      { status: 500 }
    )
  }
}
