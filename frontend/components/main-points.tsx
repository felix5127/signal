// Input: main_points_zh 或 main_points 数组（{ point, explanation }）
// Output: 渲染可展开的主要观点列表
// Position: 资源详情页的主要观点展示组件
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { useState } from 'react'

interface MainPoint {
  point: string
  explanation: string
}

interface MainPointsProps {
  points: MainPoint[] | null
  className?: string
}

export function MainPoints({ points, className = '' }: MainPointsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  if (!points || points.length === 0) {
    return null
  }

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index)
  }

  return (
    <div className={className}>
      <style jsx>{`
        .main-points-container {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .point-card {
          background: #fafafa;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.2s ease;
        }

        .point-card:hover {
          border-color: #6366f1;
          box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
        }

        .point-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 16px;
          cursor: pointer;
          user-select: none;
        }

        .point-number {
          flex-shrink: 0;
          width: 28px;
          height: 28px;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          color: white;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
        }

        .point-content {
          flex: 1;
          min-width: 0;
        }

        .point-text {
          font-size: 15px;
          font-weight: 600;
          color: #1f2937;
          line-height: 1.5;
          margin: 0;
        }

        .expand-icon {
          flex-shrink: 0;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #9ca3af;
          transition: transform 0.2s ease;
        }

        .expand-icon.expanded {
          transform: rotate(180deg);
        }

        .explanation {
          padding: 0 16px 16px 56px;
          color: #4b5563;
          font-size: 14px;
          line-height: 1.7;
          border-top: 1px dashed #e5e7eb;
          margin-top: 0;
          padding-top: 12px;
          animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      <div className="main-points-container">
        {points.map((item, index) => (
          <div key={index} className="point-card">
            <div
              className="point-header"
              onClick={() => toggleExpand(index)}
            >
              <div className="point-number">{index + 1}</div>
              <div className="point-content">
                <p className="point-text">{item.point}</p>
              </div>
              <div className={`expand-icon ${expandedIndex === index ? 'expanded' : ''}`}>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M4 6l4 4 4-4" />
                </svg>
              </div>
            </div>

            {expandedIndex === index && item.explanation && (
              <div className="explanation">
                {item.explanation}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
