/**
 * [INPUT]: 后端 API (INTERNAL_API_URL/api/resources/*)
 * [OUTPUT]: 代理到后端 resources API 的 Next.js Route Handler (catch-all)
 * [POS]: app/api/resources/[...path]/ 的路由，处理如 /api/resources/stats 等子路径
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.INTERNAL_API_URL || 'http://localhost:8000'

// 禁用 Next.js 路由缓存
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  const url = new URL(request.url)
  const queryString = url.search

  const backendUrl = `${BACKEND_URL}/api/resources/${path.join('/')}${queryString}`

  console.log('[API Proxy catch-all] Backend URL:', backendUrl)

  try {
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      console.error('[API Proxy catch-all] Backend error:', response.status)
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: `Backend error: ${response.status}`, details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy catch-all] Fetch error:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to proxy request', details: String(error) },
      { status: 500 }
    )
  }
}
