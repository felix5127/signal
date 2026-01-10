// Input: Markdown文本内容
// Output: 渲染后的React组件（带XSS防护）
// Position: Deep Research报告的Markdown渲染器，支持表格、代码高亮、GFM语法
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md

'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { memo } from 'react'

interface MarkdownRendererProps {
  content: string
}

function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeSanitize]}
      components={{
        // 代码块渲染 - 支持语法高亮
        code({ node, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '')
          const inline = !match
          return !inline && match ? (
            <SyntaxHighlighter
              style={vscDarkPlus}
              language={match[1]}
              PreTag="div"
              customStyle={{
                borderRadius: '8px',
                fontSize: '14px',
                marginTop: '16px',
                marginBottom: '16px',
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code
              className={className}
              style={{
                background: '#f3f4f6',
                padding: '2px 6px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '14px',
                color: '#d73a49',
              }}
              {...props}
            >
              {children}
            </code>
          )
        },

        // 表格样式
        table({ children }) {
          return (
            <div style={{ overflowX: 'auto', marginTop: '20px', marginBottom: '20px' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '14px',
                  border: '1px solid #e5e7eb',
                }}
              >
                {children}
              </table>
            </div>
          )
        },

        th({ children }) {
          return (
            <th
              style={{
                background: '#f9fafb',
                padding: '12px 16px',
                textAlign: 'left',
                borderBottom: '2px solid #d1d5db',
                border: '1px solid #e5e7eb',
                fontWeight: '600',
                color: '#374151',
              }}
            >
              {children}
            </th>
          )
        },

        td({ children }) {
          return (
            <td
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid #e5e7eb',
                border: '1px solid #e5e7eb',
                color: '#6b7280',
              }}
            >
              {children}
            </td>
          )
        },

        // 标题样式
        h1({ children }) {
          return (
            <h1
              style={{
                fontSize: '28px',
                fontWeight: '700',
                margin: '32px 0 20px 0',
                color: '#111827',
                borderBottom: '2px solid #e5e7eb',
                paddingBottom: '12px',
              }}
            >
              {children}
            </h1>
          )
        },

        h2({ children }) {
          return (
            <h2
              style={{
                fontSize: '22px',
                fontWeight: '700',
                margin: '32px 0 16px 0',
                color: '#1f2937',
              }}
            >
              {children}
            </h2>
          )
        },

        h3({ children }) {
          return (
            <h3
              style={{
                fontSize: '18px',
                fontWeight: '600',
                margin: '24px 0 12px 0',
                color: '#374151',
              }}
            >
              {children}
            </h3>
          )
        },

        // 链接样式
        a({ children, href }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: '#667eea',
                textDecoration: 'underline',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#764ba2'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#667eea'
              }}
            >
              {children}
            </a>
          )
        },

        // 列表样式
        ul({ children }) {
          return (
            <ul
              style={{
                marginLeft: '24px',
                marginTop: '12px',
                marginBottom: '12px',
                listStyleType: 'disc',
              }}
            >
              {children}
            </ul>
          )
        },

        ol({ children }) {
          return (
            <ol
              style={{
                marginLeft: '24px',
                marginTop: '12px',
                marginBottom: '12px',
                listStyleType: 'decimal',
              }}
            >
              {children}
            </ol>
          )
        },

        li({ children }) {
          return (
            <li
              style={{
                marginTop: '8px',
                marginBottom: '8px',
                color: '#4b5563',
                lineHeight: '1.7',
              }}
            >
              {children}
            </li>
          )
        },

        // 段落
        p({ children }) {
          return (
            <p
              style={{
                margin: '16px 0',
                lineHeight: '1.8',
                color: '#4b5563',
              }}
            >
              {children}
            </p>
          )
        },

        // 引用块
        blockquote({ children }) {
          return (
            <blockquote
              style={{
                borderLeft: '4px solid #667eea',
                paddingLeft: '20px',
                marginLeft: '0',
                marginTop: '20px',
                marginBottom: '20px',
                color: '#6b7280',
                fontStyle: 'italic',
                background: '#f9fafb',
                padding: '16px 20px',
                borderRadius: '4px',
              }}
            >
              {children}
            </blockquote>
          )
        },

        // 强调
        strong({ children }) {
          return (
            <strong
              style={{
                fontWeight: '700',
                color: '#111827',
              }}
            >
              {children}
            </strong>
          )
        },

        em({ children }) {
          return (
            <em
              style={{
                fontStyle: 'italic',
                color: '#4b5563',
              }}
            >
              {children}
            </em>
          )
        },

        // 分隔线
        hr() {
          return (
            <hr
              style={{
                border: 'none',
                borderTop: '2px solid #e5e7eb',
                margin: '32px 0',
              }}
            />
          )
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

// 使用 memo 优化性能，避免不必要的重新渲染
export default memo(MarkdownRenderer)
