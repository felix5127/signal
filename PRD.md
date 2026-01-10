# 产品需求文档 (PRD): Signal Hunter v2.0

**文档属性**

* **文档版本:** V2.3 (Transcription Implementation)
* **产品代号:** Signal Hunter
* **核心定位:** 一比一复现 BestBlogs.dev 的技术内容聚合平台
* **目标用户:** 技术 KOL、独立开发者、科技博主、内容创作者
* **状态:** 开发中 (In Development)
* **更新日期:** 2026-01-03

---

## 1. 产品概述

### 1.1 目标

完全复现 [BestBlogs.dev](https://www.bestblogs.dev) 的核心功能，包括：
- 多类型内容聚合（文章、播客、推文、视频）
- AI 驱动的内容分析与评分
- 中文翻译与摘要生成
- 丰富的筛选与搜索功能
- 首页 Hero 展示与热门来源推荐

### 1.2 与 BestBlogs 的对标关系

| 功能 | BestBlogs | Signal Hunter v2.0 |
|------|-----------|-------------------|
| 文章聚合 | ✅ 170个RSS源 | ✅ 复用BestBlogs源 |
| 播客分析 | ✅ 30个RSS源 | ✅ 复用BestBlogs源 |
| 推文采集 | ✅ 160个账号 | ✅ 复用BestBlogs源 |
| 视频聚合 | ✅ 40个RSS源 | ✅ 复用BestBlogs源 |
| AI评分 | ✅ 0-100分 | ✅ 相同体系 |
| 三步分析 | ✅ 分析→反思→优化 | ✅ 相同流程 |
| 三步翻译 | ✅ 翻译→检查→意译 | ✅ 相同流程 |
| 精选标记 | ✅ | ✅ |
| 周刊功能 | ✅ | ✅ |
| RSS输出 | ✅ | ✅ |
| 开放API | ✅ | ❌ 不需要 |
| 语言筛选 | ✅ | ✅ 新增 |
| 评分梯度 | ✅ | ✅ 新增 |
| 无限滚动 | ✅ | ✅ 新增 |
| 热门来源侧边栏 | ✅ | ✅ 新增 |

---

## 2. 内容类型

### 2.1 四种内容类型

| 类型 | 数据源 | 数量 | 处理方式 |
|------|--------|------|----------|
| **文章 Articles** | BestBlogs RSS OPML | 170个源 | RSS解析 + Playwright全文提取 + LLM分析 |
| **播客 Podcasts** | BestBlogs RSS OPML | 30个源 | RSS解析 + 通义听悟转写 + LLM分析 |
| **推文 Tweets** | BestBlogs Twitter列表 | 160个账号 | XGo.ing采集 + LLM分析 |
| **视频 Videos** | BestBlogs RSS OPML | 40个源 | RSS解析 + 转写 + LLM分析 |

### 2.2 数据源文件

使用项目中 `BestBlog/` 目录下的 OPML 文件：
- `BestBlogs_RSS_Articles.opml` - 文章源
- `BestBlogs_RSS_Podcasts.opml` - 播客源
- `BestBlogs_RSS_Twitters.opml` - Twitter账号
- `BestBlogs_RSS_Videos.opml` - 视频源

---

## 3. 后端功能需求

### 3.1 数据采集模块

#### 3.1.1 RSS 采集
| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| DC-01 | OPML 解析 | 解析 BestBlogs OPML 文件，获取所有 RSS 源 | P0 |
| DC-02 | RSS 定时拉取 | APScheduler 定时拉取，每天 1-2 次 | P0 |
| DC-03 | 增量更新 | 只处理新内容，避免重复 | P0 |
| DC-04 | 源图标抓取 | 自动抓取 RSS 源的 favicon/logo | P1 |

#### 3.1.2 全文提取
| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| DC-05 | Playwright 全文提取 | 无头浏览器抓取文章正文 | P0 |
| DC-06 | Markdown 转换 | HTML 转 Markdown，保留结构 | P0 |
| DC-07 | 字数统计 | 统计文章字数，计算阅读时长 | P0 |
| DC-08 | 正文选择器 | 根据源配置提取正文区域 | P1 |

#### 3.1.3 Twitter 采集
| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| DC-09 | XGo.ing 集成 | 通过 XGo.ing 服务采集推文 | P0 |
| DC-10 | 推文解析 | 提取文本、图片、链接等 | P0 |

#### 3.1.4 播客转写
| ID | 功能 | 说明 | 优先级 | 状态 |
|----|------|------|--------|------|
| DC-11 | 通义听悟集成 | 调用通义听悟 API 转写音频 | P0 | ✅ 已实现 |
| DC-12 | 转写结果存储 | 存储文字稿，支持后续分析 | P0 | ✅ 已实现 |

**实现细节:**
- SDK: `aliyun-python-sdk-core>=2.14.0`
- API: 通义听悟离线转写 API v2
- 端点: `tingwu.cn-beijing.aliyuncs.com`
- 文件: `backend/app/processors/transcriber.py`
- 功能:
  - 提交转写任务 (PUT `/openapi/tingwu/v2/tasks`)
  - 轮询任务状态 (GET `/openapi/tingwu/v2/tasks/{task_id}`)
  - 下载转写结果 JSON
  - 支持说话人分离 (Diarization)

### 3.2 LLM 处理模块

#### 3.2.1 初评流程（规则 + LLM）
| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| LP-01 | 规则预筛 | 关键词、来源白名单等规则过滤 | P0 |
| LP-02 | LLM 初评 | 判断是否值得深入分析，输出 ignore/value/summary | P0 |
| LP-03 | 中英文分流 | 中文/英文内容使用不同 prompt | P0 |
| LP-04 | 语言识别 | 自动识别内容语言 (zh/en)，存储到 language 字段 | P0 |

**初评 Prompt 参考 BestBlogs：**
```
输出格式：
{
  "ignore": boolean,  // 是否忽略
  "reason": string,   // 判断原因（30-50字）
  "value": 0-5,       // 价值评分
  "summary": string,  // 一句话总结
  "language": string  // 语言类型 (zh/en)
}
```

#### 3.2.2 深度分析流程（三步）
| ID | 步骤 | 说明 | 优先级 |
|----|------|------|--------|
| LP-05 | 全文分析 | 生成摘要、主要观点、金句、分类、标签、评分 | P0 |
| LP-06 | 检查反思 | 审核分析结果，提出改进建议 | P0 |
| LP-07 | 优化改进 | 根据反思结果优化最终输出 | P0 |

**分析输出格式（参考 BestBlogs DSL）：**
```json
{
  "oneSentenceSummary": "一句话总结（50字内）",
  "summary": "详细摘要（200-400字）",
  "domain": "软件编程/人工智能/产品设计/商业科技",
  "aiSubcategory": "AI模型/AI开发/AI产品/AI资讯/其他",
  "tags": ["标签1", "标签2", "..."],
  "mainPoints": [
    {"point": "观点", "explanation": "解释"}
  ],
  "keyQuotes": ["金句1", "金句2"],
  "score": 85,
  "improvements": "改进建议"
}
```

#### 3.2.3 翻译流程（三步）
| ID | 步骤 | 说明 | 优先级 |
|----|------|------|--------|
| LP-08 | 初次翻译 | 英文内容翻译为中文 | P0 |
| LP-09 | 检查反思 | 检查翻译质量，识别问题 | P0 |
| LP-10 | 意译优化 | 根据反思优化翻译，更符合中文表达 | P0 |

### 3.3 评分体系

| 维度 | 分值 | 说明 |
|------|------|------|
| **总分** | 0-100 | 综合评分 |
| **内容深度** | 30分 | 技术专业度、分析严谨性、论述完整性 |
| **相关性** | 30分 | 领域契合度、时效性、受众匹配度 |
| **实用性** | 20分 | 方案可执行性、实践参考价值 |
| **创新性** | 10分 | 观点与方法创新 |
| **调整分** | -10~+5 | 加分项/减分项 |

**精选标记：** 评分 ≥ 85 自动标记为精选

**评分分级体系：**
| 评分区间 | 等级名称 | 颜色标识 | 说明 |
|----------|----------|----------|------|
| 91-100 分 | 推荐阅读 | 绿色 | 高质量必读内容 |
| 86-90 分 | 值得一读 | 蓝色 | 优质内容 |
| 75-85 分 | 基础阅读 | 灰色 | 一般性信息 |
| 0-74 分 | 暂不推荐 | - | 低质量内容 |

### 3.4 分类体系

```
├── 软件编程
│   ├── 编程语言
│   ├── 软件架构
│   ├── 开发工具
│   ├── 开源技术
│   ├── 软件工程
│   └── 云服务
├── 人工智能
│   ├── AI模型（大语言模型、理论研究、评测分析、训练优化）
│   ├── AI开发（应用开发、提示词工程、开发框架、最佳实践）
│   ├── AI产品（产品设计、智能助手、AIGC工具、产品评测）
│   └── AI资讯（行业动态、企业新闻、专家观点、投融资）
├── 产品设计
│   ├── 产品策略
│   ├── 用户体验
│   ├── 产品运营
│   └── 市场分析
└── 商业科技
    ├── 技术创业
    ├── 商业模式
    ├── 个人成长
    └── 领导力
```

### 3.5 数据存储

#### 3.5.1 主表结构（resources）

```sql
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,

    -- 类型与来源
    type VARCHAR(20) NOT NULL,           -- article/podcast/tweet/video
    source_name VARCHAR(100) NOT NULL,   -- RSS源名称
    source_url TEXT,                      -- RSS源URL
    source_logo_url TEXT,                 -- RSS源Logo URL (新增)
    url TEXT NOT NULL UNIQUE,            -- 原文链接
    url_hash VARCHAR(64) NOT NULL,       -- URL哈希，去重用

    -- 原始内容
    title TEXT NOT NULL,
    title_translated TEXT,               -- 翻译后标题
    author VARCHAR(255),
    content_markdown TEXT,               -- Markdown全文
    content_html TEXT,                   -- 原始HTML
    word_count INTEGER,                  -- 字数统计
    read_time INTEGER,                   -- 阅读时长（分钟）

    -- LLM分析结果
    one_sentence_summary VARCHAR(500),   -- 一句话总结
    one_sentence_summary_zh VARCHAR(500),-- 中文一句话总结
    summary TEXT,                        -- 详细摘要
    summary_zh TEXT,                     -- 中文摘要
    main_points JSONB,                   -- 主要观点
    main_points_zh JSONB,                -- 中文主要观点
    key_quotes JSONB,                    -- 金句
    key_quotes_zh JSONB,                 -- 中文金句

    -- 分类与标签
    domain VARCHAR(50),                  -- 一级分类
    subdomain VARCHAR(50),               -- 二级分类（AI专用）
    tags JSONB,                          -- 标签数组

    -- 评分
    score INTEGER DEFAULT 0,             -- 0-100综合评分
    is_featured BOOLEAN DEFAULT FALSE,   -- 是否精选（score>=85）

    -- 状态
    language VARCHAR(10),                -- zh/en (新增索引)
    status VARCHAR(20) DEFAULT 'pending',-- pending/analyzing/published/failed

    -- 播客专用
    audio_url TEXT,
    duration INTEGER,                    -- 音频时长（秒）
    transcript TEXT,                     -- 转写文本

    -- 时间戳
    published_at TIMESTAMP,              -- 原文发布时间
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    analyzed_at TIMESTAMP,

    -- 元数据
    metadata JSONB                       -- 其他元数据
);

-- 索引
CREATE INDEX idx_resources_type ON resources(type);
CREATE INDEX idx_resources_type_score ON resources(type, score DESC);
CREATE INDEX idx_resources_domain ON resources(domain);
CREATE INDEX idx_resources_score ON resources(score DESC);
CREATE INDEX idx_resources_published ON resources(published_at DESC);
CREATE INDEX idx_resources_featured ON resources(is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_resources_language ON resources(language);  -- 新增
CREATE INDEX idx_resources_source_name ON resources(source_name);  -- 新增（侧边栏用）
```

#### 3.5.2 周刊表

```sql
CREATE TABLE newsletters (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    week_number INTEGER NOT NULL,        -- 第几周
    year INTEGER NOT NULL,
    content TEXT,                        -- Markdown内容
    resource_ids JSONB,                  -- 包含的资源ID
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.6 API 筛选参数完整规格

#### 3.6.1 URL 参数对照表

| 参数名 | 类型 | 说明 | 可选值 | 默认值 |
|--------|------|------|--------|--------|
| `type` | string | 内容类型 | article, podcast, tweet, video | all |
| `time` | string | 时间范围 | all, 1d, 3d, 1w, 1m, 3m, 1y | 1w |
| `lang` | string | 语言筛选 | zh, en, all | all |
| `domain` | string | 分类筛选 | programming, ai, product, business | all |
| `sort` | string | 排序方式 | default, time, score | default |
| `q` | string | 搜索关键词 | 任意字符串 | - |
| `sourceid` | string | 指定源ID | 源ID (UUID) | - |
| `qualified` | boolean | 仅精选 | true, false | false |
| `score` | number | 最低评分 | 91, 86, 75 | - |

#### 3.6.2 筛选逻辑说明

**时间筛选 (`time`)**
```
all  → 无限制
1d   → published_at >= NOW() - INTERVAL '1 day'
3d   → published_at >= NOW() - INTERVAL '3 days'
1w   → published_at >= NOW() - INTERVAL '1 week'
1m   → published_at >= NOW() - INTERVAL '1 month'
3m   → published_at >= NOW() - INTERVAL '3 months'
1y   → published_at >= NOW() - INTERVAL '1 year'
```

**语言筛选 (`lang`)**
```
all  → 无限制
zh   → language = 'zh'
en   → language = 'en'
```

**评分筛选 (`score`)**
```
91   → score >= 91 (推荐阅读)
86   → score >= 86 (值得读 + 推荐)
75   → score >= 75 (基础读以上)
```

**排序 (`sort`)**
```
default → 按综合权重排序（分数 + 时间衰减）
time    → published_at DESC
score   → score DESC
```

### 3.7 热门来源 API

#### 3.7.1 接口规格

```
GET /api/sources/popular

Query Parameters:
  - type: 内容类型 (可选)
  - domain: 分类 (可选)
  - limit: 返回数量 (默认 10)

Response:
{
  "items": [
    {
      "source_name": "机器之心",
      "source_logo_url": "https://...",
      "article_count": 125,
      "type": "article"
    },
    ...
  ]
}
```

#### 3.7.2 实现逻辑

```python
# 按当前筛选条件统计各源文章数
def get_popular_sources(type: str = None, domain: str = None, limit: int = 10):
    query = db.query(
        Resource.source_name,
        Resource.source_logo_url,
        func.count(Resource.id).label('article_count')
    )

    # 应用筛选条件
    if type:
        query = query.filter(Resource.type == type)
    if domain:
        query = query.filter(Resource.domain == domain)

    # 分组统计
    query = query.group_by(Resource.source_name, Resource.source_logo_url)
    query = query.order_by(desc('article_count'))
    query = query.limit(limit)

    return query.all()
```

### 3.8 RSS 输出

| RSS 类型 | URL 格式 | 说明 |
|----------|----------|------|
| 全站 | `/feeds/rss` | 所有内容 |
| 按类型 | `/feeds/rss?type=article` | 文章/播客/推文/视频 |
| 按分类 | `/feeds/rss?domain=ai` | 按一级分类 |
| 按语言 | `/feeds/rss?lang=zh` | 仅中文内容 |
| 精选 | `/feeds/rss?featured=true` | 仅精选内容 |
| 高分 | `/feeds/rss?score=91` | 91分以上 |
| 时间 | `/feeds/rss?time=1w` | 最近一周 |

### 3.9 周刊功能

| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| NL-01 | 自动生成 | 每周五自动生成本周精选 | P1 |
| NL-02 | 内容筛选 | 选取本周 Top 内容 | P1 |
| NL-03 | 格式输出 | 生成 Markdown 格式周刊 | P1 |

---

## 4. 前端功能需求

### 4.1 页面结构

```
├── 首页 /
│   ├── Hero Section (新增)
│   │   ├── 价值主张标题
│   │   ├── 「浏览本周精选」CTA
│   │   └── 可信来源 Logo 展示
│   ├── Tab导航：文章 | 播客 | 推文 | 视频
│   ├── 筛选栏
│   ├── 热门来源侧边栏 (新增)
│   └── 内容列表（卡片网格 + 无限滚动）
├── 详情页 /resources/:id
│   ├── 完整摘要
│   ├── 主要观点
│   ├── 金句
│   └── 原文链接
├── 周刊页 /newsletters
│   └── 周刊列表与详情
└── RSS页 /feeds
    └── RSS订阅说明
```

### 4.2 首页 Hero Section（新增）

#### 4.2.1 设计规格

```
┌─────────────────────────────────────────────────────────────────┐
│                    Signal Hunter                                │
│                技术情报聚合，AI 驱动筛选                          │
│                                                                         │
│  从 400+ 优质源中，每日精选最值得阅读的技术内容                     │
│                                                                         │
│  [浏览本周精选]           [了解工作原理]                             │
│                                                                         │
│  可信来源:                                                               │
│  [OpenAI] [DeepMind] [Anthropic] [Hugging Face] ...                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 技术实现

| 元素 | 实现方式 |
|------|----------|
| **来源 Logo** | 从配置文件读取，展示知名来源图标 |
| **CTA 按钮** | 跳转带筛选参数的首页，如 `/?time=1w&score=86` |
| **统计数据** | 调用 `/api/stats` 获取总数、源数量等 |

### 4.3 筛选栏功能

#### 4.3.1 常规筛选（一级入口）

| 筛选项 | 选项列表 | 默认值 | URL 参数 | 优先级 |
|--------|----------|--------|----------|--------|
| 时间范围 | 全部/1天/3天/1周/1月/3月/1年 | 1周 | `time` | P0 |
| 语言 | 不限/中文/英文 | 不限 | `lang` | P1 |
| 分类 | 全部/编程/AI/产品/商业 | 全部 | `domain` | P0 |
| 排序 | 默认/时间/评分 | 默认 | `sort` | P0 |
| 评分梯度 | 全部/91+/86+/75+ | 全部 | `score` | P1 |

#### 4.3.2 高级筛选

| 筛选项 | 说明 | URL 参数 | 优先级 |
|--------|------|----------|--------|
| 关键词搜索 | 全文搜索标题和摘要 | `q` | P0 |
| 指定源筛选 | 筛选特定媒体/博主 | `sourceid` | P1 |
| 精选内容 | 仅显示精选内容 | `qualified=true` | P0 |

#### 4.3.3 筛选交互规格

| 功能 | 说明 |
|------|------|
| **实时筛选** | 选择筛选条件后立即刷新列表 |
| **URL 同步** | 筛选条件同步到 URL，支持分享 |
| **无限滚动** | 滚动到底部自动加载更多 (替代分页) |

### 4.4 热门来源侧边栏（新增）

#### 4.4.1 设计规格

```
┌─────────────────────────┐
│ 热门来源                 │
├─────────────────────────┤
│ [图标] 机器之心   (45) │
│ [图标] 宝玉分享    (32) │
│ [图标] Founder Park (28)│
│ [图标] Indie Hackers (25)│
│ ...                     │
└─────────────────────────┘
```

#### 4.4.2 技术实现

```typescript
// 组件:热门来源侧边栏
// 路径: frontend/components/popular-sources.tsx

interface PopularSource {
  source_name: string;
  source_logo_url: string;
  article_count: number;
}

interface PopularSourcesProps {
  type?: string;      // 当前选中的类型
  domain?: string;    // 当前选中的分类
  limit?: number;     // 显示数量
  onSelect?: (sourceName: string) => void;  // 点击回调
}

// API 调用
const fetchPopularSources = async (params: {
  type?: string;
  domain?: string;
  limit?: number;
}): Promise<PopularSources[]> => {
  const res = await fetch(`/api/sources/popular?${new URLSearchParams(params)}`);
  return res.json();
};
```

### 4.5 卡片组件增强

#### 4.5.1 卡片元素新增

| 元素 | 说明 | 数据来源 | 优先级 |
|------|------|----------|--------|
| **来源图标** | 显示源 Logo/Favicon | `source_logo_url` | P1 |
| **字数 & 阅读时间** | "5014字 · 约21分钟" | `word_count`, `read_time` | P1 |
| **评分徽章颜色** | 91+绿色/86-90蓝色/75-85灰色 | `score` | P1 |

#### 4.5.2 卡片布局

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

### 4.6 无限滚动（新增）

#### 4.6.1 实现方案

使用 React Intersection Observer API 实现滚动检测：

```typescript
// 组件:无限滚动触发器
// 路径: frontend/components/infinite-scroll.tsx

import { useEffect, useRef } from 'react';

interface InfiniteScrollProps {
  hasMore: boolean;          // 是否还有更多数据
  isLoading: boolean;        // 是否正在加载
  onLoadMore: () => void;   // 加载更多回调
  threshold?: number;       // 触发阈值（像素）
}

export function InfiniteScroll({
  hasMore,
  isLoading,
  onLoadMore,
  threshold = 200
}: InfiniteScrollProps) {
  const observerTarget = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          onLoadMore();
        }
      },
      { rootMargin: `${threshold}px` }
    );

    const current = observerTarget.current;
    if (current) {
      observer.observe(current);
    }

    return () => {
      if (current) {
        observer.unobserve(current);
      }
    };
  }, [hasMore, isLoading, onLoadMore, threshold]);

  return <div ref={observerTarget} />;
}
```

#### 4.6.2 集成到列表页

```typescript
// 列表页使用无限滚动
const [page, setPage] = useState(1);
const [resources, setResources] = useState<Resource[]>([]);
const [hasMore, setHasMore] = useState(true);
const [isLoading, setIsLoading] = useState(false);

const loadMore = async () => {
  if (isLoading || !hasMore) return;

  setIsLoading(true);
  const newItems = await fetchResources(page + 1);

  setResources(prev => [...prev, ...newItems.items]);
  setHasMore(newItems.items.length >= PAGE_SIZE);
  setPage(p => p + 1);
  setIsLoading(false);
};

// 在列表底部放置触发器
return (
  <>
    {resources.map(r => <ResourceCard key={r.id} resource={r} />)}
    <InfiniteScroll
      hasMore={hasMore}
      isLoading={isLoading}
      onLoadMore={loadMore}
    />
  </>
);
```

### 4.7 详情页功能

| ID | 功能 | 说明 | 优先级 |
|----|------|------|--------|
| FE-01 | 元信息 | 来源、作者、发布时间、字数、阅读时长 | P0 |
| FE-02 | 评分展示 | 0-100分 + 精选标记 + 颜色分级 | P0 |
| FE-03 | 一句话总结 | 醒目展示 | P0 |
| FE-04 | 详细摘要 | 可展开/收起 | P0 |
| FE-05 | 主要观点 | 列表展示 | P0 |
| FE-06 | 金句 | 引用样式展示 | P0 |
| FE-07 | 原文链接 | 跳转原文 | P0 |
| FE-08 | 标签 | 可点击跳转 | P1 |

### 4.8 UI 设计要求

| 要求 | 说明 |
|------|------|
| **风格** | 克隆 BestBlogs UI 风格 |
| **响应式** | 适配桌面端和移动端 |
| **主题** | 支持亮色/暗色模式 |
| **语言** | 纯中文界面 |

### 4.9 前端 UI 设计规范 - 极简主义重构（2026-01-03 更新）

#### 4.9.1 设计目标

打造一个**紧凑、干净、居中对齐**的现代 SaaS 工具界面，参考 Linear / Raycast / Vercel 的极简主义风格。

#### 4.9.2 统一头部导航栏设计规范

**设计原则**
- 紧凑高度：`h-16` (64px)
- 居中对齐：Logo 左侧，Tabs 居中，操作右侧
- 减法设计：去掉副标题，缩小 Logo，去除过度装饰

**布局结构**

```
┌────────────────────────────────────────────────────────────┐
│ [Logo]          [文章 播客 推文 视频]        [主题切换]     │
└────────────────────────────────────────────────────────────┘
   Left              Center                    Right
```

**组件规格**

| 元素 | 尺寸 | 样式 | 说明 |
|------|------|------|------|
| **Logo 容器** | `w-8 h-8` (32x32px) | `rounded-lg` + 渐变背景 | 缩小以减少视觉重量 |
| **Logo 图标** | `w-5 h-5` (20x20px) | 白色闪电 SVG | 保持清晰度 |
| **品牌标题** | `text-lg` | `font-semibold text-slate-800` | 去掉渐变效果 |
| **导航胶囊** | 自适应高度 | `rounded-full bg-[#0B1E22]` | AngelList 风格 |
| **主题按钮** | `h-9 w-9` | `variant="ghost"` | 标准尺寸 |

**Tabs 导航规格**

| 属性 | 桌面端 | 移动端 |
|------|--------|--------|
| 显示方式 | `hidden md:flex` | `md:hidden` |
| Padding | `px-8 py-2.5` | `px-6 py-2` |
| 选项间距 | `gap-8` | `gap-6` |
| 字体大小 | `text-sm` | `text-xs` |
| 图标间距 | `gap-2` | `gap-1.5` |

**头部容器样式**

```tsx
<header className="sticky top-0 z-50 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80">
```

| 属性 | 值 | 说明 |
|------|-----|------|
| 高度 | `h-16` | 固定 64px 高度 |
| 背景 | `bg-white/80 backdrop-blur-md` | 半透明毛玻璃效果 |
| 边框 | `border-b border-slate-200` | 细边框分隔 |
| 定位 | `sticky top-0` | 滚动时吸顶 |

#### 4.9.3 搜索区域设计规范

**设计目标**
- 居中对齐，最大宽度 `max-w-2xl`
- 增强阴影效果：`shadow-xl shadow-slate-200/60`
- 圆角加大：`rounded-2xl`
- 高度：`h-14`
- 占位符文字居中

**搜索框规格**

| 属性 | 值 | 说明 |
|------|-----|------|
| 最大宽度 | `max-w-2xl` (672px) | 限制宽度以保持紧凑 |
| 高度 | `h-14` (56px) | 舒适的点击区域 |
| 圆角 | `rounded-2xl` | 16px 圆角 |
| 阴影 | `shadow-xl shadow-slate-200/60` | 增强视觉层次 |
| 间距 | 距离 Header 约 40px | `gap-6` (24px) + `py-6` (24px) |

**搜索框集成方式**

```tsx
<div className="flex justify-center">
  <SearchBox
    value={filters.searchKeyword}
    onSearch={onSearch}
    loading={searchLoading}
    placeholder="搜索标题、摘要、标签..."
    className="max-w-2xl w-full shadow-xl shadow-slate-200/60 dark:shadow-none"
  />
</div>
```

#### 4.9.4 工具栏式筛选器设计规范

**设计目标**
- 将原有的平铺标签组改为**下拉菜单按钮**
- 单行水平布局，居中对齐
- 激活状态使用紫色高亮
- 减少视觉噪音，提升可用性

**工具栏布局**

```
┌─────────────────────────────────────────────────────────────┐
│  [🕒 时间: 全部 ▾] [🏷️ 分类: 全部 ▾] [🌐 语言: 全部 ▾] ...   │
└─────────────────────────────────────────────────────────────┘
```

**下拉菜单按钮规格**

| 属性 | 默认状态 | 激活状态 |
|------|----------|----------|
| 背景 | `transparent` | `bg-violet-50 dark:bg-violet-900/30` |
| 文字颜色 | `text-slate-600 dark:text-slate-400` | `text-violet-700 dark:text-violet-300` |
| Padding | `px-4 py-2` | 相同 |
| 圆角 | `rounded-lg` | 相同 |
| 字体大小 | `text-sm` | `font-medium` |
| Hover | `hover:bg-slate-100 dark:hover:bg-slate-800` | 相同 |

**按钮元素结构**

```tsx
<button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm">
  <span className="text-base">{icon}</span>
  <span>{label}:</span>
  <span className="font-medium">{selectedValue}</span>
  <svg className="w-4 h-4">▼</svg>
</button>
```

**下拉菜单规格**

| 属性 | 值 | 说明 |
|------|-----|------|
| 背景 | `bg-white dark:bg-slate-900` | 与页面背景一致 |
| 边框 | `border border-slate-200 dark:border-slate-700` | 细边框 |
| 圆角 | `rounded-lg` | 8px |
| 阴影 | `shadow-xl` | 强阴影增强层次 |
| 最小宽度 | `min-w-[200px]` | 确保内容显示完整 |
| 选项 Padding | `px-4 py-2` | 舒适的点击区域 |
| 选项 Hover | `hover:bg-slate-50 dark:hover:bg-slate-800` | 轻微背景变化 |

**筛选器选项列表**

| 筛选类型 | 图标 | 选项 |
|----------|------|------|
| 时间 | 🕒 | 全部时间、1天、1周、1月、3月、1年 |
| 分类 | 🏷️ | 全部分类、软件编程、人工智能、产品设计、商业科技 |
| 语言 | 🌐 | 全部语言、仅中文、仅英文 |
| 评分 | ⭐ | 全部评分、9.0+ 推荐、8.5+ 值得读、7.5+ 基础 |
| 排序 | 🔀 | 默认排序、最新时间、最高评分 |
| 精选 | ⭐ | 开关按钮（非下拉） |

**工具栏布局规格**

| 属性 | 值 | 说明 |
|------|-----|------|
| 容器 | `flex items-center justify-center gap-2` | 居中水平布局 |
| 换行 | `flex-wrap` | 小屏自动换行 |
| 距离搜索框 | `gap-6` (24px) | 保持视觉分离 |

**状态指示器**

当来源筛选激活时，显示可清除的状态标签：

```tsx
<div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/30 rounded-lg">
  <span className="text-sm text-green-600 dark:text-green-400">
    来源: {filters.sourceFilter}
  </span>
  <button onClick={clearSource} className="text-green-400 hover:text-green-600">
    <svg>✕</svg>
  </button>
</div>
```

#### 4.9.5 视觉层级原则

**对齐（Alignment）**
- 所有核心元素严格居中（搜索框、工具栏）
- 保持一致的左右边距（`max-w-7xl mx-auto px-4`）
- 头部元素左-中-右三段式对齐

**间距（Spacing）**
- Header ↔ 搜索区：40px（`py-6` + `gap-6`）
- 搜索框 ↔ 工具栏：24px（`gap-6`）
- 工具栏 ↔ 内容区：32px（`mb-8`）
- 工具栏按钮间距：8px（`gap-2`）

**层级（Hierarchy）**
1. **Primary**: 搜索框（最大、最醒目）
2. **Secondary**: 工具栏筛选器（功能性）
3. **Tertiary**: 内容列表（结果展示）

**减法设计（Reduction）**
- 去除副标题（"技术情报聚合"）
- 缩小 Logo 尺寸（40x32px）
- 移除过度装饰（渐变标题 → 纯色）
- 隐藏筛选选项（平铺 → 下拉菜单）

#### 4.9.6 响应式适配

**桌面端（>= 768px）**
- Header: 三段式布局（Logo + Tabs + 主题）
- Tabs: 完整显示，字体 `text-sm`
- 工具栏: 水平排列，自动换行

**移动端（< 768px）**
- Header: Logo + 主题在第一行，Tabs 在第二行
- Tabs: 缩小字体 `text-xs`，间距 `gap-6`
- 工具栏: 保持水平布局，支持换行

**组件路径**

| 组件 | 路径 | 说明 |
|------|------|------|
| 紧凑工具栏 | `/components/compact-filter-toolbar.tsx` | 新增，工具栏式筛选器 |
| 搜索框 | `/components/search-box.tsx` | 复用，通过 className 增强样式 |
| 首页 | `/app/page.tsx` | 重构头部和筛选器集成 |

#### 4.9.7 实现示例

**头部导航完整代码**

```tsx
<header className="sticky top-0 z-50 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full">
    <div className="flex items-center justify-between h-full">
      {/* Left: Logo + 标题 */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h1 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
          Signal Hunter
        </h1>
      </div>

      {/* Center: Tabs 导航 */}
      <nav className="hidden md:flex items-center gap-8 px-8 py-2.5 rounded-full shadow-md" style={{ backgroundColor: '#0B1E22' }}>
        {TABS.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}>
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      {/* Right: 主题切换 */}
      <Button variant="ghost" size="icon" onClick={toggleTheme} className="h-9 w-9">
        {resolvedTheme === 'dark' ? <Sun /> : <Moon />}
      </Button>
    </div>
  </div>
</header>
```

**工具栏筛选器集成**

```tsx
<main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
  <div className="flex gap-6">
    <div className="flex-1 min-w-0">
      {/* 紧凑工具栏式筛选器 */}
      <div className="mb-8">
        <CompactFilterToolbar
          filters={filters}
          onFiltersChange={setFilters}
          onSearch={handleSearch}
          searchLoading={searchLoading}
        />
      </div>

      {/* 内容列表 */}
      {/* ... */}
    </div>

    {/* 右侧侧边栏 */}
    <div className="hidden lg:block w-72 flex-shrink-0">
      <HotSourcesSidebar />
    </div>
  </div>
</main>
```

#### 4.9.8 悬浮胶囊导航栏（旧版规范，仅供参考）

**注意**: 以下规范为 2026-01-02 版本，已被上述极简主义重构取代。保留此章节仅供参考。

**容器样式**

| 属性 | 值 | 说明 |
|------|-----|------|
| 背景色 | `#0B1E22` | 深蓝绿色，与页面背景形成对比 |
| 形状 | `rounded-full` | 全圆角胶囊形 |
| Padding | `px-8 py-3` | 水平32px，垂直12px |
| 高度 | 约 48-52px | 根据内容自适应 |
| Shadow | `shadow-lg` | 轻微阴影，营造悬浮感 |

**Tabs 选项样式**

| 状态 | 文字颜色 | 字重 | 图标滤镜 | 说明 |
|------|----------|------|----------|------|
| 默认 | `#8FAEB6` | `font-normal` | `grayscale(100%) opacity(0.85)` | 带青调的灰色，去色图标 |
| 选中 | `#FFFFFF` | `font-semibold` | `none` | 纯白色，恢复图标色彩 |
| Hover | `#D1D5DB` | `font-normal` | `grayscale(100%) opacity(0.85)` | 亮灰色 |

---

#### 4.9.9 VisionOS 浮动玻璃岛设计（2026-01-03 更新）

**设计目标**

打造 **Apple VisionOS** 风格的浮动玻璃岛 UI，参考 iOS / visionOS 的毛玻璃材质和悬浮效果。

**Header 浮动玻璃岛规格**

| 属性 | 值 | 说明 |
|------|-----|------|
| 定位 | `fixed top-4 left-1/2 -translate-x-1/2` | 居中浮动，顶部间距 16px |
| 最大宽度 | `max-w-4xl` | 限制最大宽度 |
| 高度 | 自适应 | `py-3` (12px 上下内边距) |
| 圆角 | `rounded-full` | 完整胶囊形状 |
| 毛玻璃材质 | `bg-white/70 backdrop-blur-2xl backdrop-saturate-150` | True Optical Glass 配方 |
| 阴影 | `shadow-[0_8px_30px_rgba(0,0,0,0.08)]` | 柔和扩散阴影 |
| 边框 | **无** | 移除所有 border 和 ring |

**True VisionOS 光学玻璃配方**

```tsx
// 核心玻璃材质
bg-white/70              // 70% 透明度白色
backdrop-blur-2xl         // 超强模糊 (40px+)
backdrop-saturate-150     // 提高背景饱和度
shadow-[0_8px_30px_rgba(0,0,0,0.08)]  // 柔和深度阴影
// 注意：移除 border 和 ring，纯靠阴影悬浮
```

**Tab 导航样式**

| 状态 | 背景色 | 文字颜色 | 说明 |
|------|--------|----------|------|
| 激活 | `bg-white/90 backdrop-blur-sm` | `text-slate-900 font-semibold` | 高对比度 |
| 非激活 | `text-slate-600 hover:bg-white/60 hover:text-slate-900` | - | 柔和交互 |

**背景层次结构**

```
z-20: FlickeringGrid（最底层，闪烁网格）
z-10: Aurora 渐变光球（紫/蓝/粉色）
z-50: Header（浮动玻璃岛）
z-50: 搜索栏（毛玻璃输入框）
z-10: 内容列表
```

**搜索栏毛玻璃规格**

| 属性 | 值 | 说明 |
|------|-----|------|
| 高度 | `h-14` (56px) | 舒适点击区域 |
| 圆角 | `rounded-2xl` | 16px 大圆角 |
| 背景 | `bg-white/70 backdrop-blur-2xl backdrop-saturate-150` | 与 Header 一致 |
| 边框 | **无** | 纯玻璃效果 |
| 阴影 | `shadow-2xl shadow-black/5` | 深度阴影 |

**筛选按钮激活态**

| 属性 | 值 | 说明 |
|------|-----|------|
| 背景 | `bg-white/50 backdrop-blur-md ring-1 ring-black/5` | 轻量毛玻璃 |
| 内阴影 | `shadow-[inset_0_0_0_1px_rgba(255,255,255,0.5)]` | 高光边沿 |
| 文字 | `text-purple-700` | 品牌紫色 |

**Aurora 渐变背景层**

```tsx
// 固定在顶部，高度 600px
<div className="fixed top-0 left-0 right-0 h-[600px] -z-10">
  {/* Blob 1: Top Left - Purple */}
  <div className="absolute top-[-10%] left-[-5%] w-[500px] h-[500px]
    bg-purple-400/25 rounded-full mix-blend-multiply filter blur-[100px] opacity-70" />
  {/* Blob 2: Top Right - Blue */}
  <div className="absolute top-[-5%] right-[-5%] w-[500px] h-[500px]
    bg-blue-400/25 rounded-full mix-blend-multiply filter blur-[100px] opacity-70" />
  {/* Blob 3: Center Top - Pink */}
  <div className="absolute top-[-15%] left-[30%] w-[600px] h-[600px]
    bg-pink-400/20 rounded-full mix-blend-multiply filter blur-[120px] opacity-60" />
</div>
```

**FlickeringGrid 闪烁网格背景**

| 属性 | 值 | 说明 |
|------|-----|------|
| 方块大小 | `squareSize=2` | 微小点阵 |
| 网格间距 | `gridGap=20` | 稀疏分布 |
| 颜色 | `#6B21A8` (Brand Purple) | 品牌紫色 |
| 最大透明度 | `maxOpacity=0.15` | 极淡效果 |
| 闪烁概率 | `flickerChance=0.1` | 缓慢闪烁 |
| 容器 | `fixed inset-0 -z-20` | 全屏覆盖，最底层 |

**页面底色**

| 区域 | 底色 | 说明 |
|------|------|------|
| 首页 | `bg-white` | 纯白色 |
| 详情页 | `bg-white` | 纯白色 |

**推文卡片修复**

| 修复项 | 说明 |
|--------|------|
| HTML 渲染 | 新增 `extractTextFromHtml()` 函数，移除 HTML 标签和转义字符 |
| 作者信息 | 从 URL 提取用户名（如 `shao__meng` → `Shao Meng`） |
| 真实头像 | 使用 `unavatar.io/twitter/:username` 获取 Twitter 头像 |
| 头像失败回退 | 头像加载失败时显示默认的 X Logo 渐变背景 |

**组件文件路径**

| 组件 | 路径 | 说明 |
|------|------|------|
| FlickeringGrid | `/components/effects/flickering-grid.tsx` | 新增 |
| TweetCard | `/components/tweet-card.tsx` | 更新 |
| 首页 | `/app/page.tsx` | VisionOS 风格重构 |
| 详情页 | `/components/resource-detail.tsx` | 背景更新 |

---

## 5. 技术实现方案

### 5.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Next.js 14 (App Router) | SSR + CSR 混合 |
| **UI组件** | Tailwind CSS + shadcn/ui | 现代化组件库 |
| **无限滚动** | Intersection Observer API | 原生 API |
| **后端框架** | FastAPI + Pydantic v2 | 异步、类型安全 |
| **数据库** | PostgreSQL | 支持 JSONB、全文检索 |
| **全文提取** | Playwright | Python 无头浏览器 |
| **播客转写** | 通义听悟 | 阿里云服务 |
| **Twitter采集** | XGo.ing | 第三方服务 |
| **LLM** | OpenRouter (google/gemini-3-flash-preview) | Gemini Flash 3.0 |
| **任务调度** | APScheduler | 轻量级调度器 |
| **部署-后端** | Railway | 云端部署 |
| **部署-前端** | Vercel | 云端部署 |
| **本地开发** | Docker Compose | 本地环境 |

### 5.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Signal Hunter v2.0                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │                    数据采集层 (Data Collection)                 │    │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │    │
│   │  │RSS解析  │ │Playwright│ │ XGo.ing │ │通义听悟 │             │    │
│   │  │(文章)   │ │(全文提取)│ │(Twitter)│ │(播客)   │             │    │
│   │  │         │ │+字数统计│ │         │ │         │             │    │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                    ↓                                    │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │                    LLM处理层 (Intelligence)                     │    │
│   │                                                                │    │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │    │
│   │   │  规则预筛    │───→│  LLM初评    │───→│  深度分析   │       │    │
│   │   │             │    │+语言识别    │    │ (三步流程)  │       │    │
│   │   └─────────────┘    └─────────────┘    └─────────────┘       │    │
│   │                                                 ↓              │    │
│   │                                          ┌─────────────┐       │    │
│   │                                          │  翻译流程   │       │    │
│   │                                          │ (三步流程)  │       │    │
│   │                                          └─────────────┘       │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                    ↓                                    │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │                    存储层 (Storage)                            │    │
│   │   ┌─────────────┐    ┌─────────────┐                          │    │
│   │   │ PostgreSQL  │    │  RSS生成    │                          │    │
│   │   │ (+新索引)   │    │ (feeds)     │                          │    │
│   │   └─────────────┘    └─────────────┘                          │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                    ↓                                    │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │                    交付层 (Delivery)                           │    │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │    │
│   │   │  Web前端    │    │  RSS输出    │    │   周刊      │       │    │
│   │   │+无限滚动    │    │  (多种)     │    │  (每周五)   │       │    │
│   │   │+侧边栏      │    │             │    │             │       │    │
│   │   └─────────────┘    └─────────────┘    └─────────────┘       │    │
│   └───────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 API 端点完整清单

| 方法 | 路径 | 说明 | 新增 |
|------|------|------|------|
| GET | `/api/resources` | 资源列表（支持所有筛选参数） | - |
| GET | `/api/resources/:id` | 资源详情 | - |
| GET | `/api/search` | 全文搜索 | - |
| GET | `/api/sources/popular` | 热门来源统计 | ✅ |
| GET | `/api/stats` | 全局统计 | - |
| GET | `/api/feeds/rss` | RSS 输出 | - |
| POST | `/api/trigger-pipeline` | 手动触发文章采集 | - |
| POST | `/api/trigger-twitter` | 手动触发Twitter采集 | - |
| POST | `/api/trigger-podcast` | 手动触发播客采集+转写 | ✅ |
| POST | `/api/trigger-video` | 手动触发视频采集 | ✅ |

### 5.4 筛选参数后端实现

```python
# 路径: backend/app/api/resources.py

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal

@router.get("/resources", response_model=ResourceListResponse)
async def list_resources(
    db: Session = Depends(get_db),
    # 类型筛选
    type: Optional[Literal["article", "podcast", "tweet", "video"]] = Query(None),
    # 时间筛选
    time: Optional[str] = Query(None),  # all, 1d, 3d, 1w, 1m, 3m, 1y
    # 语言筛选
    lang: Optional[Literal["zh", "en", "all"]] = Query(None),
    # 分类筛选
    domain: Optional[str] = Query(None),
    # 排序
    sort: Optional[Literal["default", "time", "score"]] = Query("default"),
    # 搜索
    q: Optional[str] = Query(None),
    # 指定源筛选
    sourceid: Optional[str] = Query(None),
    # 精选筛选
    qualified: Optional[bool] = Query(None),
    # 评分筛选
    score: Optional[int] = Query(None),
    # 分页（无限滚动使用）
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    资源列表接口，支持多维度筛选

    ## 筛选参数说明

    ### 常规筛选
    - **type**: 内容类型 (article, podcast, tweet, video)
    - **time**: 时间范围 (all, 1d, 3d, 1w, 1m, 3m, 1y)
    - **lang**: 语言 (zh, en, all)
    - **domain**: 分类 (programming, ai, product, business)
    - **sort**: 排序 (default, time, score)

    ### 高级筛选
    - **q**: 搜索关键词（全文搜索标题和摘要）
    - **sourceid**: 指定源ID
    - **qualified**: 仅精选内容
    - **score**: 最低评分 (91, 86, 75)
    """

    # 构建查询
    query = db.query(Resource)

    # 类型筛选
    if type:
        query = query.filter(Resource.type == type)

    # 语言筛选
    if lang and lang != "all":
        query = query.filter(Resource.language == lang)

    # 分类筛选
    if domain:
        query = query.filter(Resource.domain == domain)

    # 精选筛选
    if qualified:
        query = query.filter(Resource.is_featured == True)

    # 评分筛选
    if score:
        query = query.filter(Resource.score >= score)

    # 指定源筛选
    if sourceid:
        query = query.filter(Resource.source_name == sourceid)

    # 时间筛选
    if time and time != "all":
        time_delta = get_time_delta(time)  # 实现 time -> timedelta 转换
        query = query.filter(Resource.published_at >= time_delta)

    # 搜索（全文）
    if q:
        query = query.filter(
            (Resource.title.ilike(f"%{q}%")) |
            (Resource.one_sentence_summary.ilike(f"%{q}%")) |
            (Resource.summary.ilike(f"%{q}%"))
        )

    # 排序
    if sort == "time":
        query = query.order_by(Resource.published_at.desc())
    elif sort == "score":
        query = query.order_by(Resource.score.desc())
    else:  # default
        query = query.order_by(
            Resource.score.desc(),
            Resource.published_at.desc()
        )

    # 分页
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(items) < total
    }
```

---

## 6. 代码迭代策略

### 6.1 模块处理方式

| 模块 | 策略 | 说明 |
|------|------|------|
| **Scraper 架构** | ✅ 保留 | 基础架构好，增加全文提取能力 |
| **配置系统** | ✅ 保留 | 现有 config.py 够用 |
| **LLM 调用** | ✅ 保留 | 现有 llm.py 够用 |
| **LLM 处理流程** | 🔄 重写 | 参考 BestBlogs DSL 实现三步流程 |
| **数据库模型** | 🔄 更新 | 添加新字段和索引 |
| **前端 UI** | 🔄 更新 | 增加新组件和筛选功能 |
| **RSS 采集** | ➕ 新增 | OPML 解析 + RSS 拉取 |
| **全文提取** | ➕ 新增 | Playwright 集成 + 字数统计 |
| **翻译流程** | ➕ 新增 | 三步翻译 |
| **RSS 输出** | ➕ 新增 | 多种 RSS feed |
| **周刊功能** | ➕ 新增 | 自动生成 |

### 6.2 开发阶段

#### Phase 1: 核心功能（当前）
1. ✅ 数据库基础结构
2. ✅ RSS 采集 + 全文提取
3. ✅ LLM 三步分析流程
4. ✅ 前端列表页 + 详情页
5. ✅ 基础筛选功能

#### Phase 1.5: 筛选增强（新增）
1. ➕ 语言筛选 (`lang=`)
2. ➕ 评分梯度筛选 (`score=`)
3. ➕ 无限滚动组件
4. ➕ 热门来源 API + 侧边栏
5. ➕ 卡片显示增强（图标、字数、阅读时间）
6. ➕ 首页 Hero Section

#### Phase 2: 完善功能
1. 翻译流程
2. Twitter 采集 (XGo.ing)
3. ✅ 播客转写 (通义听悟) - 代码已完成，待容器部署测试
4. ✅ 视频采集 (YouTube RSS) - 元数据采集已实现
5. 搜索功能
6. RSS 输出

#### Phase 3: 增强功能
1. 周刊功能
2. 视频内容转写（需要视频下载能力）
3. 精选标记优化
4. 性能优化

---

## 7. 参考资源

### 7.1 BestBlogs 资源（项目内）

| 文件 | 路径 | 用途 |
|------|------|------|
| 文章RSS源 | `BestBlog/BestBlogs_RSS_Articles.opml` | 170个源 |
| 播客RSS源 | `BestBlog/BestBlogs_RSS_Podcasts.opml` | 30个源 |
| Twitter源 | `BestBlog/BestBlogs_RSS_Twitters.opml` | 160个账号 |
| 视频RSS源 | `BestBlog/BestBlogs_RSS_Videos.opml` | 40个源 |
| Dify DSL | `BestBlog/flows/Dify/dsl/` | LLM流程参考 |
| 流程文档 | `BestBlog/flows/Dify/*.md` | 详细说明 |

### 7.2 关键 Prompt 参考

初评、分析、翻译的详细 Prompt 参考 `BestBlog/flows/Dify/dsl/` 目录下的 YAML 文件。

---

## 8. 验收标准

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

*文档版本: V2.3 (Transcription Implementation) | 更新时间: 2026-01-03 | 作者: Felix + Claude*
