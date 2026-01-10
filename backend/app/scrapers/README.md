# Scrapers - 数据采集层

从外部数据源抓取原始数据，实现统一的爬虫接口。

## 文件清单

- `base.py` - BaseScraper 抽象基类，定义统一爬虫接口 + 重试逻辑
- `hackernews.py` - Hacker News 爬虫，调用 Firebase API 获取 Top Stories
- `github.py` - GitHub Trending 爬虫，通过 Search API 抓取热门项目
- `huggingface.py` - Hugging Face Models 爬虫，抓取热门 AI 模型
- `twitter.py` - Twitter RSS 爬虫，通过 RSS Bridge 免费抓取指定账号推文（旧版）
- `xgoing.py` - Twitter XGo.ing 爬虫，通过 XGo.ing 服务抓取 OPML 中的 Twitter 账号推文（推荐）
- `arxiv.py` - ArXiv 论文爬虫，通过官方 API 抓取最新 AI 论文
- `producthunt.py` - Product Hunt 爬虫，通过 GraphQL API 抓取热门产品
- `blog.py` - 博客 RSS 爬虫，解析 OPML 文件并异步抓取博客文章
- `podcast.py` - 播客 RSS 爬虫，解析 OPML 文件并异步抓取播客节目
- `video.py` - 视频 RSS 爬虫，解析 OPML 文件并异步抓取视频（YouTube 等）
- `opml_parser.py` - OPML 解析器，解析 BestBlogs OPML 订阅文件提取 RSS 源列表（支持 Twitter 用户名提取）
- `content_extractor.py` - Playwright 全文提取器，访问 URL 提取正文转 Markdown

## 数据源说明

### 1. Hacker News (免费)
- **API**: Firebase API (https://hacker-news.firebaseio.com/v0/)
- **无需 Token**: 完全开放
- **规则预筛**: Score ≥ 30 + 关键词匹配

### 2. GitHub (免费/Token可选)
- **API**: GitHub Search API
- **Token**: 可选，有 Token 限流更宽松
- **规则预筛**: Stars + Language + 排除 awesome-list

### 3. Hugging Face (免费)
- **API**: Hugging Face Models API
- **无需 Token**: 公开访问
- **规则预筛**: Likes ≥ 100 + Downloads ≥ 1000

### 4. Twitter - XGo.ing (免费，推荐)
- **方案**: XGo.ing 服务 (https://xgo.ing)
- **爬虫文件**: `xgoing.py`
- **无需 Token**: 完全免费
- **账号来源**: BestBlogs_RSS_Twitters.opml (160+ 账号)
- **URL 格式**: `https://api.xgo.ing/rss/user/{user_id}`
- **规则预筛**: 关键词匹配 + 排除转发
- **特性**:
  - 从 OPML 文件自动读取 Twitter 账号列表
  - 支持并发抓取（批量处理，避免限流）
  - 自动提取 Twitter 用户名

### 5. Twitter - RSS Bridge (免费，旧版)
- **方案**: RSS Bridge (https://rss-bridge.org/)
- **爬虫文件**: `twitter.py`
- **无需 Token**: 完全免费，绕过 Twitter API 限制
- **账号列表**: 需在配置中手动指定
- **规则预筛**: 关键词匹配 + 排除转发

### 6. ArXiv (免费)
- **API**: ArXiv API (https://export.arxiv.org/api/query)
- **无需 Token**: 学术资源，完全开放
- **规则预筛**: 分类过滤 (cs.AI, cs.LG 等) + 关键词匹配

### 7. Product Hunt (需 API Key)
- **API**: Product Hunt GraphQL API
- **需要 Token**: 在 .env 中配置 PRODUCTHUNT_API_KEY
- **申请地址**: https://www.producthunt.com/v2/oauth/applications
- **规则预筛**: Upvotes ≥ 100 + 分类匹配

### 8. BestBlogs OPML 订阅源 (免费)
- **解析器**: `opml_parser.py`
- **数据来源**: BestBlog/ 目录下的 OPML 文件
- **源统计**:
  - 文章源: 200 个 (BestBlogs_RSS_Articles.opml)
  - 播客源: 30 个 (BestBlogs_RSS_Podcasts.opml)
  - 视频源: 40 个 (BestBlogs_RSS_Videos.opml)
  - Twitter 源: 160 个 (BestBlogs_RSS_Twitters.opml)
- **用途**: 为 RSS Scraper、Podcast Scraper、Video Scraper 和 XGoing Scraper 提供订阅源列表

### 9. 播客 RSS (免费)
- **爬虫文件**: `podcast.py`
- **数据源**: BestBlogs_RSS_Podcasts.opml
- **支持格式**: 标准 RSS 2.0 + iTunes podcast extension
- **提取内容**: 标题、描述、音频URL、时长、发布时间
- **转写支持**: 可选集成通义听悟 API 进行音频转写

### 10. 视频 RSS (免费)
- **爬虫文件**: `video.py`
- **数据源**: BestBlogs_RSS_Videos.opml
- **支持平台**: YouTube、其他标准视频 RSS 源
- **提取内容**: 标题、描述、视频URL、缩略图、时长、发布时间
- **YouTube 特性**:
  - 自动提取视频 ID
  - 获取高清缩略图 (hqdefault/maxresdefault)
  - 支持 media_yt_duration 时长提取
- **转写支持**: 可选集成通义听悟 API 进行视频转写
- **配置**: `config.video.transcribe_enabled` (默认 False，成本较高)

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
