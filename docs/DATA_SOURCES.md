# Signal Hunter 数据源配置规范

> **单一真相源** - 所有数据源变更必须在此文档同步更新
>
> [PROTOCOL]: 变更时更新此文档，然后同步到相关代码和配置文件

---

## 1. 当前启用的数据源

Signal Hunter 只采集以下 4 类内容：

| 模块 | 类型 | 当前数量 | 状态 |
|------|------|----------|------|
| **文章** | Blog RSS | 16 源 | ✅ 生产中 |
| **播客** | Podcast RSS | 待配置 | 🔧 规划中 |
| **推文** | Twitter (XGoing) | 待配置 | 🔧 规划中 |
| **视频** | Video RSS | 待配置 | 🔧 规划中 |

---

## 2. Blog RSS 源清单 (16个)

来源：`backend/BestBlog/current_sources.md`

| # | 名称 | 状态 |
|---|------|------|
| 1 | 阮一峰的网络日志 | ✅ |
| 2 | 云风的 BLOG | ✅ |
| 3 | 酷壳 | ✅ |
| 4 | 二丫讲梵 | ✅ |
| 5 | Limboy | ✅ |
| 6 | DIYGod | ✅ |
| 7 | 一派胡言 | ✅ |
| 8 | Yingbo Li | ✅ |
| 9 | 戴铭 | ✅ |
| 10 | GeekPlux | ✅ |
| 11 | 小胡子哥 | ✅ |
| 12 | Pseudoyu | ✅ |
| 13 | Owen | ✅ |
| 14 | 1byte | ✅ |
| 15 | Randy's Blog | ✅ |
| 16 | Tw93 | ✅ |

---

## 3. 已废弃的数据源

以下数据源已永久移除，**不再采集**：

| 数据源 | 移除日期 | 原因 |
|--------|----------|------|
| Hacker News | 2026-01-17 | 用户决定不需要 |
| GitHub Trending | 2026-01-17 | 用户决定不需要 |
| arXiv | 2026-01-17 | 用户决定不需要 |
| HuggingFace | 2026-01-17 | 用户决定不需要 |
| Product Hunt | 2026-01-17 | 用户决定不需要 |

---

## 4. 配置文件位置

数据源配置分布在以下位置，变更时需**全部同步**：

| 文件 | 位置 | 职责 |
|------|------|------|
| `DATA_SOURCES.md` | `docs/` | **本文档 - 权威配置** |
| `current_sources.md` | `backend/BestBlog/` | Blog RSS 源清单 |
| `config.yaml` | `backend/app/` | 后端数据源开关 |
| `startup.py` | `backend/app/` | 定时任务配置 |
| `sources-page-content.tsx` | `frontend/components/admin/` | 前端 UI 展示 |
| `scheduler-page-content.tsx` | `frontend/components/admin/` | 任务描述映射 |

---

## 5. 定时任务配置

| 任务 ID | 名称 | 触发规则 | 采集内容 |
|---------|------|----------|----------|
| `twitter_pipeline_job` | Twitter 采集 | 每 1 小时 | 推文 |
| `main_pipeline_job` | RSS 内容采集 | 每 12 小时 | Blog/Podcast/Video |
| `daily_digest_job` | 每日精选 | 每天 07:00 | 汇总 |
| `weekly_digest_job` | 每周精选 | 每周一 08:00 | 汇总 |
| `newsletter_job` | 周刊生成 | 每周五 17:00 | 周刊 |

---

## 6. 变更日志

### 2026-01-17 - 数据源精简

**变更内容**：
- 移除 5 个数据源：HN、GitHub、arXiv、HuggingFace、Product Hunt
- 保留 4 个模块：文章、播客、推文、视频
- 更新前端任务描述

**修改文件**：
- `backend/app/api/stats.py` - 修复 API 路由路径
- `backend/app/api/admin/prompts.py` - 修复响应格式
- `frontend/components/admin/scheduler-page-content.tsx` - 更新任务描述
- `frontend/app/admin/page.tsx` - 新建重定向页面

**待完成**：
- [ ] 后端 `config.yaml` 禁用废弃数据源
- [ ] 后端 `main_pipeline` 任务逻辑调整

---

## 7. 新增数据源流程

1. **更新本文档** - 在对应模块表格中添加新源
2. **更新后端配置** - 修改 `config.yaml` 或 OPML 文件
3. **验证采集** - 手动触发或等待定时任务
4. **同步前端** - 如需展示新类型，更新 UI 组件

---

## 8. 相关文档

- `docs/PRD.md` - 产品需求文档（数据源规划）
- `backend/BestBlog/` - OPML 配置目录
- `docs/media-subscriptions.md` - 播客/视频订阅清单

---

[PROTOCOL]: 变更时更新此文档，然后同步到相关代码和配置文件
