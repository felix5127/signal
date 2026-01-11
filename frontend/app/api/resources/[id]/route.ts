/**
 * [INPUT]: 后端 API (INTERNAL_API_URL/api/resources/{id})
 * [OUTPUT]: 代理到后端 resource 详情 API 的 Next.js Route Handler
 * [POS]: app/api/resources/[id]/ 的路由，解决 CORS 问题
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.INTERNAL_API_URL || 'http://localhost:8000'

// 禁用 Next.js 路由缓存
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const backendUrl = `${BACKEND_URL}/api/resources/${id}`

  try {
    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: `Backend error: ${response.status}`, details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to proxy request', details: String(error) },
      { status: 500 }
    )
  }
}
