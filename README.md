# AI Signal Hunter (AI 信号捕手)

> 🎯 面向超级个体的技术情报分析系统

从 Hacker News 等海量信息源中自动筛选高质量技术信号，通过 Kimi AI 深度过滤和摘要生成，帮助独立开发者、科技投资人、技术创作者每天节省 2 小时信息筛选时间。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

## ✨ 核心特性

- 🤖 **智能过滤**: 使用 Kimi AI 判断内容是否符合标准（新代码/新模型/新论文/可复现结果/可用工具）
- 📝 **AI 摘要**: 自动生成一句话总结 + 详细摘要 + 评分 + 分类标签
- 🔬 **Deep Research**: 一键生成1500字深度研究报告,含技术分析、竞品对比、应用场景(Phase 2新功能)
- 🔍 **搜索筛选**: 支持按来源、评分、分类、关键词筛选信号
- 📊 **数据统计**: 实时查看信号分布、评分统计、系统运行状态
- 🎯 **详情页**: 点击查看完整信号详情,包含摘要、评分、标签、原文链接
- 🔄 **自动采集**: APScheduler 定时任务,每小时自动抓取最新内容
- 🎨 **精美界面**: Next.js 14 + 渐变主题,响应式设计
- 💰 **成本优化**: 规则预筛过滤 70% 噪音,每次运行仅消耗 ~60K tokens（约 ¥0.6）
- 🐳 **开箱即用**: Docker Compose 一键启动
- ⚡ **已验证**: 实际运行数据 - 51条抓取 → 15条通过 → 100%成功率

## 📊 实际运行效果

**最新一次运行统计** (2025-12-29):
- ✅ 抓取: 51 条 HN 热门新闻
- ✅ 过滤: 15 条通过（过滤率 71%）
- ✅ 成功: 15 条全部保存
- 💰 成本: ¥0.67 (67,193 tokens)
- ⏱️ 用时: ~6 分钟

**发现的高质量信号**:
- Alzheimer's disease can be reversed in animal models - 阿尔茨海默病可逆转研究
- Asahi Linux with Sway on MacBook Air M2 - M2 Mac运行Linux
- iOS 26.3 brings AirPods-like pairing to third-party devices - iOS新特性

## 🚀 快速开始

### 前置要求

- Docker Desktop
- OpenAI API Key（用于 GPT-4o-mini）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/signal-hunter.git
cd signal-hunter
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
```

3. **启动服务**
```bash
docker-compose up --build
```

4. **访问应用**
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 📖 使用说明

### 查看信号列表

访问 http://localhost:3000 即可看到自动抓取的技术信号，支持：
- 按来源筛选（HN / GitHub / Hugging Face）
- 按评分筛选（1-5 星）
- 按类型筛选（技术突破 / 开源工具 / 论文研究等）

### 查看详情

点击任意信号卡片，查看：
- 一句话总结（20 字）
- 结构化摘要（3-5 个要点）
- 质量评分 + 热度评分
- 原文链接
- **🔬 Deep Research**: 生成1500字深度研究报告(AI驱动)

### 生成深度研究报告 (新功能!)

在信号详情页点击"🔬 生成深度研究报告"按钮:
1. 系统自动生成3个研究问题
2. 使用Tavily Search搜索相关资料(6次搜索)
3. AI综合分析生成1500字深度报告
4. 包含参考来源链接和成本统计
5. 24小时缓存,避免重复生成

**预计时间**: 60-120秒
**预计成本**: $0.03/篇 (~¥0.2)
**报告内容**: 技术深度分析、竞品对比、应用场景、总结建议

### 手动触发抓取

```bash
# 进入后端容器
docker-compose exec backend bash

# 手动运行流水线
python -c "from app.tasks.pipeline import run_full_pipeline; run_full_pipeline()"
```

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Next.js 14)                       │
│  Dashboard (SSR) → Signal Detail (SSR) → Client Components  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    API 层 (FastAPI)                          │
│  /api/signals | /api/signals/{id} | /health                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              定时任务层 (APScheduler)                         │
│  每小时触发: Scrape → Dedup → Filter → Generate → Store     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   数据存储 (SQLite WAL)                       │
│  signals 表 | run_logs 表                                   │
└──────────────────────────────────────────────────────────────┘
```

**详细架构**: 查看 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 📊 成本估算

### LLM 成本（OpenAI GPT-4o-mini）
- 每小时处理 ~20 条信号
- 月成本: **$12-15**（包含过滤 + 摘要生成）

### 其他成本
- Jina Reader: 免费额度足够（200 次/天）
- Docker 运行: 本地零成本

## 📁 项目结构

```
signal/
├── ARCHITECTURE.md          # 系统架构文档
├── PRD.md                   # 产品需求文档
├── README.md                # 本文件
├── config.yaml              # 配置文件
├── docker-compose.yml       # Docker 编排
├── .env.example             # 环境变量模板
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── scrapers/        # 数据采集
│   │   ├── processors/      # 数据处理
│   │   ├── tasks/           # 定时任务
│   │   └── api/             # API 路由
│   └── data/                # SQLite 数据库
│
└── frontend/                # Next.js 前端
    ├── app/                 # 应用页面
    ├── components/          # UI 组件
    └── lib/                 # 工具库
```

## 🛠️ 开发指南

### 本地开发

**后端开发**:
```bash
cd backend
uv sync  # 安装依赖
uv run uvicorn app.main:app --reload
```

**前端开发**:
```bash
cd frontend
pnpm install
pnpm dev
```

### 运行测试

```bash
# 后端测试
cd backend
uv run pytest

# 前端测试（待添加）
cd frontend
pnpm test
```

### 代码格式化

```bash
# 后端
cd backend
uv run ruff check .
uv run ruff format .

# 前端
cd frontend
pnpm lint
```

## 📚 文档

- [系统架构](./ARCHITECTURE.md) - 技术架构详解
- [开发指南](./docs/DEVELOPMENT.md) - 本地开发教程
- [API 文档](./docs/API.md) - REST API 接口说明
- [部署指南](./docs/DEPLOYMENT.md) - 生产环境部署

## 🗺️ Roadmap

### ✅ Phase 1: MVP（当前版本）
- [x] Hacker News 数据源
- [x] 单 Prompt LLM 过滤 + 摘要
- [x] SQLite 数据存储
- [x] Next.js 前端展示
- [x] Docker Compose 本地部署

### 🚧 Phase 2: 增强版
- [ ] GitHub Trending 数据源
- [ ] Hugging Face 数据源
- [ ] Deep Dive 深度研报（1000-1500 字）
- [ ] WebSocket 实时更新
- [ ] 用户配置界面

### 🔮 Phase 3: 完整版
- [ ] Multi-Agent 架构（LangGraph）
- [ ] Reddit 数据源
- [ ] 风格化输出（Style RAG）
- [ ] 多用户支持
- [ ] 邮件/Telegram 推送

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

贡献前请：
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Hacker News](https://news.ycombinator.com/) - 数据源
- [OpenAI](https://openai.com/) - GPT-4o-mini
- [Jina AI](https://jina.ai/) - Jina Reader
- [shadcn/ui](https://ui.shadcn.com/) - UI 组件库

## 📮 联系方式

- 作者: Felix
- 项目主页: https://github.com/yourusername/signal-hunter
- Issue: https://github.com/yourusername/signal-hunter/issues

---

**Built with ❤️ by Felix**
