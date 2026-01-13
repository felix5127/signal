/**
 * [INPUT]: Next.js middleware API, 环境变量 ADMIN_PASSWORD
 * [OUTPUT]: 对外提供 /admin/* 路由保护
 * [POS]: 前端根目录中间件，保护管理后台路由
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// ========== Admin 路由保护 ==========

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 只保护 /admin/* 路由（排除登录页）
  if (pathname.startsWith('/admin') && !pathname.startsWith('/admin/login')) {
    const authCookie = request.cookies.get('admin_auth')

    // 未认证则重定向到登录页
    if (authCookie?.value !== 'authenticated') {
      const loginUrl = new URL('/admin/login', request.url)
      // 保存原始路径用于登录后跳转
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

// ========== 匹配配置 ==========

export const config = {
  matcher: ['/admin/:path*'],
}
