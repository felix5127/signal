// Input: tags 字符串数组
// Output: 渲染可点击的标签列表
// Position: 资源详情页的标签展示组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

interface TagListProps {
  tags: string[] | null
  onTagClick?: (tag: string) => void
  className?: string
}

export function TagList({ tags, onTagClick, className = '' }: TagListProps) {
  if (!tags || tags.length === 0) {
    return null
  }

  const handleClick = (tag: string) => {
    if (onTagClick) {
      onTagClick(tag)
    }
  }

  return (
    <div className={className}>
      <style jsx>{`
        .tags-container {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .tag {
          display: inline-flex;
          align-items: center;
          padding: 6px 14px;
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          border: 1px solid #c7d2fe;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
          color: #4338ca;
          cursor: pointer;
          transition: all 0.2s ease;
          text-decoration: none;
        }

        .tag:hover {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border-color: #6366f1;
          color: white;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .tag:active {
          transform: translateY(0);
        }

        .tag-hash {
          margin-right: 2px;
          opacity: 0.7;
        }
      `}</style>

      <div className="tags-container">
        {tags.map((tag, index) => (
          <span
            key={index}
            className="tag"
            onClick={() => handleClick(tag)}
          >
            <span className="tag-hash">#</span>
            {tag.trim()}
          </span>
        ))}
      </div>
    </div>
  )
}
