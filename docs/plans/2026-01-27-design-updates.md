# 设计变更日志 - 2026-01-27

> 基于 Pencil 设计稿 `/Users/felix/Desktop/ssss.pen` 的设计同步

## 变更概览

| 变更项 | 影响范围 | 状态 |
|--------|----------|------|
| 推文卡片"显示全文"按钮 | tweet-card.tsx, tweets/page.tsx | 设计完成 |
| Footer 品牌统一 | Footer.tsx, 所有页面 | 设计完成 |
| Footer 链接结构统一 | Footer.tsx | 设计完成 |

---

## 1. 推文卡片设计优化

### 设计决策
推文不需要详情页，直接在卡片内展开全文内容。

### 规格
- **按钮文案**: "显示全文"
- **按钮图标**: chevron-down (Lucide)
- **按钮颜色**: #1E3A5F (深海军蓝)
- **按钮字号**: 13px
- **卡片间距**: 16px (卡片之间)

### 交互行为
1. 默认状态：显示截断的推文内容
2. 点击"显示全文"：展开完整推文
3. 展开后按钮变为"收起" + chevron-up 图标

### 实现要点
- 使用 `useState` 控制展开状态
- 动画过渡使用 Framer Motion
- 保持 Mercury 风格一致性

---

## 2. Footer 品牌统一

### 设计决策
所有页面 Footer 使用统一的品牌元素，强化产品认知。

### 规格
- **Logo 图标**: `Radar` (Lucide React)
- **品牌名称**: Signal Hunter
- **品牌描述**: "AI 驱动的技术情报分析平台，帮助你发现改变世界的技术信号。"

### 涉及页面
- 首页 (/)
- 推文页 (/tweets)
- 播客页 (/podcasts)
- 视频页 (/videos)
- 播客详情页 (/resources/[id])
- 视频详情页 (/resources/[id])
- 文章页 (/articles)
- 精选页 (/featured)

---

## 3. Footer 链接结构统一

### 设计决策
简化 Footer 链接结构，从 4 列减少为 2 列，突出核心内容。

### 旧结构（已废弃）
```
产品 | 资源 | 支持 | 法律
```

### 新结构
```
内容                   | 关于
- 文章 (/articles)    | - 关于我们 (/about)
- 视频 (/videos)      | - 联系方式 (/contact)
- 播客 (/podcasts)    |
- 推文 (/tweets)      |
```

### 实现要点
- 使用 2 列 Grid 布局
- 响应式：移动端单列，桌面端双列
- 链接使用 Next.js Link 组件

---

## Mercury 风格颜色系统参考

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 背景色 | #FBFCFD | 极浅灰白 |
| 主色调 | #1E3A5F | 深海军蓝 |
| 主文字 | #272735 | 近黑色 |
| 次要文字 | #6B6B6B | 中灰色 |
| 弱化文字 | #9A9A9A | 浅灰色 |
| 边框 | rgba(0,0,0,0.06) | 微透明黑 |

---

## 待实现任务

- [x] 更新 tweet-card.tsx 添加"显示全文"功能 ✅
- [x] 更新 Footer.tsx 统一品牌和链接结构 ✅
- [ ] 验证所有页面 Footer 一致性（需启动服务）
- [x] 添加展开/收起动画 ✅

---

## 相关文件

- 设计稿: `/Users/felix/Desktop/ssss.pen`
- 组件文档: `frontend/components/CLAUDE.md`
- 进度日志: `docs/plans/2026-01-25-ui-ux-progress.md`
