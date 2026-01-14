/**
 * [INPUT]: 依赖 Next.js 错误页面机制
 * [OUTPUT]: Pages Router 错误页面组件（纯 HTML，无 framer-motion）
 * [POS]: pages/ 的错误边界，处理 Pages Router 的 404/500 错误
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { NextPageContext } from 'next'

interface ErrorProps {
  statusCode?: number
}

/**
 * Pages Router 错误页面
 * 注意：不能使用任何需要 Context 的组件（如 framer-motion、usePathname 等）
 */
function Error({ statusCode }: ErrorProps) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(to bottom, #f9fafb, #ffffff)',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>
      <div style={{ textAlign: 'center', padding: '1rem' }}>
        <h1 style={{
          fontSize: '6rem',
          fontWeight: 'bold',
          color: '#e5e7eb',
          margin: 0,
        }}>
          {statusCode || 'Error'}
        </h1>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: '#1f2937',
          marginTop: '1rem',
        }}>
          {statusCode === 404 ? '页面未找到' : '服务器错误'}
        </h2>
        <p style={{
          color: '#6b7280',
          marginTop: '0.5rem',
        }}>
          {statusCode === 404
            ? '抱歉，您访问的页面不存在。'
            : '抱歉，服务器出现了问题。'}
        </p>
        <a
          href="/"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginTop: '1.5rem',
            padding: '0.75rem 1.5rem',
            background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
            color: 'white',
            borderRadius: '1rem',
            textDecoration: 'none',
            fontWeight: '500',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.35)',
          }}
        >
          返回首页
        </a>
      </div>
    </div>
  )
}

Error.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404
  return { statusCode }
}

export default Error
