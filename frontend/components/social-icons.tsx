// Input: 社交平台类型 (twitter/github/linkedin等)
// Output: 社交媒体图标组件（使用 react-icons）
// Position: UI 组件，用于页脚、作者信息等场景
// 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import {
  SiX,
  SiGithub,
  SiLinkedin,
  SiYoutube,
  SiInstagram,
  SiFacebook,
  SiTelegram,
  SiDiscord,
  SiReddit,
  SiYcombinator,
} from 'react-icons/si'

// 社交平台配置
const SOCIAL_PLATFORMS = {
  twitter: {
    icon: SiX,
    color: 'text-black dark:text-white',
    hoverColor: 'hover:text-gray-700 dark:hover:text-gray-300',
    label: 'X (Twitter)',
  },
  github: {
    icon: SiGithub,
    color: 'text-gray-700 dark:text-gray-300',
    hoverColor: 'hover:text-gray-900 dark:hover:text-white',
    label: 'GitHub',
  },
  linkedin: {
    icon: SiLinkedin,
    color: 'text-blue-600',
    hoverColor: 'hover:text-blue-700',
    label: 'LinkedIn',
  },
  youtube: {
    icon: SiYoutube,
    color: 'text-red-600',
    hoverColor: 'hover:text-red-700',
    label: 'YouTube',
  },
  instagram: {
    icon: SiInstagram,
    color: 'text-pink-600',
    hoverColor: 'hover:text-pink-700',
    label: 'Instagram',
  },
  facebook: {
    icon: SiFacebook,
    color: 'text-blue-500',
    hoverColor: 'hover:text-blue-600',
    label: 'Facebook',
  },
  telegram: {
    icon: SiTelegram,
    color: 'text-blue-400',
    hoverColor: 'hover:text-blue-500',
    label: 'Telegram',
  },
  discord: {
    icon: SiDiscord,
    color: 'text-indigo-500',
    hoverColor: 'hover:text-indigo-600',
    label: 'Discord',
  },
  reddit: {
    icon: SiReddit,
    color: 'text-orange-500',
    hoverColor: 'hover:text-orange-600',
    label: 'Reddit',
  },
  hackernews: {
    icon: SiYcombinator,
    color: 'text-orange-600',
    hoverColor: 'hover:text-orange-700',
    label: 'Hacker News',
  },
} as const

type SocialPlatform = keyof typeof SOCIAL_PLATFORMS

interface SocialIconProps {
  platform: SocialPlatform
  href?: string
  size?: number
  showLabel?: boolean
  className?: string
}

export function SocialIcon({
  platform,
  href,
  size = 24,
  showLabel = false,
  className = ''
}: SocialIconProps) {
  const config = SOCIAL_PLATFORMS[platform]
  const Icon = config.icon

  const iconComponent = (
    <motion.div
      whileHover={{ y: -2, scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        'inline-flex items-center space-x-2 transition-colors duration-200',
        config.color,
        config.hoverColor,
        className
      )}
    >
      <Icon size={size} />
      {showLabel && <span className="text-sm font-medium">{config.label}</span>}
    </motion.div>
  )

  if (href) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={config.label}
      >
        {iconComponent}
      </a>
    )
  }

  return iconComponent
}

// 社交图标列表（用于页脚）
interface SocialIconsProps {
  icons: Array<{ platform: SocialPlatform; href: string }>
  size?: number
  className?: string
}

export function SocialIcons({ icons, size = 24, className = '' }: SocialIconsProps) {
  return (
    <div className={cn('flex items-center space-x-4', className)}>
      {icons.map((item, index) => (
        <motion.div
          key={item.platform}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1, duration: 0.3 }}
        >
          <SocialIcon platform={item.platform} href={item.href} size={size} />
        </motion.div>
      ))}
    </div>
  )
}

// 快捷方式：常用社交图标组合
export const COMMON_SOCIAL_ICONS = {
  twitter: (href: string) => ({ platform: 'twitter' as const, href }),
  github: (href: string) => ({ platform: 'github' as const, href }),
  linkedin: (href: string) => ({ platform: 'linkedin' as const, href }),
}
