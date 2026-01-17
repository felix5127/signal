# Signal Hunter PRD v2.3 完整梳理

> 基于 PRD.md 的结构化整理文档
> 整理时间: 2026-01-17

## 文档元数据

| 属性 | 值 |
|------|-----|
| 版本 | V2.3 (Transcription Implementation) |
| 更新 | 2026-01-03 |
| 定位 | 一比一复现 BestBlogs.dev |
| 目标用户 | 技术 KOL、独立开发者、科技博主 |

---

## 一、内容类型体系

### 1.1 四种内容类型

| 类型 | 数据源 | 数量 | 处理流程 | 状态 |
|------|--------|------|----------|------|
| **文章** | BestBlogs OPML | 170源 | RSS → Playwright全文 → LLM | ✅ |
| **播客** | BestBlogs OPML | 30源 | RSS → 通义听悟转写 → LLM | ✅ 已实现 |
| **推文** | BestBlogs Twitter | 160账号 | XGo.ing → LLM | ⏳ |
| **视频** | BestBlogs OPML | 40源 | RSS → 转写 → LLM | ⏳ 元数据已实现 |

### 1.2 数据源文件

```
BestBlog/
├── BestBlogs_RSS_Articles.opml   # 170个文章源
├── BestBlogs_RSS_Podcasts.opml   # 30个播客源
├── BestBlogs_RSS_Twitters.opml   # 160个Twitter账号
└── BestBlogs_RSS_Videos.opml     # 40个视频源
```

---

## 二、后端功能规格

### 2.1 数据采集模块 (DC-01 ~ DC-12)

**RSS 采集**

| ID | 功能 | 优先级 |
|----|------|--------|
| DC-01 | OPML 解析 | P0 |
| DC-02 | RSS 定时拉取 (APScheduler) | P0 |
| DC-03 | 增量更新 | P0 |
| DC-04 | 源图标抓取 | P1 |

**全文提取**

| ID | 功能 | 优先级 |
|----|------|--------|
| DC-05 | Playwright 全文提取 | P0 |
| DC-06 | HTML → Markdown 转换 | P0 |
| DC-07 | 字数统计 + 阅读时长 | P0 |
| DC-08 | 正文选择器配置 | P1 |

**播客转写** (✅ 已实现)

| ID | 功能 | 实现文件 |
|----|------|----------|
| DC-11 | 通义听悟 API 集成 | `backend/app/processors/transcriber.py` |
| DC-12 | 转写结果存储 | 同上 |

### 2.2 LLM 处理模块 (LP-01 ~ LP-10)

**初评流程 (规则 + LLM)**

```json
{
  "ignore": boolean,     // 是否忽略
  "reason": "string",    // 判断原因 (30-50字)
  "value": 0-5,          // 价值评分
  "summary": "string",   // 一句话总结
  "language": "zh/en"    // 语言识别
}
```

**深度分析流程 (三步)**

```
LP-05: 全文分析 → LP-06: 检查反思 → LP-07: 优化改进
```

**分析输出格式 (BestBlogs DSL)**

```json
{
  "oneSentenceSummary": "一句话总结 (50字内)",
  "summary": "详细摘要 (200-400字)",
  "domain": "软件编程/人工智能/产品设计/商业科技",
  "aiSubcategory": "AI模型/AI开发/AI产品/AI资讯/其他",
  "tags": ["标签1", "标签2"],
  "mainPoints": [{"point": "观点", "explanation": "解释"}],
  "keyQuotes": ["金句1", "金句2"],
  "score": 85,
  "improvements": "改进建议"
}
```

**翻译流程 (三步)**

```
LP-08: 初次翻译 → LP-09: 检查反思 → LP-10: 意译优化
```

### 2.3 评分体系

| 维度 | 分值 | 说明 |
|------|------|------|
| 内容深度 | 30分 | 技术专业度、分析严谨性 |
| 相关性 | 30分 | 领域契合度、时效性 |
| 实用性 | 20分 | 方案可执行性 |
| 创新性 | 10分 | 观点与方法创新 |
| 调整分 | -10~+5 | 加分/减分项 |

**评分分级**

| 区间 | 等级 | 颜色 |
|------|------|------|
| 91-100 | 推荐阅读 | 🟢 绿色 |
| 86-90 | 值得一读 | 🔵 蓝色 |
| 75-85 | 基础阅读 | ⚪ 灰色 |
| 0-74 | 暂不推荐 | - |

**精选标记**: score ≥ 85 自动标记

### 2.4 分类体系

```
├── 软件编程
│   ├── 编程语言 / 软件架构 / 开发工具
│   ├── 开源技术 / 软件工程 / 云服务
├── 人工智能
│   ├── AI模型 (大语言模型/理论研究/评测分析/训练优化)
│   ├── AI开发 (应用开发/提示词工程/开发框架/最佳实践)
│   ├── AI产品 (产品设计/智能助手/AIGC工具/产品评测)
│   └── AI资讯 (行业动态/企业新闻/专家观点/投融资)
├── 产品设计
│   ├── 产品策略 / 用户体验 / 产品运营 / 市场分析
└── 商业科技
    ├── 技术创业 / 商业模式 / 个人成长 / 领导力
```

### 2.5 数据库 Schema

**resources 表核心字段**

```sql
-- 类型与来源
type VARCHAR(20)              -- article/podcast/tweet/video
source_name VARCHAR(100)      -- RSS源名称
source_logo_url TEXT          -- 新增：源Logo

-- 原始内容
title TEXT
title_translated TEXT         -- 翻译后标题
word_count INTEGER            -- 新增：字数
read_time INTEGER             -- 新增：阅读时长

-- LLM分析
one_sentence_summary VARCHAR(500)
one_sentence_summary_zh VARCHAR(500)
summary TEXT / summary_zh TEXT
main_points JSONB / main_points_zh JSONB
key_quotes JSONB / key_quotes_zh JSONB

-- 分类评分
domain VARCHAR(50)            -- 一级分类
subdomain VARCHAR(50)         -- 二级分类 (AI专用)
tags JSONB
score INTEGER                 -- 0-100
is_featured BOOLEAN           -- score >= 85

-- 新增字段
language VARCHAR(10)          -- zh/en (带索引)

-- 播客专用
audio_url TEXT
duration INTEGER              -- 秒
transcript TEXT               -- 转写文本
```

**索引策略 (14个)**

```sql
idx_resources_type
idx_resources_type_score
idx_resources_domain
idx_resources_score
idx_resources_published
idx_resources_featured
idx_resources_language       -- 新增
idx_resources_source_name    -- 新增 (侧边栏用)
```

### 2.6 API 筛选参数完整规格

| 参数 | 类型 | 可选值 | 默认 |
|------|------|--------|------|
| `type` | string | article/podcast/tweet/video | all |
| `time` | string | all/1d/3d/1w/1m/3m/1y | 1w |
| `lang` | string | zh/en/all | all |
| `domain` | string | programming/ai/product/business | all |
| `sort` | string | default/time/score | default |
| `q` | string | 任意 | - |
| `sourceid` | string | 源ID | - |
| `qualified` | boolean | true/false | false |
| `score` | number | 91/86/75 | - |

### 2.7 API 端点清单

| 方法 | 路径 | 新增 |
|------|------|------|
| GET | `/api/resources` | - |
| GET | `/api/resources/:id` | - |
| GET | `/api/search` | - |
| GET | `/api/sources/popular` | ✅ |
| GET | `/api/stats` | - |
| GET | `/api/feeds/rss` | - |
| POST | `/api/trigger-pipeline` | - |
| POST | `/api/trigger-twitter` | - |
| POST | `/api/trigger-podcast` | ✅ |
| POST | `/api/trigger-video` | ✅ |

### 2.8 RSS 输出

| 类型 | URL |
|------|-----|
| 全站 | `/feeds/rss` |
| 按类型 | `/feeds/rss?type=article` |
| 按分类 | `/feeds/rss?domain=ai` |
| 按语言 | `/feeds/rss?lang=zh` |
| 精选 | `/feeds/rss?featured=true` |
| 高分 | `/feeds/rss?score=91` |

---

## 三、前端功能规格

### 3.1 页面结构

```
/                      首页
├── Hero Section       价值主张 + CTA + 来源Logo
├── Tab 导航           文章 | 播客 | 推文 | 视频
├── 筛选栏             时间/语言/分类/评分/排序
├── 热门来源侧边栏      按当前筛选显示热门源
└── 内容列表           卡片网格 + 无限滚动

/resources/:id         详情页
├── 元信息             来源/作者/时间/字数/时长
├── 评分展示           0-100分 + 精选标记 + 颜色
├── 一句话总结
├── 详细摘要           可展开/收起
├── 主要观点           列表展示
├── 金句               引用样式
└── 原文链接

/newsletters           周刊页
/feeds                 RSS 订阅说明
```

### 3.2 筛选栏规格

**常规筛选 (一级入口)**

| 筛选项 | 选项 | 默认 | URL参数 |
|--------|------|------|---------|
| 时间 | 全部/1天/3天/1周/1月/3月/1年 | 1周 | `time` |
| 语言 | 不限/中文/英文 | 不限 | `lang` |
| 分类 | 全部/编程/AI/产品/商业 | 全部 | `domain` |
| 排序 | 默认/时间/评分 | 默认 | `sort` |
| 评分 | 全部/91+/86+/75+ | 全部 | `score` |

**高级筛选**

| 筛选项 | URL参数 |
|--------|---------|
| 关键词搜索 | `q` |
| 指定源 | `sourceid` |
| 精选内容 | `qualified=true` |

### 3.3 卡片组件规格

```
┌─────────────────────────────────────────────────────────┐
│ [图标] 机器之心  ·  2小时前  ·  人工智能  [⭐精选]      │
├─────────────────────────────────────────────────────────┤
│ 文章标题（可点击跳转详情页）                              │
│                                                         │
│ AI 生成的文章摘要，2-3 行文字...                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [91分] [5014字 · 约21分钟] [标签1] [标签2]             │
└─────────────────────────────────────────────────────────┘
```

**新增元素**

- 来源图标 (`source_logo_url`)
- 字数 + 阅读时间 (`word_count`, `read_time`)
- 评分徽章颜色分级 (91+绿/86-90蓝/75-85灰)

### 3.4 无限滚动实现

```typescript
// Intersection Observer API
const observer = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting && hasMore && !isLoading) {
      onLoadMore();
    }
  },
  { rootMargin: `${threshold}px` }
);
```

---

## 四、UI 设计规范

### 4.1 设计风格演进

| 版本 | 风格 | 参考 |
|------|------|------|
| V1 | 基础 shadcn/ui | - |
| V2 | 极简主义重构 | Linear / Raycast / Vercel |
| V2.3 | VisionOS 浮动玻璃岛 | Apple VisionOS |

### 4.2 VisionOS 玻璃岛规格

**True Optical Glass 配方**

```css
bg-white/70              /* 70% 透明度白色 */
backdrop-blur-2xl        /* 超强模糊 (40px+) */
backdrop-saturate-150    /* 提高背景饱和度 */
shadow-[0_8px_30px_rgba(0,0,0,0.08)]  /* 柔和深度阴影 */
/* 注意：移除 border 和 ring，纯靠阴影悬浮 */
```

**Header 浮动玻璃岛**

| 属性 | 值 |
|------|-----|
| 定位 | `fixed top-4 left-1/2 -translate-x-1/2` |
| 最大宽度 | `max-w-4xl` |
| 圆角 | `rounded-full` |

**背景层次**

```
z-20: FlickeringGrid (闪烁网格，最底层)
z-10: Aurora 渐变光球 (紫/蓝/粉色)
z-50: Header (浮动玻璃岛)
z-50: 搜索栏 (毛玻璃输入框)
z-10: 内容列表
```

### 4.3 工具栏筛选器

**按钮规格**

| 状态 | 背景 | 文字颜色 |
|------|------|----------|
| 默认 | transparent | `text-slate-600` |
| 激活 | `bg-violet-50` | `text-violet-700` |

**下拉菜单**

| 属性 | 值 |
|------|-----|
| 圆角 | `rounded-lg` |
| 阴影 | `shadow-xl` |
| 最小宽度 | `min-w-[200px]` |

---

## 五、开发阶段规划

### Phase 1: 核心功能 ✅

- 数据库基础结构
- RSS 采集 + 全文提取
- LLM 三步分析流程
- 前端列表页 + 详情页
- 基础筛选功能

### Phase 1.5: 筛选增强 ✅

- 语言筛选 (`lang=`)
- 评分梯度筛选 (`score=`)
- 无限滚动组件
- 热门来源 API + 侧边栏
- 卡片显示增强
- Hero Section

### Phase 2: 功能完善 (进行中)

- ⏳ 翻译流程
- ⏳ Twitter 采集 (XGo.ing)
- ✅ 播客转写 (通义听悟)
- ✅ 视频采集 (元数据)
- ⏳ 搜索功能
- ⏳ RSS 输出

### Phase 3: 增强功能

- 周刊功能
- 视频内容转写
- 精选标记优化
- 性能优化

---

## 六、技术栈总览

| 层级 | 技术 |
|------|------|
| 前端框架 | Next.js 14 (App Router) |
| UI组件 | Tailwind CSS + shadcn/ui |
| 后端框架 | FastAPI + Pydantic v2 |
| 数据库 | PostgreSQL (JSONB + 全文检索) |
| 全文提取 | Playwright |
| 播客转写 | 通义听悟 |
| Twitter | XGo.ing |
| LLM | OpenRouter (Gemini Flash 3.0) |
| 任务调度 | APScheduler |
| 部署 | Railway (后端) + Vercel (前端) |

---

## 七、验收标准

### Phase 1.5 验收（筛选增强）

| 功能 | 验收标准 |
|------|----------|
| 语言筛选 | 中文/英文筛选正常工作，URL 同步 |
| 评分梯度 | 91+/86+/75+ 梯度筛选正常 |
| 无限滚动 | 滚动到底部自动加载更多，无重复加载 |
| 热门来源侧边栏 | 正确显示当前筛选下的热门来源，点击可筛选 |
| 卡片增强 | 显示源图标、字数、阅读时间，评分颜色分级 |
| Hero Section | 首页正确展示价值主张、CTA、来源Logo |

### Phase 2 验收

| 指标 | 标准 |
|------|------|
| 翻译功能 | 英文内容正确翻译为中文 |
| Twitter | XGo.ing 采集正常 |
| 播客 | 通义听悟转写正常 |
| RSS 输出 | 多种 RSS feed 可用 |
| 搜索 | 关键词搜索功能正常 |

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
