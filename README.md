# Signal Hunter

> AI-powered tech intelligence radar for super-individuals

Signal Hunter automatically aggregates content from multiple sources (RSS, Twitter/X, Podcasts, YouTube), filters high-quality signals using AI, and generates structured summaries and deep research reports.

## Features

- **Multi-source aggregation** — RSS/OPML, Twitter/X, Podcasts, YouTube
- **AI-powered filtering** — Rule-based pre-filter + LLM scoring (0-5 scale)
- **Deep analysis** — Three-step analysis: Analyze → Reflect → Optimize
- **Bilingual support** — Auto-translation between English and Chinese
- **Deep research** — Tavily search-enhanced research reports
- **Research workspace** — Project-based knowledge management with AI chat
- **Podcast generation** — Convert articles to podcast-style audio
- **Admin dashboard** — Content review, source management, analytics

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, shadcn/ui, Framer Motion |
| Backend | FastAPI, SQLAlchemy 2.0, APScheduler |
| Database | PostgreSQL 15, Redis 7 |
| AI | Kimi K2 (Moonshot), Tavily Search, DashScope (Embedding/TTS) |
| Deploy | Docker Compose, Railway |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys (see [Configuration](#configuration))

### 1. Clone & Configure

```bash
git clone https://github.com/felix5127/signal-hunter.git
cd signal-hunter
cp .env.example .env
```

Edit `.env` with your API keys (see [Configuration](#configuration)).

### 2. Start with Docker Compose

```bash
# Development mode (with hot reload)
docker-compose up -d

# Production mode
docker-compose -f docker-compose.prod.yml up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Database Setup

Migrations run automatically on first start. For manual migration:

```bash
docker exec signal-backend python -m app.tasks.migrate
```

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Kimi/Moonshot API key ([get one](https://platform.moonshot.cn)) |
| `TAVILY_API_KEY` | Yes | Tavily search API key ([get one](https://tavily.com)) |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT authentication |
| `ADMIN_PASSWORD` | Yes | Admin dashboard password |
| `DATABASE_URL` | Auto | PostgreSQL connection (auto-configured in Docker) |
| `REDIS_URL` | Auto | Redis connection (auto-configured in Docker) |
| `GITHUB_TOKEN` | No | GitHub API token for higher rate limits |
| `JINA_API_KEY` | No | Jina Reader API key for full-text extraction |
| `KIMI_API_KEY` | No | Kimi K2 API key for research agent |
| `DASHSCOPE_API_KEY` | No | Alibaba DashScope for embedding/TTS |
| `R2_*` | No | Cloudflare R2 for file storage (research workspace) |

## Project Structure

```
signal-hunter/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/             # REST API routes
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── services/        # Business logic
│   │   ├── processors/      # Content processing (AI analysis, translation)
│   │   ├── scrapers/        # Data collectors (RSS, Twitter, Podcast, Video)
│   │   ├── tasks/           # Background tasks & pipeline
│   │   ├── agents/          # AI agents (mindmap, research)
│   │   └── utils/           # Utilities (LLM client, cache, logger)
│   ├── migrations/          # SQL migration scripts
│   ├── BestBlog/            # OPML subscription configs
│   └── tests/               # Test suite
├── frontend/                 # Next.js 14 frontend
│   ├── app/                 # App Router pages
│   ├── components/          # React components (shadcn/ui)
│   ├── lib/                 # Utilities & design system
│   └── hooks/               # Custom React hooks
├── docs/                     # Documentation
│   ├── API.md               # API reference
│   ├── ARCHITECTURE.md      # System architecture
│   ├── FEATURES.md          # Feature specifications
│   ├── DATA_SOURCES.md      # Data source guide
│   └── DEPLOYMENT.md        # Deployment guide
├── docker-compose.yml        # Dev environment
├── docker-compose.prod.yml   # Production environment
└── config.yaml              # Data source & LLM configuration
```

## Data Pipeline

```
Scheduled Tasks (APScheduler)
       ↓
Data Collection (RSS/Twitter/Podcast/Video)
       ↓
Rule-based Pre-filter
       ↓
AI Analysis (LLM scoring + summary + categorization)
       ↓
Translation (EN → CN)
       ↓
PostgreSQL Storage
       ↓
REST API (FastAPI)
       ↓
Web UI (Next.js)
```

## Documentation

- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Features](docs/FEATURES.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
