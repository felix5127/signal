/**
 * [INPUT]: 请求体 { password }，环境变量 ADMIN_PASSWORD
 * [OUTPUT]: 对外提供 POST /api/admin/login
 * [POS]: admin API 的登录验证端点
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

// ========== POST: 验证密码并设置 Cookie ==========

export async function POST(request: NextRequest) {
  try {
    const { password } = await request.json()

    // 从环境变量获取密码
    const adminPassword = process.env.ADMIN_PASSWORD
    if (!adminPassword) {
      return NextResponse.json(
        { success: false, message: '服务器未配置管理员密码' },
        { status: 500 }
      )
    }

    if (password === adminPassword) {
      // 设置认证 Cookie（7天有效期）
      // sameSite: 'strict' 提供 CSRF 防护，仅同站请求携带 Cookie
      const cookieStore = await cookies()
      cookieStore.set('admin_auth', 'authenticated', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict', // 严格模式防止 CSRF 攻击
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
      })

      return NextResponse.json({ success: true })
    } else {
      return NextResponse.json(
        { success: false, message: '密码错误' },
        { status: 401 }
      )
    }
  } catch (error) {
    return NextResponse.json(
      { success: false, message: '登录失败' },
      { status: 500 }
    )
  }
}
