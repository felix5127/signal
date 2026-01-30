# docs/
> L2 | 父级: /CLAUDE.md

## 职责
项目文档目录，存放产品规格、架构设计、API 文档、技术设计方案。

## 核心文档

### 产品与架构
| 文件 | 描述 | 状态 |
|------|------|------|
| **PRD.md** | 产品需求文档 v3.0 - 功能规格/API/数据库/UI设计 | 最新 |
| **DATA_SOURCES.md** | 数据源配置规范 (单一真相源) | 最新 |
| **API_GUIDE.md** | API 使用指南，端点说明与示例 | 最新 |

### 研究助手模块
| 文件 | 描述 |
|------|------|
| RESEARCH_ASSISTANT_SPEC.md | 研究助手产品规范 v1.1 |
| RESEARCH_ASSISTANT_TECHNICAL_DESIGN.md | 研究助手技术方案 |
| RESEARCH_ASSISTANT_DEV_PLAN.md | 研究助手开发计划 |

### 审查记录 (历史)
| 文件 | 描述 |
|------|------|
| filter-review-2026-01-13.md | 过滤规则审查记录 |
| twitter-following-review.md | Twitter 关注列表审查 |
| wechat-rss-review.md | 微信 RSS 审查记录 |
| media-subscriptions.md | 播客/视频订阅清单 |

## 子目录

### architecture/
系统架构设计文档
| 文件 | 描述 | 状态 |
|------|------|------|
| **ARCHITECTURE.md** | 系统架构文档 v3.0 - 后端/前端/数据库/部署 | 最新 |

### design/
技术设计方案文档
| 文件 | 描述 |
|------|------|
| MULTIMODAL_PROCESSING.md | 多模态处理技术方案 |
| PODCAST_GENERATION.md | 播客生成模块技术方案 |
| AGENT_SYSTEM.md | Agent 系统设计 |
| FRONTEND_COMPONENTS.md | 前端组件规格 |

### deployment/
部署指南
| 文件 | 描述 |
|------|------|
| CLOUDFLARE_DEPLOYMENT_GUIDE.md | Cloudflare 部署指南 |

### plans/
开发计划与迭代记录
| 文件 | 描述 |
|------|------|
| 2026-01-17-data-pipeline-refactor-spec.md | 数据管道重构规格 |
| 2026-01-17-data-pipeline-refactor-design.md | 数据管道重构设计 |
| 2026-01-25-ui-ux-findings.md | UI/UX 问题发现 |
| 2026-01-25-ui-ux-pro-max-redesign.md | UI/UX 重构计划 |
| 2026-01-25-ui-ux-progress.md | UI/UX 重构进度日志 |
| 2026-01-27-design-updates.md | 设计变更日志 |

## 文档层级

```
docs/
├── PRD.md                    # 产品需求文档 (核心)
├── ARCHITECTURE.md → architecture/  # 架构文档入口
├── DATA_SOURCES.md           # 数据源配置 (单一真相源)
├── API_GUIDE.md              # API 使用指南
├── RESEARCH_ASSISTANT_*.md   # 研究助手系列
├── architecture/             # 架构设计
├── design/                   # 技术设计
├── deployment/               # 部署指南
└── plans/                    # 开发计划
```

## 文档更新规范

1. **PRD.md** - 功能变更时更新
2. **ARCHITECTURE.md** - 架构变更时更新
3. **DATA_SOURCES.md** - 数据源变更时更新 (单一真相源)
4. **design/*.md** - 新增模块时创建技术设计
5. **plans/*.md** - 重大迭代时创建计划文档

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
