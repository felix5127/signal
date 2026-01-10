# App - Next.js 应用页面

使用 Next.js 14 App Router 定义的应用页面和路由。

## 文件清单

- `layout.tsx` - 根布局，定义全局样式、暗色模式支持和元数据
- `page.tsx` - BestBlogs风格首页（Client Component），Tab导航+筛选栏+卡片网格+分页
- `signals/[id]/page.tsx` - 信号详情页（Server Component），动态路由
- `resources/[id]/page.tsx` - 资源详情页
- `stats/page.tsx` - 统计页面
- `feeds/page.tsx` - RSS 订阅页面，展示各种 RSS Feed 订阅链接
- `globals.css` - 全局 Tailwind CSS 样式，包含深色/浅色主题变量

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
