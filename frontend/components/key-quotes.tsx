// Input: key_quotes_zh 或 key_quotes 字符串数组
// Output: 渲染引用样式的金句列表
// Position: 资源详情页的金句展示组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

interface KeyQuotesProps {
  quotes: string[] | null
  className?: string
}

export function KeyQuotes({ quotes, className = '' }: KeyQuotesProps) {
  if (!quotes || quotes.length === 0) {
    return null
  }

  return (
    <div className={className}>
      <style jsx>{`
        .quotes-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .quote-card {
          position: relative;
          background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
          border-radius: 12px;
          padding: 20px 24px 20px 48px;
          border-left: 4px solid #f59e0b;
        }

        .quote-icon {
          position: absolute;
          left: 16px;
          top: 16px;
          color: #d97706;
          font-size: 24px;
          font-weight: 700;
          font-family: Georgia, serif;
          line-height: 1;
        }

        .quote-text {
          font-size: 15px;
          line-height: 1.7;
          color: #78350f;
          font-style: italic;
          margin: 0;
        }

        /* 交替颜色样式 */
        .quote-card:nth-child(2n) {
          background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
          border-left-color: #3b82f6;
        }

        .quote-card:nth-child(2n) .quote-icon {
          color: #2563eb;
        }

        .quote-card:nth-child(2n) .quote-text {
          color: #1e3a8a;
        }

        .quote-card:nth-child(3n) {
          background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
          border-left-color: #22c55e;
        }

        .quote-card:nth-child(3n) .quote-icon {
          color: #16a34a;
        }

        .quote-card:nth-child(3n) .quote-text {
          color: #14532d;
        }

        .quote-card:nth-child(4n) {
          background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
          border-left-color: #a855f7;
        }

        .quote-card:nth-child(4n) .quote-icon {
          color: #9333ea;
        }

        .quote-card:nth-child(4n) .quote-text {
          color: #581c87;
        }
      `}</style>

      <div className="quotes-container">
        {quotes.map((quote, index) => (
          <div key={index} className="quote-card">
            <span className="quote-icon">&ldquo;</span>
            <p className="quote-text">{quote}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
