// Input: Backend API (/api/feeds/info)
// Output: RSS 订阅列表页面
// Position: 展示可用的 RSS Feed 订阅链接
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState, useEffect } from 'react'

interface Feed {
  name: string
  url: string
  description: string
}

interface FeedsInfo {
  feeds: Feed[]
  parameters: Record<string, {
    description: string
    values?: string[]
    default?: string | number
    example?: number
  }>
}

export default function FeedsPage() {
  const [feedsInfo, setFeedsInfo] = useState<FeedsInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null)

  useEffect(() => {
    const fetchFeedsInfo = async () => {
      try {
        const response = await fetch(`/api/feeds/info`)
        if (!response.ok) {
          throw new Error(`API 请求失败: ${response.status}`)
        }
        const data = await response.json()
        setFeedsInfo(data)
      } catch (err) {
        console.error('获取 Feed 信息失败:', err)
        setError(err instanceof Error ? err.message : '获取数据失败')
      } finally {
        setLoading(false)
      }
    }

    fetchFeedsInfo()
  }, [])

  const handleCopy = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url)
      setCopiedUrl(url)
      setTimeout(() => setCopiedUrl(null), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--ds-surface)]">
      {/* 头部 */}
      <header className="bg-[var(--ds-bg)] border-b border-[var(--ds-border)]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-[var(--ds-fg)]">
                    Signal Hunter
                  </h1>
                  <p className="text-xs text-[var(--ds-muted)]">
                    RSS 订阅
                  </p>
                </div>
              </a>
            </div>

            <button
              onClick={() => {
                document.documentElement.classList.toggle('dark')
              }}
              className="p-2 rounded-2xl hover:bg-[var(--ds-surface-2)] transition-colors"
              aria-label="切换主题"
            >
              <svg
                className="w-5 h-5 text-[var(--ds-muted)]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* 主内容 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-orange-100 dark:bg-orange-900/30 mb-4">
            <svg
              className="w-8 h-8 text-orange-500"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795.001 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.71-7.118-15.758-15.839-15.82zm0-3.368c10.58.046 19.152 8.594 19.183 19.188h4.817c-.03-13.231-10.755-23.954-24-24v4.812z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-[var(--ds-fg)] mb-3">
            RSS 订阅
          </h2>
          <p className="text-[var(--ds-muted)] max-w-2xl mx-auto">
            使用你喜欢的 RSS 阅读器订阅 Signal Hunter 的内容更新。
            支持按类型、分类、评分等多种方式订阅。
          </p>
        </div>

        {/* 加载状态 */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-indigo-200 dark:border-indigo-800 border-t-indigo-500 rounded-full animate-spin" />
            <p className="mt-4 text-[var(--ds-muted)]">加载中...</p>
          </div>
        )}

        {/* 错误状态 */}
        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-2">
              加载失败
            </h3>
            <p className="text-[var(--ds-muted)]">{error}</p>
          </div>
        )}

        {/* Feed 列表 */}
        {!loading && !error && feedsInfo && (
          <>
            {/* 推荐订阅 */}
            <section className="mb-12">
              <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                推荐订阅
              </h3>
              <div className="grid gap-4">
                {feedsInfo.feeds.slice(0, 3).map((feed) => (
                  <FeedCard
                    key={feed.url}
                    feed={feed}
                    onCopy={handleCopy}
                    isCopied={copiedUrl === feed.url}
                    highlight
                  />
                ))}
              </div>
            </section>

            {/* 按类型订阅 */}
            <section className="mb-12">
              <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                按类型订阅
              </h3>
              <div className="grid gap-4 sm:grid-cols-2">
                {feedsInfo.feeds.slice(3, 7).map((feed) => (
                  <FeedCard
                    key={feed.url}
                    feed={feed}
                    onCopy={handleCopy}
                    isCopied={copiedUrl === feed.url}
                  />
                ))}
              </div>
            </section>

            {/* 按分类订阅 */}
            <section className="mb-12">
              <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                按分类订阅
              </h3>
              <div className="grid gap-4 sm:grid-cols-2">
                {feedsInfo.feeds.slice(7, 11).map((feed) => (
                  <FeedCard
                    key={feed.url}
                    feed={feed}
                    onCopy={handleCopy}
                    isCopied={copiedUrl === feed.url}
                  />
                ))}
              </div>
            </section>

            {/* 组合订阅 */}
            <section className="mb-12">
              <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                组合订阅
              </h3>
              <div className="grid gap-4">
                {feedsInfo.feeds.slice(11).map((feed) => (
                  <FeedCard
                    key={feed.url}
                    feed={feed}
                    onCopy={handleCopy}
                    isCopied={copiedUrl === feed.url}
                  />
                ))}
              </div>
            </section>

            {/* 自定义订阅说明 */}
            <section className="bg-[var(--ds-surface-2)] rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-[var(--ds-fg)] mb-4">
                自定义订阅
              </h3>
              <p className="text-[var(--ds-muted)] mb-4">
                你可以通过组合以下参数来创建自定义的 RSS 订阅：
              </p>
              <div className="space-y-3">
                {Object.entries(feedsInfo.parameters).map(([key, param]) => (
                  <div
                    key={key}
                    className="bg-[var(--ds-bg)] rounded-xl p-4 border border-[var(--ds-border)]"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <code className="text-sm font-mono text-indigo-600 dark:text-indigo-400">
                          {key}
                        </code>
                        <p className="text-sm text-[var(--ds-muted)] mt-1">
                          {param.description}
                        </p>
                      </div>
                      <div className="text-right text-sm">
                        {param.values && (
                          <span className="text-[var(--ds-subtle)]">
                            {param.values.join(' | ')}
                          </span>
                        )}
                        {param.default !== undefined && (
                          <span className="block text-[var(--ds-subtle)] mt-1">
                            默认: {param.default}
                          </span>
                        )}
                        {param.example !== undefined && (
                          <span className="block text-[var(--ds-subtle)] mt-1">
                            示例: {param.example}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-sm text-[var(--ds-subtle)] mt-4">
                示例: <code className="bg-[var(--ds-surface-2)] px-2 py-1 rounded text-xs">
                  /api/feeds/rss?type=article&domain=人工智能&minScore=80
                </code>
              </p>
            </section>
          </>
        )}
      </main>

      {/* 页脚 */}
      <footer className="border-t border-[var(--ds-border)] bg-[var(--ds-bg)] mt-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[var(--ds-muted)]">
              Signal Hunter - 面向超级个体的技术情报分析系统
            </p>
            <div className="flex items-center gap-4 text-sm text-[var(--ds-muted)]">
              <a href="/" className="hover:text-[var(--ds-fg)] transition-colors">
                首页
              </a>
              <span>|</span>
              <a href="/newsletters" className="hover:text-[var(--ds-fg)] transition-colors">
                周刊
              </a>
              <span>|</span>
              <a href="/stats" className="hover:text-[var(--ds-fg)] transition-colors">
                统计
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Feed 卡片组件
function FeedCard({
  feed,
  onCopy,
  isCopied,
  highlight = false,
}: {
  feed: Feed
  onCopy: (url: string) => void
  isCopied: boolean
  highlight?: boolean
}) {
  return (
    <div
      className={`
        bg-[var(--ds-bg)] rounded-2xl p-4 border transition-all
        ${highlight
          ? 'border-indigo-200 dark:border-indigo-800 shadow-sm'
          : 'border-[var(--ds-border)]'
        }
        hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700
      `}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-[var(--ds-fg)]">
            {feed.name}
          </h4>
          <p className="text-sm text-[var(--ds-muted)] mt-1">
            {feed.description}
          </p>
          <p className="text-xs text-[var(--ds-subtle)] mt-2 truncate font-mono">
            {feed.url}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={feed.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-2xl bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors"
            title="在新标签页打开"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795.001 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.71-7.118-15.758-15.839-15.82zm0-3.368c10.58.046 19.152 8.594 19.183 19.188h4.817c-.03-13.231-10.755-23.954-24-24v4.812z" />
            </svg>
          </a>
          <button
            onClick={() => onCopy(feed.url)}
            className={`
              p-2 rounded-2xl transition-colors
              ${isCopied
                ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                : 'bg-[var(--ds-surface-2)] text-[var(--ds-muted)] hover:bg-[var(--ds-bg)]'
              }
            `}
            title={isCopied ? '已复制' : '复制链接'}
          >
            {isCopied ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
