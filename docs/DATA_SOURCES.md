# Signal 数据源目录

> 版本: 1.1 | 更新: 2026-02-09 | 状态: Active

本文档记录 Signal 支持的所有数据源、数据模型及采集流水线。

---

## 目录

1. [数据源概览](#1-数据源概览)
2. [数据源详情](#2-数据源详情)
3. [数据模型](#3-数据模型)
4. [采集流水线](#4-采集流水线)
5. [配置管理](#5-配置管理)

---

## 1. 数据源概览

### 1.1 数据源分类

| 分类 | 数据源 | 采集器 | 内容类型 | 数量 |
|------|--------|--------|----------|------|
| **RSS 订阅** | OPML 技术博客 | `rss.py` | article | 16 个 |
| **社交媒体** | Twitter/X | `xgoing.py` | tweet | 76 个 |
| **播客节目** | Podcast RSS | `podcast.py` | podcast | 11 个 |
| **视频内容** | YouTube RSS | `video.py` | video | 26 个 |

### 1.2 采集频率

| 频率 | 数据源 | 说明 |
|------|--------|------|
| **每小时** | RSS/OPML, Twitter | 时效性要求高 |
| **按需** | Podcast, Video | 手动触发或低频 |

### 1.3 数据源状态

```
┌─────────────────────────────────────────────────────────────┐
│                     数据源健康状态                           │
├────────────────┬────────────┬────────────┬─────────────────┤
│     数据源     │   状态     │  最近采集   │    今日采集     │
├────────────────┼────────────┼────────────┼─────────────────┤
│ RSS/OPML       │ ✅ 正常    │ 5分钟前    │ 127 条         │
│ Twitter        │ ✅ 正常    │ 30分钟前   │ 89 条          │
│ Podcast        │ ⏸️ 按需    │ 2天前      │ 0 条           │
│ YouTube        │ ⏸️ 按需    │ 3天前      │ 0 条           │
└────────────────┴────────────┴────────────┴─────────────────┘
```

---

## 2. 数据源详情

### 2.1 RSS/OPML 订阅

**采集器**: `backend/app/scrapers/rss.py`

**配置位置**: `backend/BestBlog/BestBlogs_RSS_Articles.opml`

**数据源 (16 个)**:

| 分类 | 数据源 | 数量 |
|------|--------|------|
| **AI 公司官方** | OpenAI Blog, Anthropic News, Google DeepMind Blog | 3 |
| **AI 工具框架** | LangChain Blog | 1 |
| **顶级博主** | 宝玉的分享 | 1 |
| **综合媒体** | 硅谷101, 晚点LatePost | 2 |
| **投资商业** | 海外独角兽, 真格基金 | 2 |
| **小众公众号** | 超人的电话亭, 深思圈, 赛博禅心, 向阳乔木推荐看, 花叔, 语言即世界, 十字路口Crossing | 7 |

**采集流程**:
```
1. 解析 OPML 文件，获取 RSS 订阅列表
2. 并发请求各 RSS Feed
3. 解析 Feed 条目 (feedparser)
4. 构造 RawSignal 对象
5. 规则预筛 + URL 去重
```

**输出字段**:
| 字段 | 来源 |
|------|------|
| title | feed.entry.title |
| url | feed.entry.link |
| content | feed.entry.summary / description |
| published_at | feed.entry.published |
| source_name | feed.title |

---

### 2.2 Twitter/X (XGoing)

**采集器**: `backend/app/scrapers/xgoing.py`

**配置位置**: `backend/BestBlog/BestBlogs_RSS_Twitters.opml`

**数据源 (76 个)**:

| 分类 | 账号类型 | 数量 |
|------|----------|------|
| **OpenAI 系** | OpenAI, ChatGPT, Sam Altman, Greg Brockman, Kevin Weil, Logan Kilpatrick, Lilian Weng 等 | 8 |
| **Anthropic 系** | Anthropic, Claude, Dario Amodei, Alex Albert, Mike Krieger, Jan Leike | 6 |
| **Google 系** | Google AI, DeepMind, Gemini, Demis Hassabis, Jeff Dean, Sundar Pichai 等 | 7 |
| **xAI** | xAI | 1 |
| **Microsoft** | MSFTResearch, Mustafa Suleyman, Satya Nadella | 3 |
| **AI 大佬** | Andrej Karpathy, Fei-Fei Li, Andrew Ng, DeepLearning.AI, Jim Fan 等 | 7 |
| **AI 开发工具** | Cursor, LangChain, Harrison Chase, mem0, Cognition, ManusAI 等 | 10 |
| **AI 媒体/播客** | Lex Fridman, Rowan Cheung, AI Engineer, Latent.Space | 4 |
| **投资人/企业家** | Marc Andreessen, a16z, Y Combinator, Justine Moore, andrew chen | 5 |
| **中文 AI 账号** | 宝玉, 歸藏, 小互, 向阳乔木, Yangyi, hidecloud | 6 |

**特点**:
- 跳过 LLM 分析，直接存储
- 高频采集 (每小时)
- 覆盖全球 AI 行业核心人物与组织

**采集流程**:
```
1. 调用 XGoing API
2. 获取指定账号的推文
3. 解析推文内容
4. 直接存储 (不经过 LLM 过滤)
```

**输出字段**:
| 字段 | 来源 |
|------|------|
| title | tweet.text (截取) |
| url | tweet.url |
| content | tweet.text |
| author | tweet.author |
| type | "tweet" |

---

### 2.3 Podcast RSS

**采集器**: `backend/app/scrapers/podcast.py`

**配置位置**: `backend/BestBlog/BestBlogs_RSS_Podcasts.opml`

**数据源 (11 个)**:
- What's Next｜科技早知道
- 无人知晓
- 硅谷101
- 乱翻书
- 硬地骇客
- AI炼金术
- 人民公园说AI
- 保持偏见
- 枫言枫语
- 屠龙之术
- 晚点聊 LateTalk

**特点**: 主要为中文科技/AI 播客节目

**处理流程**:
```
1. 解析播客 RSS Feed
2. 提取节目信息
3. 下载音频文件 (可选)
4. 听悟转写 → transcript
5. 章节分析 → chapters
6. Q&A 提取 → qa_pairs
```

**输出字段**:
| 字段 | 来源 |
|------|------|
| title | episode.title |
| url | episode.link |
| audio_url | episode.enclosure |
| duration | episode.duration |
| transcript | 听悟转写 |
| chapters | PodcastAnalyzer |
| qa_pairs | PodcastAnalyzer |

---

### 2.4 YouTube RSS

**采集器**: `backend/app/scrapers/video.py`

**配置位置**: `backend/BestBlog/BestBlogs_RSS_Videos.opml`

**数据源 (26 个)**:

| 分类 | 频道名称 |
|------|----------|
| **AI 公司官方** | Anthropic, OpenAI, Google DeepMind |
| **顶级播客** | AI Engineer, No Priors, Lenny's Podcast, Lex Fridman, Dwarkesh Patel |
| **技术教育** | Fireship, leerob, freeCodeCamp.org, ByteByteGo, LangChain |
| **AI 研究者** | Andrej Karpathy, Hung-yi Lee (李宏毅) |
| **AI 资讯** | AI Master, Matt Wolfe, Wes Roth, Last Week in AI, AI Explained |
| **AI 分析** | Two Minute Papers, Matthew Berman, AICodeKing, Liam Ottley |
| **其他** | Product School, Siraj Raval |

**特点**: 涵盖 AI 公司官方、顶级播客、技术教育、研究者、资讯分析等全方位内容

**处理流程**:
```
1. 解析 YouTube RSS Feed
2. 提取视频信息
3. 获取字幕/转写
4. 章节分析
```

**输出字段**:
| 字段 | 来源 |
|------|------|
| title | video.title |
| url | video.link |
| thumbnail | video.thumbnail |
| duration | video.duration |
| transcript | 字幕/转写 |

---

## 3. 数据模型

### 3.1 Resource (v2 核心模型)

**位置**: `backend/app/models/resource.py`

**类型枚举**:
```python
class ResourceType(Enum):
    article = "article"   # 文章
    podcast = "podcast"   # 播客
    tweet = "tweet"       # 推文
    video = "video"       # 视频
```

**核心字段**:

| 分类 | 字段 | 类型 | 描述 |
|------|------|------|------|
| **基础** | id | UUID | 主键 |
| | title | String | 标题 |
| | url | String | 原始链接 |
| | url_hash | String | URL MD5 哈希 (唯一) |
| | type | Enum | 内容类型 |
| | source_name | String | 来源名称 |
| | source_icon_url | String | 来源图标 |
| **分类** | domain | String | 一级领域 |
| | subdomain | String | 二级领域 |
| | tags | Array | 标签列表 |
| **LLM 分析** | one_sentence_summary | String | 一句话摘要 |
| | summary | Text | 详细摘要 |
| | main_points | Array | 核心观点 |
| | key_quotes | Array | 关键引用 |
| | score | Integer | 质量评分 (0-100) |
| **多语言** | title_translated | String | 标题翻译 |
| | summary_zh | Text | 中文摘要 |
| | main_points_zh | Array | 中文观点 |
| **LLM 过滤** | llm_score | Integer | LLM 评分 (0-5) |
| | llm_reason | Text | 评分理由 |
| | llm_prompt_version | String | Prompt 版本 |
| **人工审核** | review_status | Enum | 审核状态 |
| | review_comment | Text | 审核备注 |
| | reviewed_at | DateTime | 审核时间 |
| **播客/视频** | audio_url | String | 音频链接 |
| | duration | Integer | 时长 (秒) |
| | transcript | Text | 转录文本 |
| | chapters | JSON | 章节信息 |
| | qa_pairs | JSON | 问答对 |
| **精选** | is_featured | Boolean | 是否精选 |
| | featured_reason | Text | 推荐理由 |
| | featured_reason_zh | Text | 中文推荐理由 |
| **元数据** | published_at | DateTime | 发布时间 |
| | created_at | DateTime | 创建时间 |
| | language | String | 语言 (zh/en) |

---

### 3.2 Source (数据源管理)

**位置**: `backend/app/models/source.py`

**用途**: 管理数据源元信息

**核心字段**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| name | String | 数据源名称 |
| type | Enum | 类型 (blog/twitter/podcast/video) |
| url | String | 数据源 URL (唯一) |
| enabled | Boolean | 是否启用 |
| is_whitelist | Boolean | 是否白名单 |
| total_collected | Integer | 总采集数 |
| total_approved | Integer | 总通过数 |
| total_rejected | Integer | 总拒绝数 |
| avg_llm_score | Float | 平均 LLM 评分 |
| last_collected_at | DateTime | 最近采集时间 |
| last_error | Text | 最近错误信息 |

---

### 3.3 SourceRun (采集记录)

**位置**: `backend/app/models/source_run.py`

**用途**: 记录每次采集的统计数据

**核心字段**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| source_type | String | 数据源类型 |
| started_at | DateTime | 开始时间 |
| finished_at | DateTime | 结束时间 |
| status | Enum | 状态 (running/completed/failed) |
| fetched_count | Integer | 抓取数量 |
| rule_filtered | Integer | 规则过滤数 |
| dedup_filtered | Integer | 去重过滤数 |
| llm_filtered | Integer | LLM 过滤数 |
| saved | Integer | 最终保存数 |
| error_message | Text | 错误信息 |

---

### 3.4 RawSignal (采集中间结构)

**位置**: `backend/app/scrapers/base.py`

**用途**: 采集器输出的原始数据结构

```python
@dataclass
class RawSignal:
    title: str
    url: str
    content: str
    published_at: datetime
    source_name: str
    source_type: str
    extra: dict = None  # 额外数据
```

---

## 4. 采集流水线

### 4.1 流水线架构

```
┌─────────────────────────────────────────────────────────────┐
│                     采集流水线架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │ APScheduler │ ─── 定时触发                               │
│  └─────────────┘                                           │
│         │                                                   │
│         ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Pipeline 选择                       │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ ArticlePipeline │ TwitterPipeline │ PodcastPipeline │   │
│  │ VideoPipeline │                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               标准处理流程                           │   │
│  │  采集 → 去重 → 全文提取 → 过滤 → 分析 → 翻译 → 存储  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               数据追踪 (DataTracker)                 │   │
│  │           飞书多维表格记录                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 ArticlePipeline (文章流水线)

**触发**: 每小时 (RSS)

**处理步骤**:

| 步骤 | 处理器 | 输入 | 输出 |
|------|--------|------|------|
| 1 | RSS Scraper | OPML | RawSignal[] |
| 2 | Deduper | RawSignal[] | 去重后信号 |
| 3 | ContentExtractor | URL | 全文内容 |
| 4 | UnifiedFilter | 内容 | 过滤结果 |
| 5 | Analyzer | 内容 | 结构化分析 |
| 6 | Translator | 英文内容 | 中文翻译 |
| 7 | Favicon | URL | 图标URL |
| 8 | DB Save | 处理结果 | Resource |

**数据追踪节点**:
- 去重阶段: 记录重复项 (stage=dedup)
- 过滤阶段: 记录 LLM 评分 (stage=llm)
- 存储阶段: 记录收录项 (stage=save)

---

### 4.3 TwitterPipeline (推文流水线)

**触发**: 每小时

**特点**: 跳过 LLM 分析，直接存储

**处理步骤**:

| 步骤 | 处理器 | 说明 |
|------|--------|------|
| 1 | XGoing Scraper | 采集推文 |
| 2 | Deduper | URL 去重 |
| 3 | DB Save | 直接存储 |

---

### 4.4 PodcastPipeline / VideoPipeline

**触发**: 按需

**额外处理**:
- 音频/视频转写 (听悟)
- 章节分析 (PodcastAnalyzer)
- Q&A 提取 (PodcastAnalyzer)

---

## 5. 配置管理

### 5.1 数据源配置

**静态配置**: `config.yaml`

```yaml
scrapers:
  rss:
    enabled: true
    interval: 3600  # 秒
  xgoing:
    enabled: true
    interval: 3600
```

**动态配置**: `SourceConfig` 模型

```python
# 运行时覆盖 config.yaml
SourceConfig(
    source_type="rss",
    enabled=True,
    config_override={}
)
```

### 5.2 OPML 订阅管理

**位置**: `backend/BestBlog/` 目录

**文件清单**:
- `BestBlogs_RSS_Articles.opml` - 技术博客订阅 (16 个)
- `BestBlogs_RSS_Twitters.opml` - Twitter 账号订阅 (76 个)
- `BestBlogs_RSS_Podcasts.opml` - 播客节目订阅 (11 个)
- `BestBlogs_RSS_Videos.opml` - YouTube 频道订阅 (26 个)
- `current_sources.md` - 数据源清单文档

**格式**: 标准 OPML 2.0 文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Tech Blogs</title>
  </head>
  <body>
    <outline text="AI/ML" title="AI/ML">
      <outline type="rss" text="Blog Name" xmlUrl="https://..." />
    </outline>
  </body>
</opml>
```

**管理方式**:
- 直接编辑 OPML 文件
- 重启后端服务生效
- 使用管理后台动态启用/禁用

### 5.3 白名单机制

**作用**: 白名单源的内容自动通过 LLM 过滤 (score=5)

**设置方式**:
1. 管理后台: 数据源管理 → 设置白名单
2. API: `PUT /api/admin/sources/{id}/whitelist`

**生效位置**: `UnifiedFilter.filter()` 第一步检查

---

## 附录: 数据源 API 参考

| 数据源 | API 端点 | 认证 |
|--------|----------|------|
| XGoing | 私有 API | API Key |
| Tavily | https://api.tavily.com | API Key |

---

*数据源变更时请同步更新此文档*
