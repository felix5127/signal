# UI/UX Pro Max 全面重构计划

> 风格: Mercury.com 简洁大气风格
> 开始时间: 2026-01-25
> 状态: in_progress

## 目标

将 Signal Hunter 前端从当前混乱的多设计系统状态，重构为统一的 Mercury 风格：
- 简洁大气的视觉语言
- 墨绿色主色调 (#188554)
- 大圆角 (2rem)
- 微妙的玻璃效果
- 统一的设计系统

---

## Phase 1: 设计系统基础重构
**状态**: `pending`

### 任务清单
- [ ] 1.1 清理 globals.css - 移除冗余的 3 套变量系统
- [ ] 1.2 创建新的 Mercury 风格 CSS 变量
- [ ] 1.3 更新 globals-neumorphic.css 为新设计系统
- [ ] 1.4 定义玻璃效果工具类
- [ ] 1.5 定义排版系统（字体、字重、行高）

### 关键文件
- `frontend/app/globals.css`
- `frontend/app/globals-neumorphic.css`
- `frontend/tailwind.config.ts`

### 验收标准
- 只有一套统一的 CSS 变量
- 所有颜色通过变量引用
- 玻璃效果类可用

---

## Phase 2: 核心 UI 组件升级
**状态**: `pending`

### 任务清单
- [ ] 2.1 Button 组件 - Mercury 风格按钮
- [ ] 2.2 Card 组件 - 简洁大圆角卡片
- [ ] 2.3 Input 组件 - 简洁输入框
- [ ] 2.4 Badge 组件 - 简洁标签
- [ ] 2.5 Skeleton 组件 - 加载骨架屏

### 关键文件
- `frontend/components/ui/button.tsx`
- `frontend/components/ui/card.tsx`
- `frontend/components/ui/input.tsx`
- `frontend/components/ui/badge.tsx`
- `frontend/components/ui/skeleton.tsx`

### 验收标准
- 所有组件使用新设计系统变量
- 圆角统一为 2rem
- 交互动画流畅 (200-300ms)

---

## Phase 3: 导航栏重构
**状态**: `pending`

### 任务清单
- [ ] 3.1 Navbar 组件 - 简洁玻璃效果
- [ ] 3.2 移动端菜单优化
- [ ] 3.3 Logo 样式更新
- [ ] 3.4 导航项 hover/active 状态

### 关键文件
- `frontend/components/navbar.tsx`

### 验收标准
- 导航栏使用玻璃效果
- 滚动时增强模糊
- 移动端体验流畅

---

## Phase 4: 首页重构
**状态**: `pending`

### 任务清单
- [ ] 4.1 Hero 区域 - 简洁大气背景
- [ ] 4.2 Features 区域 - 简化视觉
- [ ] 4.3 Content Hub 卡片 - Mercury 风格
- [ ] 4.4 CTA 区域 - 墨绿主色按钮

### 关键文件
- `frontend/components/home-page-content.tsx`
- `frontend/components/landing/Hero.tsx`
- `frontend/components/landing/FeaturesSection.tsx`
- `frontend/components/content-hub-cards.tsx`

### 验收标准
- 首页视觉统一
- 背景效果微妙不喧宾夺主
- CTA 明确突出

---

## Phase 5: 列表页优化
**状态**: `pending`

### 任务清单
- [ ] 5.1 ResourceCard 组件 - Mercury 风格
- [ ] 5.2 ArticleListCard 组件 - 统一样式
- [ ] 5.3 TweetCard 组件 - 统一样式
- [ ] 5.4 筛选工具栏 - 简化设计
- [ ] 5.5 无限滚动加载状态

### 关键文件
- `frontend/components/resource-card.tsx`
- `frontend/components/article-list-card.tsx`
- `frontend/components/tweet-card.tsx`
- `frontend/components/compact-filter-toolbar.tsx`
- `frontend/components/resource-list-page.tsx`

### 验收标准
- 所有卡片风格统一
- 加载状态有骨架屏
- 筛选器简洁易用

---

## Phase 6: 详情页优化
**状态**: `pending`

### 任务清单
- [ ] 6.1 资源详情页布局优化
- [ ] 6.2 AI 侧边栏样式
- [ ] 6.3 内容区域排版
- [ ] 6.4 播客详情页特殊设计

### 关键文件
- `frontend/components/resource-detail.tsx`
- `frontend/components/detail/*.tsx`
- `frontend/components/podcast/*.tsx`

### 验收标准
- 详情页阅读体验舒适
- 侧边栏信息清晰
- 播客播放器美观

---

## Phase 7: 交互与动画优化
**状态**: `pending`

### 任务清单
- [ ] 7.1 统一 Spring 动画配置
- [ ] 7.2 页面过渡动画优化
- [ ] 7.3 微交互统一（hover, active, focus）
- [ ] 7.4 加载状态动画

### 关键文件
- `frontend/lib/motion.ts`
- `frontend/components/page-transition.tsx`

### 验收标准
- 所有动画时长一致 (200-300ms)
- 页面切换流畅
- 交互反馈明确

---

## Phase 8: 最终测试与收尾
**状态**: `pending`

### 任务清单
- [ ] 8.1 全站视觉一致性检查
- [ ] 8.2 响应式布局测试
- [ ] 8.3 暗色模式适配（如需要）
- [ ] 8.4 性能检查
- [ ] 8.5 更新 CLAUDE.md 文档

### 验收标准
- 所有页面风格统一
- 移动端体验良好
- 文档同步更新

---

## 设计规范速查

### 颜色
```
主色: #188554 (墨绿)
主色浅: #f1f7f3
强调色: #8a753c (琥珀金)
背景: #fbfcfd
文字: #272735
次要文字: #6b7280
边框: rgba(0,0,0,0.06)
```

### 圆角
```
小: 0.5rem (8px)
中: 1rem (16px)
大: 2rem (32px) - 默认
特大: 2.5rem (40px)
```

### 玻璃效果
```
轻度: rgba(251,252,253,0.7) + blur(12px)
标准: rgba(251,252,253,0.6) + blur(16px)
```

### 动画
```
快速: 150ms ease
标准: 200ms ease
慢速: 300ms ease
```

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| - | - | - |

---

## Notes
- Mercury 风格核心：简洁、留白、专业
- 避免过度装饰，让内容说话
- 玻璃效果克制使用，不要喧宾夺主
