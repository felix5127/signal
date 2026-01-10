/**
 * [INPUT]: 依赖 React useState/useEffect/useRef
 * [OUTPUT]: 对外提供每日新闻时间流组件（按日期+数据源分组，无限滚动）
 * [POS]: components/ 的每日新闻Tab组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { Clock, CheckCircle2, Lightbulb } from 'lucide-react'

interface Signal {
  id: number
  source: string
  title: string
  url: string
  one_liner: string
  summary: string
  final_score: number
  category: string
  tags: string[]
  created_at: string
  source_metadata: any
}

// 数据源配置
const SOURCES = [
  { id: 'all', name: '全部', color: '#667eea' },  // 新增全部选项
  { id: 'hn', name: 'Hacker News', color: '#ff6600' },
  { id: 'github', name: 'GitHub', color: '#24292e' },
  { id: 'huggingface', name: 'Hugging Face', color: '#ff9d00' },
  { id: 'twitter', name: 'Twitter', color: '#1da1f2' },
  { id: 'arxiv', name: 'ArXiv', color: '#b31b1b' },
  { id: 'producthunt', name: 'Product Hunt', color: '#da552f' },
  { id: 'blog', name: 'Blog/Podcast', color: '#8b5cf6' },
]

// 实际的数据源（不包括"全部"）
const DATA_SOURCES = SOURCES.filter(s => s.id !== 'all')

export function DailyNewsTab() {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [offset, setOffset] = useState(0)
  const [selectedSources, setSelectedSources] = useState<string[]>(
    ['all'] // 默认选中"全部"
  )
  const observerTarget = useRef(null)

  const LIMIT = 20

  // 切换数据源选择
  const toggleSource = (sourceId: string, event?: React.MouseEvent) => {
    const isMultiSelect = event?.ctrlKey || event?.metaKey // Ctrl(Windows) 或 Cmd(Mac)

    if (sourceId === 'all') {
      // 点击"全部"，选中所有
      setSelectedSources(['all'])
    } else if (isMultiSelect) {
      // 多选模式（按住 Ctrl/Cmd）
      setSelectedSources(prev => {
        // 移除"全部"
        const withoutAll = prev.filter(s => s !== 'all')

        if (withoutAll.includes(sourceId)) {
          // 取消选择
          const newSources = withoutAll.filter(s => s !== sourceId)
          // 如果没有选中任何数据源，回到"全部"
          return newSources.length === 0 ? ['all'] : newSources
        } else {
          // 添加选择
          const newSources = [...withoutAll, sourceId]
          // 如果选中了所有数据源，切换到"全部"
          return newSources.length === DATA_SOURCES.length ? ['all'] : newSources
        }
      })
    } else {
      // 单选模式（正常点击）
      setSelectedSources([sourceId])
    }
  }

  // 按日期分组信号
  const groupByDate = (signals: Signal[]) => {
    const groups: { [key: string]: Signal[] } = {}
    signals.forEach(signal => {
      const date = new Date(signal.created_at).toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'short'
      })
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(signal)
    })
    return groups
  }

  // 按数据源分组
  const groupBySource = (signals: Signal[]) => {
    const groups: { [key: string]: Signal[] } = {}
    signals.forEach(signal => {
      if (!groups[signal.source]) {
        groups[signal.source] = []
      }
      groups[signal.source].push(signal)
    })
    return groups
  }

  // 加载更多数据
  const loadMore = async () => {
    if (loading) return

    setLoading(true)

    // 保存当前选中的数据源和offset,用于验证响应是否仍然有效
    const currentSources = selectedSources.join(',')
    const currentOffset = offset

    try {
      // 客户端组件使用环境变量配置的 API 地址
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // 构建数据源筛选参数
      // 如果选中"全部"，不传 sources 参数；否则传实际选中的数据源
      const isAllSelected = selectedSources.includes('all')
      const sourceParam = !isAllSelected && selectedSources.length > 0
        ? `&sources=${selectedSources.join(',')}`
        : ''

      const res = await fetch(
        `${apiUrl}/api/signals?limit=${LIMIT}&offset=${currentOffset}&sort_by=created_at${sourceParam}`
      )
      const data = await res.json()

      // 检查数据源是否在请求期间发生了变化,如果变了就丢弃这个响应
      if (currentSources !== selectedSources.join(',')) {
        console.log('数据源已变化,丢弃过期响应')
        setLoading(false)
        return
      }

      if (data.items.length < LIMIT) {
        setHasMore(false)
      }

      // 如果是新查询(offset=0),直接替换数据;否则追加
      if (currentOffset === 0) {
        setSignals(data.items)
      } else {
        setSignals(prev => [...prev, ...data.items])
      }
      setOffset(currentOffset + LIMIT)
    } catch (error) {
      console.error('Failed to load signals:', error)
    } finally {
      setLoading(false)
    }
  }

  // 初始加载和数据源切换时重新加载
  useEffect(() => {
    // 重置状态
    setSignals([])
    setOffset(0)
    setHasMore(true)

    // 延迟加载以确保状态已更新
    const timer = setTimeout(() => {
      loadMore()
    }, 100)

    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSources]) // 当数据源改变时重新加载

  // 无限滚动观察器
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore()
        }
      },
      { threshold: 1.0 }
    )

    if (observerTarget.current) {
      observer.observe(observerTarget.current)
    }

    return () => {
      if (observerTarget.current) {
        observer.unobserve(observerTarget.current)
      }
      observer.disconnect()
    }
  }, [hasMore, loading])

  const dateGroups = groupByDate(signals)

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <style>{`
        .source-filter {
          position: sticky;
          top: 0;
          background: white;
          padding: 16px 0;
          margin-bottom: 24px;
          z-index: 100;
          border-bottom: 2px solid #f3f4f6;
        }
        .filter-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .filter-title {
          font-size: 14px;
          font-weight: 600;
          color: #6b7280;
        }
        .filter-toggle-all {
          font-size: 13px;
          color: #667eea;
          cursor: pointer;
          text-decoration: underline;
        }
        .filter-toggle-all:hover {
          color: #764ba2;
        }
        .filter-buttons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .filter-button {
          padding: 6px 12px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .filter-button:hover {
          border-color: #667eea;
          transform: translateY(-1px);
        }
        .filter-button.active {
          border-color: transparent;
          color: white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .filter-button.active.all {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .filter-button.active.hn {
          background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
        }
        .filter-button.active.github {
          background: linear-gradient(135deg, #24292e 0%, #40444b 100%);
        }
        .filter-button.active.huggingface {
          background: linear-gradient(135deg, #ff9d00 0%, #ffb347 100%);
        }
        .filter-button.active.twitter {
          background: linear-gradient(135deg, #1da1f2 0%, #4db8ff 100%);
        }
        .filter-button.active.arxiv {
          background: linear-gradient(135deg, #b31b1b 0%, #d32f2f 100%);
        }
        .filter-button.active.producthunt {
          background: linear-gradient(135deg, #da552f 0%, #ff6b4a 100%);
        }
        .filter-button.active.blog {
          background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
        }
        .timeline {
          position: relative;
        }
        .date-section {
          margin-bottom: 48px;
        }
        .date-header {
          display: flex;
          align-items: center;
          margin-bottom: 24px;
          position: sticky;
          top: 0;
          background: white;
          padding: 12px 0;
          z-index: 10;
        }
        .date-line {
          flex: 1;
          height: 2px;
          background: linear-gradient(90deg, #667eea 0%, transparent 100%);
          margin-left: 16px;
        }
        .date-title {
          font-size: 18px;
          font-weight: 600;
          color: #667eea;
          white-space: nowrap;
        }
        .source-group {
          margin-bottom: 32px;
        }
        .source-header {
          display: inline-block;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 16px;
          text-transform: uppercase;
        }
        .source-header.hn {
          background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
        }
        .source-header.github {
          background: linear-gradient(135deg, #24292e 0%, #40444b 100%);
        }
        .source-header.huggingface {
          background: linear-gradient(135deg, #ff9d00 0%, #ffb347 100%);
        }
        .source-header.twitter {
          background: linear-gradient(135deg, #1da1f2 0%, #4db8ff 100%);
        }
        .source-header.arxiv {
          background: linear-gradient(135deg, #b31b1b 0%, #d32f2f 100%);
        }
        .source-header.producthunt {
          background: linear-gradient(135deg, #da552f 0%, #ff6b4a 100%);
        }
        .source-header.blog {
          background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
        }
        .signal-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 16px;
          transition: all 0.2s;
          cursor: pointer;
        }
        .signal-card:hover {
          border-color: #667eea;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
          transform: translateX(4px);
        }
        .signal-title {
          font-size: 16px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 8px;
          line-height: 1.4;
        }
        .signal-title a {
          color: inherit;
          text-decoration: none;
        }
        .signal-title a:hover {
          color: #667eea;
        }
        .signal-oneliner {
          color: #667eea;
          font-weight: 500;
          font-size: 14px;
          margin-bottom: 8px;
        }
        .signal-summary {
          color: #6b7280;
          font-size: 14px;
          line-height: 1.6;
          margin-bottom: 12px;
        }
        .signal-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
          font-size: 13px;
          color: #9ca3af;
        }
        .signal-score {
          color: #fbbf24;
        }
        .loading {
          text-align: center;
          padding: 32px;
          color: #9ca3af;
          font-size: 14px;
        }
        .empty {
          text-align: center;
          padding: 80px 20px;
          color: #9ca3af;
        }
      `}</style>

      {/* 数据源筛选器 */}
      <div className="source-filter">
        <div className="filter-header">
          <div className="filter-title">
            🎯 数据源筛选
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>
            {selectedSources.includes('all')
              ? '显示全部数据源'
              : `已选择 ${selectedSources.length} 个数据源`}
            {!selectedSources.includes('all') && (
              <span style={{ marginLeft: '8px', color: '#667eea' }}>
                (按住 Ctrl/Cmd 多选)
              </span>
            )}
          </div>
        </div>
        <div className="filter-buttons">
          {SOURCES.map(source => (
            <button
              key={source.id}
              className={`filter-button ${selectedSources.includes(source.id) ? `active ${source.id}` : ''}`}
              onClick={(e) => toggleSource(source.id, e)}
            >
              <span>{source.name}</span>
            </button>
          ))}
        </div>
      </div>

      {signals.length === 0 && !loading && (
        <div className="empty">
          <p style={{ fontSize: '48px', marginBottom: '16px' }}>📭</p>
          <p style={{ fontSize: '18px', fontWeight: '500', marginBottom: '8px' }}>
            暂无新闻数据
          </p>
          <p>系统将每小时自动抓取最新技术信号</p>
        </div>
      )}

      <div className="timeline">
        {Object.keys(dateGroups).sort((a, b) => new Date(b).getTime() - new Date(a).getTime()).map(date => {
          const dateSignals = dateGroups[date]
          const sourceGroups = groupBySource(dateSignals)

          return (
            <div key={date} className="date-section">
              <div className="date-header">
                <div className="date-title">📅 {date}</div>
                <div className="date-line"></div>
              </div>

              {Object.keys(sourceGroups).map(source => (
                <div key={source} className="source-group">
                  <div className={`source-header ${source}`}>
                    {source === 'hn' ? 'Hacker News' :
                     source === 'github' ? 'GitHub Trending' :
                     source === 'huggingface' ? 'Hugging Face' :
                     source === 'twitter' ? 'Twitter' :
                     source === 'arxiv' ? 'ArXiv Papers' :
                     source === 'producthunt' ? 'Product Hunt' :
                     source === 'blog' ? 'Blog/Podcast' :
                     source.toUpperCase()}
                    {' '}({sourceGroups[source].length})
                  </div>

                  {sourceGroups[source].map((signal: Signal) => (
                    <div key={signal.id} className="signal-card">
                      <div className="signal-title">
                        <a href={signal.url} target="_blank" rel="noopener noreferrer">
                          {signal.title}
                        </a>
                      </div>
                      <div className="signal-oneliner flex items-center gap-1">
                        <Lightbulb className="w-3 h-3" />
                        {signal.one_liner}
                      </div>
                      <div className="signal-summary">{signal.summary}</div>
                      <div className="signal-meta">
                        <span className="signal-score">
                          {'★'.repeat(signal.final_score)}{'☆'.repeat(5 - signal.final_score)}
                        </span>
                        <span>📂 {signal.category}</span>
                        <span>🕐 {new Date(signal.created_at).toLocaleTimeString('zh-CN', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )
        })}
      </div>

      {loading && (
        <div className="loading">
          <Clock className="w-6 h-6 mx-auto mb-2 animate-pulse" />
          加载中...
        </div>
      )}

      {!hasMore && signals.length > 0 && (
        <div className="loading">
          <CheckCircle2 className="w-6 h-6 mx-auto mb-2 text-green-500" />
          已加载全部内容
        </div>
      )}

      <div ref={observerTarget} style={{ height: '20px' }}></div>
    </div>
  )
}
