# Signal Hunter PRD v3.0

> AI 技术情报聚合与深度分析平台
> 更新时间: 2026-01-29

## 文档元数据

| 属性 | 值 |
|------|-----|
| 版本 | v3.0 |
| 定位 | 面向超级个体的技术情报平台 |
| 目标用户 | 技术 KOL、独立开发者、科技博主、AI 从业者 |
| 参考 | BestBlogs.dev |

---

## 一、产品概述

### 1.1 核心价值

Signal Hunter 是一个 AI 驱动的技术情报聚合平台，自动从多个数据源采集高质量技术内容，通过 AI 进行深度分析、评分和摘要生成，帮助用户高效获取有价值的技术信息。

### 1.2 核心功能

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| **内容采集** | 多源 RSS 采集 (博客/播客/视频/推文) | ✅ 生产就绪 |
| **AI 分析** | 三步深度分析 + 评分 + 摘要生成 | ✅ 生产就绪 |
| **深度研究** | Tavily 搜索增强 + LLM 报告生成 | ✅ 生产就绪 |
| **研究助手** | NotebookLM 风格的多源研究工作台 | ✅ 基础完成 |
| **播客生成** | 文本转播客 (多角色对话) | ✅ 生产就绪 |
| **管理后台** | 审核/调度/监控/日志 | ✅ 生产就绪 |
| **用户认证** | JWT + OAuth (GitHub/Google) | ✅ 生产就绪 |

---

## 二、内容类型体系

### 2.1 四种内容类型

| 类型 | 数据源 | 数量 | 处理流程 | 状态 |
|------|--------|------|----------|------|
| **文章** | BestBlogs OPML | 51 源 | RSS → Playwright 全文 → LLM 分析 | ✅ 生产运行 |
| **播客** | BestBlogs OPML | 9 源 | RSS → 通义听悟转写 → LLM 分析 | ✅ 生产运行 |
| **视频** | BestBlogs OPML | 18 源 | RSS → 元数据提取 → 可选转写 | ✅ 生产运行 |
| **推文** | XGo.ing | 160 账号 | RSS Bridge → LLM 分析 | ⏳ 配置就绪 |

### 2.2 数据源文件

```
BestBlog/
├── BestBlogs_RSS_Articles.opml   # 51 个文章源
├── BestBlogs_RSS_Podcasts.opml   # 9 个播客源
├── BestBlogs_RSS_Videos.opml     # 18 个视频源
└── BestBlogs_RSS_Twitters.opml   # 160 个 Twitter 账号
```

### 2.3 已禁用数据源

以下数据源已于 2026-01-17 移除，专注于高质量 RSS 源：

- ❌ Hacker News
- ❌ GitHub Trending
- ❌ arXiv
- ❌ HuggingFace
- ❌ Product Hunt

---

## 三、后端功能规格

### 3.1 API 端点清单

#### 核心资源 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/resources` | 资源列表 (分页/筛选) |
| GET | `/api/resources/{id}` | 资源详情 |
| POST | `/api/resources/{id}/deep-research` | 触发深度研究 |
| GET | `/api/resources/{id}/deep-research` | 获取研究报告 |
| GET | `/api/search` | 全文搜索 |

#### 研究助手 API (v3)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET/POST | `/api/research/projects` | 项目管理 |
| GET/POST | `/api/research/sources` | 源材料管理 |
| POST | `/api/research/chat` | 对话交互 (SSE) |
| GET/POST | `/api/research/outputs` | 研究输出 |

#### 播客生成 API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/podcast/generate` | 生成播客 |
| POST | `/api/podcast/generate/stream` | 流式生成 (SSE) |
| GET | `/api/podcast/voices` | 可用声音列表 |

#### 管理后台 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET/POST | `/api/admin/sources` | 数据源管理 |
| GET | `/api/admin/stats/*` | 统计分析 |
| GET/POST | `/api/admin/review/*` | 人工审核 |
| GET/POST | `/api/admin/prompts` | Prompt 版本管理 |

#### 其他 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/feeds/{type}` | RSS 订阅输出 |
| GET | `/api/stats` | 统计数据 |
| GET | `/api/digest/*` | 每日/每周汇总 |
| GET | `/api/newsletters/*` | 周刊管理 |
| POST | `/api/tasks/pipeline/trigger` | 手动触发采集 |
| POST | `/api/auth/*` | 用户认证 |
| GET | `/api/export/*` | 数据导出 |
| GET | `/api/mindmap/*` | 概念图生成 |

### 3.2 筛选参数规格

| 参数 | 类型 | 可选值 | 默认 |
|------|------|--------|------|
| `type` | string | article/podcast/tweet/video | all |
| `time` | string | all/1d/3d/1w/1m/3m/1y | 1w |
| `lang` | string | zh/en/all | all |
| `domain` | string | programming/ai/product/business | all |
| `sort` | string | default/time/score | default |
| `q` | string | 搜索关键词 | - |
| `source_id` | string | 指定源 ID | - |
| `featured` | boolean | 精选内容 | false |
| `score` | number | 91/86/75 (最低分) | - |
| `page` | number | 页码 | 1 |
| `page_size` | number | 每页数量 | 20 |

### 3.3 LLM 处理流程

#### 初评流程 (规则 + LLM)

```json
{
  "ignore": false,
  "reason": "判断原因 (30-50字)",
  "value": 4,
  "summary": "一句话总结",
  "language": "zh"
}
```

#### 深度分析流程 (三步)

```
Step 1: 全文分析 → Step 2: 检查反思 → Step 3: 优化改进
```

#### 分析输出格式

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

#### 翻译流程 (三步)

```
Step 1: 初次翻译 → Step 2: 检查反思 → Step 3: 意译优化
```

### 3.4 评分体系

| 维度 | 分值 | 说明 |
|------|------|------|
| 内容深度 | 30分 | 技术专业度、分析严谨性 |
| 相关性 | 30分 | 领域契合度、时效性 |
| 实用性 | 20分 | 方案可执行性 |
| 创新性 | 10分 | 观点与方法创新 |
| 调整分 | -10~+5 | 加分/减分项 |

**评分分级**

| 区间 | 等级 | 标记 |
|------|------|------|
| 91-100 | 推荐阅读 | 绿色徽章 |
| 86-90 | 值得一读 | 蓝色徽章 |
| 75-85 | 基础阅读 | 灰色徽章 |
| 0-74 | 暂不推荐 | 无标记 |

**精选规则**: score ≥ 85 自动标记为精选

### 3.5 分类体系

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

### 3.6 定时任务配置

| 任务 | 频率 | 描述 |
|------|------|------|
| `main_pipeline_job` | 每 12 小时 | 博客/播客/视频采集 |
| `twitter_pipeline_job` | 每 1 小时 | Twitter 采集 |
| `daily_digest_job` | 每日 07:00 | 生成每日汇总 |
| `weekly_digest_job` | 周一 08:00 | 生成每周汇总 |
| `newsletter_job` | 周五 17:00 | 生成周刊 |

---

## 四、前端功能规格

### 4.1 页面结构

| 页面 | 路径 | 描述 | 状态 |
|------|------|------|------|
| 首页 | `/` | Hub 导航 + Hero + 内容标签页 | ✅ |
| Landing | `/landing` | 新用户引导页 | ✅ |
| 文章列表 | `/articles` | 文章内容列表 | ✅ |
| 播客列表 | `/podcasts` | 播客 + 音频播放器 | ✅ |
| 视频列表 | `/videos` | 视频内容列表 | ✅ |
| 推文列表 | `/tweets` | 推文 + 展开/收起 | ✅ |
| 精选内容 | `/featured` | 高分内容 (≥85) | ✅ |
| 周刊 | `/newsletters` | 周刊存档列表 | ✅ |
| RSS 订阅 | `/feeds` | 订阅说明页 | ✅ |
| 统计 | `/stats` | 数据仪表板 | ✅ |
| 详情页 | `/resources/[id]` | 内容详情 + AI 分析 | ✅ |
| 研究助手 | `/research` | 研究项目入口 | ✅ |
| 研究工作台 | `/research/workspace/[id]` | 三栏研究界面 | ✅ |
| 管理后台 | `/admin/*` | 审核/调度/监控 | ✅ |
| 设计系统 | `/design-system` | 组件展示 | ✅ |

### 4.2 核心组件

#### 布局组件

- `Navbar` - 浮动玻璃岛导航栏
- `Footer` - 品牌页脚
- `ClientLayout` - 客户端布局容器

#### 卡片组件

- `ResourceCard` - 通用资源卡片
- `ArticleListCard` - 文章卡片
- `PodcastCard` - 播客卡片
- `VideoCard` - 视频卡片
- `TweetCard` - 推文卡片 (展开/收起)

#### 详情页组件

- `ResourceDetail` - 资源详情主体
- `AISummaryCard` - AI 摘要卡片
- `AIAssistantCard` - AI 助手对话
- `RelatedContentCard` - 相关内容推荐

#### 研究助手组件

- `ProjectList` - 项目列表
- `Workspace` - 研究工作台
- `SourcesPanel` - 源材料面板
- `ChatPanel` - 对话面板
- `StudioPanel` - 输出工作室

#### 播客组件

- `AudioPlayer` - 音频播放器
- `PodcastDetail` - 播客详情
- `ContentTabs` - 章节/转录/问答标签

### 4.3 筛选栏规格

| 筛选项 | 选项 | 默认 |
|--------|------|------|
| 时间 | 全部/1天/3天/1周/1月/3月/1年 | 1周 |
| 语言 | 不限/中文/英文 | 不限 |
| 分类 | 全部/编程/AI/产品/商业 | 全部 |
| 排序 | 默认/时间/评分 | 默认 |
| 评分 | 全部/91+/86+/75+ | 全部 |

---

## 五、UI 设计规范

### 5.1 设计风格

| 版本 | 风格 | 特点 |
|------|------|------|
| v1 | 基础 shadcn/ui | 默认样式 |
| v2 | 极简主义 | Linear/Raycast 风格 |
| v3 | Mercury 微拟物 | 三段渐变 + 三层阴影 + Spring 动画 |

### 5.2 设计令牌

#### 颜色系统

- **主色**: Primary (蓝紫色系)
- **辅助色**: Secondary (灰色系)
- **强调色**: Accent (紫色系)
- **语义色**: Success (绿) / Destructive (红) / Warning (橙)

#### 阴影系统 (4 变体)

| 变体 | 用途 |
|------|------|
| `default` | 普通卡片 |
| `raised` | 悬浮/强调元素 |
| `inset` | 输入框/凹陷效果 |
| `outline` | 边框强调 |

#### 动画系统 (Spring 物理)

| 预设 | 参数 | 用途 |
|------|------|------|
| `snappy` | stiffness: 400, damping: 30 | 标准交互 |
| `gentle` | stiffness: 300, damping: 35 | 柔和过渡 |
| `bouncy` | stiffness: 500, damping: 25 | 弹性强调 |
| `smooth` | stiffness: 200, damping: 40 | 优雅落定 |

### 5.3 导航栏规格

- 定位: `fixed top-4 left-1/2 -translate-x-1/2`
- 效果: 玻璃拟态 (`backdrop-blur-xl`)
- 圆角: `rounded-full`
- 动画: Spring 下滑进场

---

## 六、数据库 Schema

### 6.1 核心模型

#### Resource (v2 核心表)

```sql
-- 类型与来源
type VARCHAR(20)              -- article/podcast/tweet/video
source_name VARCHAR(100)
source_logo_url TEXT

-- 原始内容
title TEXT
title_translated TEXT
url TEXT UNIQUE
content TEXT
word_count INTEGER
read_time INTEGER

-- LLM 分析结果
one_sentence_summary VARCHAR(500)
one_sentence_summary_zh VARCHAR(500)
summary TEXT
summary_zh TEXT
main_points JSONB
main_points_zh JSONB
key_quotes JSONB
key_quotes_zh JSONB

-- 分类评分
domain VARCHAR(50)
subdomain VARCHAR(50)
tags JSONB
score INTEGER                 -- 0-100
is_featured BOOLEAN           -- score >= 85

-- 媒体专用
audio_url TEXT
video_url TEXT
duration INTEGER
transcript TEXT
thumbnail_url TEXT

-- 深度研究
deep_research_report TEXT
deep_research_status VARCHAR(20)

-- 时间戳
published_at TIMESTAMP
created_at TIMESTAMP
updated_at TIMESTAMP
```

#### ResearchProject (v3 研究助手)

```sql
id UUID PRIMARY KEY
name VARCHAR(255)
description TEXT
status VARCHAR(20)            -- active/archived
created_at TIMESTAMP
updated_at TIMESTAMP
```

#### ResearchSource (v3 源材料)

```sql
id UUID PRIMARY KEY
project_id UUID REFERENCES research_projects
type VARCHAR(20)              -- url/pdf/audio/video/text
title VARCHAR(500)
content TEXT
embedding VECTOR(1536)        -- pgvector
metadata JSONB
created_at TIMESTAMP
```

### 6.2 索引策略

```sql
-- 核心查询索引
idx_resources_type
idx_resources_type_score
idx_resources_domain
idx_resources_score
idx_resources_published
idx_resources_featured
idx_resources_language
idx_resources_source_name

-- 向量索引 (pgvector)
idx_source_embedding_ivfflat
```

---

## 七、技术栈

### 7.1 后端

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.115+ |
| ORM | SQLAlchemy 2.0+ |
| 数据库 | PostgreSQL 15 + pgvector |
| 缓存 | Redis 7 |
| 任务调度 | APScheduler |
| 全文提取 | Playwright |
| 音频转写 | 通义听悟 (Tingwu) |
| 播客合成 | DashScope TTS |
| LLM | Moonshot Kimi K2 (via OpenRouter) |
| 搜索增强 | Tavily API |
| 文件存储 | Cloudflare R2 |

### 7.2 前端

| 组件 | 技术 |
|------|------|
| 框架 | Next.js 14 (App Router) |
| 样式 | TailwindCSS 3.4 |
| 组件库 | shadcn/ui 30+ 组件 |
| 动画 | Framer Motion (Spring) |
| 状态管理 | React Hooks |
| 图标 | React Icons |

### 7.3 部署

| 服务 | 平台 |
|------|------|
| 后端 | Railway |
| 前端 | Cloudflare Pages |
| 数据库 | Railway PostgreSQL |
| 缓存 | Railway Redis |
| 存储 | Cloudflare R2 |

---

## 八、开发阶段

### Phase 1: 核心功能 ✅ 已完成

- [x] 数据库基础结构
- [x] RSS 采集 + 全文提取
- [x] LLM 三步分析流程
- [x] 前端列表页 + 详情页
- [x] 基础筛选功能

### Phase 2: 功能完善 ✅ 已完成

- [x] 语言筛选 + 评分梯度
- [x] 无限滚动 + 热门来源
- [x] 播客转写 (通义听悟)
- [x] 视频采集 (元数据)
- [x] 搜索功能
- [x] RSS 输出
- [x] 用户认证
- [x] 管理后台

### Phase 3: 高级功能 ✅ 已完成

- [x] 深度研究 (Tavily + LLM)
- [x] 研究助手工作台
- [x] 播客生成 (TTS)
- [x] 概念图生成
- [x] 数据导出

### Phase 4: 优化迭代 🔄 进行中

- [x] Mercury UI 风格重构
- [x] Spring 动画系统
- [ ] Twitter 集成测试
- [ ] 视频转写集成
- [ ] 性能优化

---

## 九、验收标准

### 核心功能验收

| 功能 | 验收标准 | 状态 |
|------|----------|------|
| 内容采集 | 51 博客源正常采集，增量更新无重复 | ✅ |
| AI 分析 | 三步分析完整，评分合理 (70-95 分布) | ✅ |
| 筛选功能 | 时间/语言/分类/评分筛选正常，URL 同步 | ✅ |
| 深度研究 | 报告生成完整，搜索增强有效 | ✅ |
| 播客转写 | 通义听悟转写准确，时间戳正确 | ✅ |
| 研究助手 | 项目管理 + 源材料 + 对话功能正常 | ✅ |
| 播客生成 | TTS 合成流畅，多角色对话自然 | ✅ |

### 性能指标

| 指标 | 目标 |
|------|------|
| API 响应时间 | < 200ms (列表) / < 500ms (详情) |
| 页面加载时间 | < 2s (首屏) |
| 缓存命中率 | > 80% |
| 采集成功率 | > 95% |

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
