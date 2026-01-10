// Input: ResourceCard 组件 + index
// Output: 带有动画效果的资源卡片包装器
// Position: 卡片动效增强组件，为现有 ResourceCard 添加 framer-motion 动画
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { motion } from 'framer-motion'
import { ResourceCard, type Resource } from '@/components/resource-card'

interface AnimatedResourceCardProps {
  resource: Resource
  index?: number
  className?: string
}

export default function AnimatedResourceCard({
  resource,
  index = 0,
  className = ''
}: AnimatedResourceCardProps) {
  // 根据索引计算延迟（最多 0.5 秒）
  const delay = Math.min(index * 0.05, 0.5)

  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.4, 0, 0.2, 1],
      }}
      whileHover={{
        y: -8,
        scale: 1.02,
        transition: {
          duration: 0.2,
          ease: [0.4, 0, 0.2, 1],
        }
      }}
      whileTap={{ scale: 0.98 }}
      className={className}
    >
      <ResourceCard resource={resource} />
    </motion.div>
  )
}

// 列表项动画（用于文章列表、推文等）
export function AnimatedListItem({
  children,
  index = 0,
  className = ''
}: {
  children: React.ReactNode
  index?: number
  className?: string
}) {
  const delay = Math.min(index * 0.03, 0.3)

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.3,
        delay,
        ease: [0.4, 0, 0.2, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
