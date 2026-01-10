/**
 * [INPUT]: 依赖 React useState/useEffect、react-markdown
 * [OUTPUT]: 对外提供每周观察报告展示组件（Markdown渲染）
 * [POS]: components/ 的每周报告Tab组件
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Clock, TrendingUp, KeyRound, FileText, Inbox } from 'lucide-react'

interface WeeklyDigest {
  week_start: string
  week_end: string
  total_signals: number
  sources_breakdown: { [key: string]: number }
  top_10: Signal[]
  top_breakthroughs: Signal[]
  top_tools: Signal[]
  top_papers: Signal[]
  top_news: Signal[]
  summary: string
  trending_topics: string[]
  hot_keywords: string[]
  created_at: string
}

interface Signal {
  id: number
  title: string
  url: string
  source: string
  category: string
  final_score: number
  created_at: string
}

export function WeeklyReportTab() {
  const [digest, setDigest] = useState<WeeklyDigest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDigest = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const res = await fetch(`${apiUrl}/api/digest/week`)

        if (res.status === 404) {
          setError('上周精选尚未生成，请等待每周一 08:00 自动生成')
          return
        }

        if (!res.ok) {
          throw new Error('Failed to fetch weekly digest')
        }

        const data = await res.json()
        setDigest(data)
      } catch (err: any) {
        setError(err.message || '加载失败')
      } finally {
        setLoading(false)
      }
    }

    fetchDigest()
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px', color: '#9ca3af' }}>
        <div style={{ marginBottom: '16px' }}><Clock className="w-12 h-12 mx-auto animate-pulse" /></div>
        <p style={{ fontSize: '18px', fontWeight: '500' }}>加载中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <div style={{ marginBottom: '16px' }}><Inbox className="w-12 h-12 mx-auto text-gray-400" /></div>
        <p style={{ fontSize: '18px', fontWeight: '500', marginBottom: '8px', color: '#ef4444' }}>
          {error}
        </p>
        <p style={{ color: '#9ca3af' }}>系统将在每周一早上 8:00 自动生成上周精选</p>
      </div>
    )
  }

  if (!digest) {
    return null
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <style>{`
        .report-header {
          text-align: center;
          padding: 40px 20px;
          border-bottom: 2px solid #f0f0f0;
          margin-bottom: 40px;
        }
        .report-title {
          font-size: 28px;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 12px;
        }
        .report-meta {
          color: #6b7280;
          font-size: 14px;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 40px;
        }
        .stat-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 20px;
          border-radius: 12px;
          text-align: center;
        }
        .stat-number {
          font-size: 32px;
          font-weight: 700;
          margin-bottom: 4px;
        }
        .stat-label {
          font-size: 13px;
          opacity: 0.9;
        }
        .section {
          margin-bottom: 48px;
        }
        .section-title {
          font-size: 20px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 20px;
          padding-bottom: 12px;
          border-bottom: 2px solid #f0f0f0;
        }
        .signal-list {
          list-style: none;
        }
        .signal-item {
          padding: 16px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          margin-bottom: 12px;
          transition: all 0.2s;
        }
        .signal-item:hover {
          border-color: #667eea;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }
        .signal-item-title {
          font-size: 15px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 8px;
        }
        .signal-item-title a {
          color: inherit;
          text-decoration: none;
        }
        .signal-item-title a:hover {
          color: #667eea;
        }
        .signal-item-meta {
          display: flex;
          gap: 12px;
          font-size: 13px;
          color: #9ca3af;
        }
        .tag-list {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .tag {
          background: #e0e7ff;
          color: #4338ca;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
        }
        .markdown-content {
          line-height: 1.8;
          color: #374151;
        }
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3 {
          color: #1a1a1a;
          margin-top: 32px;
          margin-bottom: 16px;
          font-weight: 600;
        }
        .markdown-content h1 {
          font-size: 24px;
          padding-bottom: 12px;
          border-bottom: 2px solid #f0f0f0;
        }
        .markdown-content h2 {
          font-size: 20px;
        }
        .markdown-content h3 {
          font-size: 16px;
        }
        .markdown-content p {
          margin-bottom: 16px;
        }
        .markdown-content ul,
        .markdown-content ol {
          margin-bottom: 16px;
          padding-left: 24px;
        }
        .markdown-content li {
          margin-bottom: 8px;
        }
        .markdown-content code {
          background: #f3f4f6;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.9em;
          font-family: 'Monaco', 'Courier New', monospace;
        }
        .markdown-content pre {
          background: #1f2937;
          color: #f3f4f6;
          padding: 16px;
          border-radius: 8px;
          overflow-x: auto;
          margin-bottom: 16px;
        }
        .markdown-content pre code {
          background: none;
          padding: 0;
          color: inherit;
        }
        .markdown-content blockquote {
          border-left: 4px solid #667eea;
          padding-left: 16px;
          color: #6b7280;
          font-style: italic;
          margin-bottom: 16px;
        }
      `}</style>

      <div className="report-header">
        <div className="report-title">
          📊 AI 技术周报 | {new Date(digest.week_start).toLocaleDateString('zh-CN')} - {new Date(digest.week_end).toLocaleDateString('zh-CN')}
        </div>
        <div className="report-meta">
          生成时间: {new Date(digest.created_at).toLocaleString('zh-CN')}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{digest.total_signals}</div>
          <div className="stat-label">本周信号总数</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{digest.top_10.length}</div>
          <div className="stat-label">Top 10 精选</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{Object.keys(digest.sources_breakdown).length}</div>
          <div className="stat-label">数据源数量</div>
        </div>
      </div>

      <div className="section">
        <div className="section-title">🏆 本周 Top 10</div>
        <ul className="signal-list">
          {digest.top_10.map((signal, index) => (
            <li key={signal.id} className="signal-item">
              <div className="signal-item-title">
                <span style={{ color: '#667eea', fontWeight: '700', marginRight: '8px' }}>
                  #{index + 1}
                </span>
                <a href={signal.url} target="_blank" rel="noopener noreferrer">
                  {signal.title}
                </a>
              </div>
              <div className="signal-item-meta">
                <span style={{ color: '#fbbf24' }}>
                  {'★'.repeat(signal.final_score)}{'☆'.repeat(5 - signal.final_score)}
                </span>
                <span>📂 {signal.category}</span>
                <span style={{ textTransform: 'uppercase' }}>{signal.source}</span>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {digest.top_breakthroughs.length > 0 && (
        <div className="section">
          <div className="section-title">🚀 技术突破 Top 3</div>
          <ul className="signal-list">
            {digest.top_breakthroughs.map((signal) => (
              <li key={signal.id} className="signal-item">
                <div className="signal-item-title">
                  <a href={signal.url} target="_blank" rel="noopener noreferrer">
                    {signal.title}
                  </a>
                </div>
                <div className="signal-item-meta">
                  <span style={{ color: '#fbbf24' }}>
                    {'★'.repeat(signal.final_score)}
                  </span>
                  <span style={{ textTransform: 'uppercase' }}>{signal.source}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {digest.top_tools.length > 0 && (
        <div className="section">
          <div className="section-title">🔧 开源工具 Top 3</div>
          <ul className="signal-list">
            {digest.top_tools.map((signal) => (
              <li key={signal.id} className="signal-item">
                <div className="signal-item-title">
                  <a href={signal.url} target="_blank" rel="noopener noreferrer">
                    {signal.title}
                  </a>
                </div>
                <div className="signal-item-meta">
                  <span style={{ color: '#fbbf24' }}>
                    {'★'.repeat(signal.final_score)}
                  </span>
                  <span style={{ textTransform: 'uppercase' }}>{signal.source}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {digest.trending_topics.length > 0 && (
        <div className="section">
          <div className="section-title flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            热门话题
          </div>
          <div className="tag-list">
            {digest.trending_topics.map((topic, index) => (
              <span key={index} className="tag">{topic}</span>
            ))}
          </div>
        </div>
      )}

      {digest.hot_keywords.length > 0 && (
        <div className="section">
          <div className="section-title flex items-center gap-2">
            <KeyRound className="w-5 h-5" />
            高频关键词
          </div>
          <div className="tag-list">
            {digest.hot_keywords.map((keyword, index) => (
              <span key={index} className="tag">{keyword}</span>
            ))}
          </div>
        </div>
      )}

      {digest.summary && (
        <div className="section">
          <div className="section-title flex items-center gap-2">
            <FileText className="w-5 h-5" />
            本周概览
          </div>
          <div className="markdown-content">
            <ReactMarkdown>{digest.summary}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
