/**
 * [INPUT]: 依赖 @/components/ui 的 Button、Card、Input、Badge 组件
 * [OUTPUT]: 对外提供微拟物设计展示页面，展示所有升级组件的视觉效果
 * [POS]: app/ 的演示页面，独立路由 /neumorphic-showcase
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Palette, Sparkles, Zap, Layers } from 'lucide-react'

export default function NeumorphicShowcase() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-950/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-center space-x-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl shadow-[var(--shadow-raised)]">
              <Palette className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                微拟物设计系统
              </h1>
              <p className="text-muted-foreground mt-1">
                Neumorphic Design Components Showcase
              </p>
            </div>
          </div>

          <p className="text-lg text-muted-foreground max-w-3xl mt-6">
            基于三段式渐变背景 + 三层立体阴影 + 微交互动画的现代化设计语言。
            每个组件都经过精心设计，提供流畅的视觉反馈和优雅的用户体验。
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-24">

        {/* Button Showcase */}
        <section>
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
              <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold">Button 按钮</h2>
              <p className="text-muted-foreground mt-1">
                渐变背景 + 立体阴影 + 微交互动画
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Primary Variants */}
            <Card variant="raised">
              <CardHeader>
                <CardTitle>主要按钮</CardTitle>
                <CardDescription>Primary & Default</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full" variant="default">
                  Default
                </Button>
                <Button className="w-full" variant="primary">
                  Primary
                </Button>
              </CardContent>
            </Card>

            {/* Accent & Destructive */}
            <Card variant="raised">
              <CardHeader>
                <CardTitle>强调按钮</CardTitle>
                <CardDescription>Accent & Destructive</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full" variant="accent">
                  Accent
                </Button>
                <Button className="w-full" variant="destructive">
                  Destructive
                </Button>
              </CardContent>
            </Card>

            {/* Secondary & Outline */}
            <Card variant="raised">
              <CardHeader>
                <CardTitle>次要按钮</CardTitle>
                <CardDescription>Secondary & Outline</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full" variant="secondary">
                  Secondary
                </Button>
                <Button className="w-full" variant="outline">
                  Outline
                </Button>
              </CardContent>
            </Card>

            {/* Size Variants */}
            <Card variant="raised" className="md:col-span-2 lg:col-span-3">
              <CardHeader>
                <CardTitle>尺寸变体</CardTitle>
                <CardDescription>Size Variants</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <Button size="sm">Small</Button>
                  <Button size="default">Default</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button size="xl">Extra Large</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Card Showcase */}
        <section>
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
              <Layers className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold">Card 卡片</h2>
              <p className="text-muted-foreground mt-1">
                凸起 / 内凹 / 边框变体
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card variant="default">
              <CardHeader>
                <CardTitle>Default 默认</CardTitle>
                <CardDescription>标准阴影效果</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  使用默认 Tailwind shadow，适用于大多数场景。
                </p>
              </CardContent>
            </Card>

            <Card variant="raised">
              <CardHeader>
                <CardTitle>Raised 凸起</CardTitle>
                <CardDescription>凸起效果</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  使用 CSS 变量的三层阴影系统，创建立体凸起效果。
                  悬停时阴影增强。
                </p>
              </CardContent>
            </Card>

            <Card variant="inset">
              <CardHeader>
                <CardTitle>Inset 内凹</CardTitle>
                <CardDescription>内凹效果</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  使用内阴影创建凹陷效果，适合用于容器或嵌入区域。
                </p>
              </CardContent>
            </Card>

            <Card variant="outline" className="md:col-span-2 lg:col-span-3">
              <CardHeader>
                <CardTitle>Outline 边框</CardTitle>
                <CardDescription>边框变体</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  轻微阴影，强调边框，适用于需要明确边界的场景。
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Input Showcase */}
        <section>
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
              <Zap className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold">Input 输入框</h2>
              <p className="text-muted-foreground mt-1">
                内凹阴影 + 聚焦增强
              </p>
            </div>
          </div>

          <Card variant="raised">
            <CardHeader>
              <CardTitle>文本输入</CardTitle>
              <CardDescription>内凹效果营造深度感</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">用户名</label>
                <Input placeholder="输入用户名" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">邮箱</label>
                <Input type="email" placeholder="user@example.com" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">密码</label>
                <Input type="password" placeholder="••••••••" />
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Badge Showcase */}
        <section>
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-xl">
              <Sparkles className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold">Badge 标签</h2>
              <p className="text-muted-foreground mt-1">
                渐变背景 + 立体阴影
              </p>
            </div>
          </div>

          <Card variant="raised">
            <CardHeader>
              <CardTitle>标签变体</CardTitle>
              <CardDescription>Badge Variants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Badge variant="default">Default</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="destructive">Destructive</Badge>
                <Badge variant="outline">Outline</Badge>
              </div>

              <div className="mt-8">
                <h4 className="text-sm font-medium mb-3">使用场景示例</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span className="text-sm">状态</span>
                    <Badge variant="default">活跃</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span className="text-sm">优先级</span>
                    <Badge variant="destructive">高</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span className="text-sm">分类</span>
                    <Badge variant="secondary">标签</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Design Principles */}
        <section className="border-t border-gray-200 dark:border-gray-800 pt-16">
          <h2 className="text-3xl font-bold mb-8 text-center">设计原则</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card variant="raised">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span className="text-2xl">🎨</span>
                  <span>三段式渐变</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  亮色 → 混合85%黑 → 混合70%黑，创造自然的深度和立体感。
                </p>
              </CardContent>
            </Card>

            <Card variant="raised">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span className="text-2xl">✨</span>
                  <span>三层阴影</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  外投影 + 顶部高光 + 底部暗边，营造真实的物理质感。
                </p>
              </CardContent>
            </Card>

            <Card variant="raised">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span className="text-2xl">⚡</span>
                  <span>微交互</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  悬停放大 1.02，点击缩小 0.97，提供流畅的触觉反馈。
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

      </div>
    </div>
  )
}
