/**
 * [INPUT]: 后端 API (INTERNAL_API_URL/api/resources)
 * [OUTPUT]: 代理到后端 resources API 的 Next.js Route Handler
 * [POS]: app/api/resources/ 的根路由，解决 CORS 问题
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.INTERNAL_API_URL || 'http://localhost:8000'

// 禁用 Next.js 路由缓存
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(request: NextRequest) {
  const url = new URL(request.url)
  const queryString = url.search

  const backendUrl = `${BACKEND_URL}/api/resources${queryString}`

  try {
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
      // 禁用 fetch 缓存，确保每次都从后端获取最新数据
      cache: 'no-store',
    })

    if (!response.ok) {
      console.error('[API Proxy] Backend error:', response.status, response.statusText)
      const errorText = await response.text()
      console.error('[API Proxy] Error body:', errorText)
      return NextResponse.json(
        { success: false, error: `Backend error: ${response.status}`, details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] Fetch error:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to proxy request', details: String(error) },
      { status: 500 }
    )
  }
}
