/**
 * [INPUT]: 后端 API (http://backend:8000/api/feeds/*)
 * [OUTPUT]: 代理到后端 feeds API 的 Next.js Route Handler
 * [POS]: app/api/feeds/[...path]/ 的路由，解决 CORS 问题
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextRequest } from 'next/server'

const BACKEND_URL = process.env.INTERNAL_API_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params
  const url = new URL(request.url)
  const queryString = url.search

  const backendUrl = `${BACKEND_URL}/api/feeds/${path.join('/')}${queryString}`

  try {
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()
    return Response.json(data, { status: response.status })
  } catch (error) {
    return Response.json(
      { success: false, error: 'Failed to proxy request' },
      { status: 500 }
    )
  }
}
