/**
 * [INPUT]: 环境变量
 * [OUTPUT]: 调试信息（仅用于排查问题）
 * [POS]: 临时调试端点
 * [PROTOCOL]: 问题解决后删除此文件
 */

import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const INTERNAL_API_URL = process.env.INTERNAL_API_URL
  const NODE_ENV = process.env.NODE_ENV

  // 测试后端连接
  let backendStatus = 'unknown'
  let backendData = null
  let backendError = null

  if (INTERNAL_API_URL) {
    try {
      const testUrl = `${INTERNAL_API_URL}/api/resources?pageSize=1`
      const response = await fetch(testUrl, {
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
      })

      backendStatus = `${response.status} ${response.statusText}`

      if (response.ok) {
        backendData = await response.json()
      } else {
        backendError = await response.text()
      }
    } catch (error) {
      backendStatus = 'fetch_error'
      backendError = String(error)
    }
  }

  return NextResponse.json({
    env: {
      INTERNAL_API_URL: INTERNAL_API_URL || '(not set - using localhost:8000)',
      INTERNAL_API_URL_SET: !!INTERNAL_API_URL,
      NODE_ENV,
    },
    backend: {
      status: backendStatus,
      data: backendData,
      error: backendError,
    },
    timestamp: new Date().toISOString(),
  })
}
