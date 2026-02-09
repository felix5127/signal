/**
 * [INPUT]: SSE 端点 URL + 请求体
 * [OUTPUT]: 流式文本内容、工具调用状态、引用列表
 * [POS]: hooks/use-sse.ts — 研究模块 SSE 流式通信 Hook
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useRef, useCallback, useEffect } from 'react'

// ============================================================
// 类型定义
// ============================================================

export interface Reference {
  title: string
  url: string
}

interface SSEState {
  /** 累积的文本内容 */
  content: string
  /** 是否正在流式传输 */
  isStreaming: boolean
  /** 错误信息 */
  error: string | null
  /** 收集到的引用来源 */
  references: Reference[]
  /** 当前正在执行的工具名称 */
  activeTools: string[]
}

const INITIAL_STATE: SSEState = {
  content: '',
  isStreaming: false,
  error: null,
  references: [],
  activeTools: [],
}

// ============================================================
// Hook: useSSE
// ============================================================

/**
 * 通用 SSE 流式通信 Hook
 *
 * 使用 fetch + ReadableStream 而非 EventSource，
 * 因为 SSE 端点需要 POST + JSON body，EventSource 仅支持 GET。
 *
 * 支持的 SSE 事件类型:
 * - text: 增量文本 { delta: string }
 * - tool_start: 工具调用开始 { tool: string }
 * - tool_end: 工具调用结束 { tool: string, references?: Reference[] }
 * - done: 流结束 { references?: Reference[] }
 * - error: 错误 { error: string }
 */
export function useSSE() {
  const [state, setState] = useState<SSEState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)

  // ============================================================
  // 停止当前流
  // ============================================================

  const stop = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  // ============================================================
  // 启动 SSE 流
  // ============================================================

  const start = useCallback(async (url: string, body?: object) => {
    // 中断现有流
    stop()

    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...INITIAL_STATE, isStreaming: true })

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE 事件由双换行 (\n\n) 分隔
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() || ''

        for (const block of blocks) {
          if (!block.trim()) continue

          // 解析 event: 和 data: 行
          // 支持多行 data (SSE 规范) 和 "data:" 无空格格式
          const lines = block.split('\n')
          let eventType = ''
          const dataLines: string[] = []

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              const value = line.startsWith('data: ') ? line.slice(6) : line.slice(5)
              dataLines.push(value)
            }
          }

          const eventData = dataLines.join('\n')
          if (!eventType || !eventData) continue

          try {
            const data = JSON.parse(eventData)

            switch (eventType) {
              case 'text':
                setState(prev => ({
                  ...prev,
                  content: prev.content + (data.delta || ''),
                }))
                break

              case 'tool_start':
                setState(prev => ({
                  ...prev,
                  activeTools: [...prev.activeTools, data.tool],
                }))
                break

              case 'tool_end':
                setState(prev => ({
                  ...prev,
                  activeTools: prev.activeTools.filter(t => t !== data.tool),
                  references: data.references?.length
                    ? [...prev.references, ...data.references]
                    : prev.references,
                }))
                break

              case 'done':
                setState(prev => ({
                  ...prev,
                  isStreaming: false,
                  references: data.references?.length
                    ? [...prev.references, ...data.references]
                    : prev.references,
                }))
                return

              case 'error':
                setState(prev => ({
                  ...prev,
                  isStreaming: false,
                  error: data.error || '未知错误',
                }))
                return
            }
          } catch {
            // 忽略 JSON 解析错误
          }
        }
      }

      // 流结束但未收到 done/error 事件
      setState(prev => ({ ...prev, isStreaming: false }))
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setState(prev => ({ ...prev, isStreaming: false }))
        return
      }

      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: err instanceof Error ? err.message : '连接失败',
      }))
    }
  }, [stop])

  // 组件卸载时清理
  useEffect(() => () => { abortRef.current?.abort() }, [])

  return { ...state, start, stop }
}
