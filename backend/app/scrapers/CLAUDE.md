# backend/app/scrapers/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
多源数据采集层，负责从各个平台抓取原始数据，进行规则预筛和去重。

## 成员清单
base.py: BaseScraper 抽象基类，定义 RawSignal 数据结构
rss.py: 通用 RSS 爬虫，解析 OPML 订阅列表 (核心内容源)
hackernews.py: Hacker News Firebase API 爬虫，Score > 80 + 关键词过滤
github.py: GitHub Trending API 爬虫，按语言过滤，获取 stars/forks
arxiv.py: arXiv API 爬虫，论文采集，支持分类过滤
huggingface.py: HuggingFace Models API 爬虫，AI 模型库
twitter.py: Twitter/X API 爬虫 (Legacy，待迁移至 XGoing)
xgoing.py: XGoing 平台爬虫 (新版推文采集)
producthunt.py: Product Hunt API 爬虫，产品采集
podcast.py: 播客 RSS Feed 爬虫
video.py: 视频 RSS Feed 爬虫 (YouTube RSS)
blog.py: 博客抓取器 (Jina Reader)
content_extractor.py: 全文提取器 (Jina Reader + Playwright)
opml_parser.py: OPML 文件解析器
favicon.py: 网站 Favicon 获取器

## 数据源概览
| 爬虫 | 数据源 | 采集频率 | 特点 |
|------|--------|---------|------|
| rss.py | RSS/OPML | 每小时 | 核心内容源，高质量技术博客 |
| hackernews.py | HN API | 每12小时 | Score > 80，关键词过滤 |
| github.py | GitHub Trending | 每12小时 | 按语言，stars/forks |
| arxiv.py | arXiv API | 每12小时 | AI/ML 论文 |
| huggingface.py | HF API | 每12小时 | 新模型发布 |
| xgoing.py | XGoing | 每小时 | 推文采集 |
| producthunt.py | PH API | 每12小时 | 新产品 |

## 采集流程
```
1. 调用数据源 API
2. 解析响应，构造 RawSignal[]
3. 规则预筛 (关键词匹配)
4. URL Hash 去重
5. 返回新增信号
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
