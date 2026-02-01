# Signal 部署指南

> 版本: 1.0 | 更新: 2026-01-30 | 状态: Active

本文档提供 Signal 的本地开发、生产部署和运维指南。

---

## 目录

1. [快速开始](#1-快速开始)
2. [环境变量配置](#2-环境变量配置)
3. [本地开发环境](#3-本地开发环境)
4. [生产部署](#4-生产部署)
5. [监控与运维](#5-监控与运维)
6. [故障排查](#6-故障排查)

---

## 1. 快速开始

### 1.1 前置要求

- Docker & Docker Compose
- Node.js 18+ (前端开发)
- Python 3.11+ (后端开发)
- Git

### 1.2 一键启动

```bash
# 克隆项目
git clone https://github.com/your-org/signal.git
cd signal

# 复制环境变量文件
cp .env.example .env

# 编辑环境变量 (必填项)
vim .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 1.3 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Next.js 应用 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 数据库管理 | http://localhost:5050 | pgAdmin (可选) |

---

## 2. 环境变量配置

### 2.1 必需变量

```bash
# ============================================
# 数据库配置
# ============================================
DATABASE_URL=postgresql://signal_user:signal_pass@db:5432/signal_db

# ============================================
# Redis 配置
# ============================================
REDIS_URL=redis://redis:6379/0

# ============================================
# AI API Keys (必填)
# ============================================
# Moonshot Kimi K2 - 内容分析/研究
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxx

# Tavily - 网络搜索增强
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx

# 百炼 (DashScope) - 文本嵌入
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx

# ============================================
# 安全配置
# ============================================
JWT_SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=development
```

### 2.2 可选变量

```bash
# ============================================
# API 访问控制 (生产环境推荐)
# ============================================
API_KEYS=key1,key2,key3

# ============================================
# CORS 配置
# ============================================
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com

# ============================================
# 日志配置
# ============================================
LOG_LEVEL=INFO

# ============================================
# 性能配置
# ============================================
WEB_CONCURRENCY=4

# ============================================
# 文件存储 (R2/S3)
# ============================================
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=signal-hunter

# ============================================
# 飞书集成 (数据追踪)
# ============================================
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_BITABLE_APP_TOKEN=xxxxx
FEISHU_BITABLE_TABLE_ID=tblxxxxx

# ============================================
# OAuth (可选)
# ============================================
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 2.3 前端环境变量

```bash
# frontend/.env.local
INTERNAL_API_URL=http://backend:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

---

## 3. 本地开发环境

### 3.1 Docker Compose 开发模式

```bash
# 启动所有服务 (开发模式)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启单个服务
docker-compose restart backend

# 停止所有服务
docker-compose down

# 清理数据卷 (慎用)
docker-compose down -v
```

### 3.2 热重载配置

**后端热重载**:
```yaml
# docker-compose.yml
backend:
  volumes:
    - ./backend/app:/app/app  # 源码挂载
```

**前端热重载**:
```yaml
frontend:
  volumes:
    - ./frontend/app:/app/app
    - ./frontend/components:/app/components
    - ./frontend/lib:/app/lib
```

### 3.3 本地不使用 Docker

**后端**:
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

**前端**:
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3.4 数据库管理

**进入数据库容器**:
```bash
docker-compose exec db psql -U signal_user -d signal_db
```

**常用 SQL**:
```sql
-- 查看表结构
\dt

-- 查看资源数量
SELECT COUNT(*) FROM resource;

-- 查看最近采集
SELECT title, source_name, created_at
FROM resource
ORDER BY created_at DESC
LIMIT 10;

-- 查看 LLM 评分分布
SELECT llm_score, COUNT(*)
FROM resource
GROUP BY llm_score
ORDER BY llm_score;
```

**数据库迁移**:
```bash
# 迁移脚本位于 backend/migrations/
# 手动执行 SQL 迁移

docker-compose exec db psql -U signal_user -d signal_db -f /path/to/migration.sql
```

---

## 4. 生产部署

### 4.1 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      生产部署架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐                                         │
│  │   Cloudflare  │ ← 用户流量入口                           │
│  │     DNS       │                                         │
│  └───────┬───────┘                                         │
│          │                                                  │
│    ┌─────┴─────┐                                           │
│    │           │                                           │
│    ↓           ↓                                           │
│  ┌───────────┐ ┌───────────┐                              │
│  │ Cloudflare│ │  Railway  │                              │
│  │  Pages    │ │  Backend  │                              │
│  │ (前端静态)│ │ (FastAPI) │                              │
│  └───────────┘ └─────┬─────┘                              │
│                      │                                     │
│              ┌───────┴───────┐                            │
│              │               │                            │
│              ↓               ↓                            │
│        ┌───────────┐   ┌───────────┐                     │
│        │  Railway  │   │  Railway  │                     │
│        │ PostgreSQL│   │   Redis   │                     │
│        └───────────┘   └───────────┘                     │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │                 外部服务                           │   │
│  │  Moonshot | Tavily | 百炼 | CosyVoice | R2        │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Railway 后端部署

**1. 创建项目**:
```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init
```

**2. 配置环境变量**:
在 Railway Dashboard 中设置所有必需的环境变量。

**3. 部署**:
```bash
# 连接到 Railway 项目
railway link

# 部署后端
cd backend
railway up
```

**4. 数据库配置**:
- 在 Railway 中添加 PostgreSQL 插件
- 添加 Redis 插件
- 自动生成 DATABASE_URL 和 REDIS_URL

### 4.3 Cloudflare Pages 前端部署

**1. 连接仓库**:
- 登录 Cloudflare Dashboard
- 进入 Pages
- 连接 GitHub 仓库

**2. 构建配置**:
```
Build command: cd frontend && npm run build
Build output directory: frontend/.next
Root directory: /
```

**3. 环境变量**:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

**4. 自定义域名**:
- 添加自定义域名
- 配置 DNS 记录

### 4.4 生产环境 Docker Compose

```bash
# 使用生产配置
docker-compose -f docker-compose.prod.yml up -d
```

**docker-compose.prod.yml** 关键差异:
- 不挂载源码卷
- 更严格的资源限制
- 生产级日志配置
- 健康检查更频繁

---

## 5. 监控与运维

### 5.1 健康检查

**后端健康检查**:
```bash
curl http://localhost:8000/health
```

响应:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-30T10:00:00Z"
}
```

**Docker 健康检查**:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 5.2 日志管理

**查看实时日志**:
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend

# 最近 100 行
docker-compose logs --tail=100 backend
```

**日志级别**:
```bash
LOG_LEVEL=DEBUG  # 开发
LOG_LEVEL=INFO   # 生产
LOG_LEVEL=WARNING  # 仅警告
```

### 5.3 备份与恢复

**数据库备份**:
```bash
# 备份
docker-compose exec db pg_dump -U signal_user signal_db > backup.sql

# 恢复
docker-compose exec -T db psql -U signal_user signal_db < backup.sql
```

**定时备份脚本**:
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR=/path/to/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker-compose exec -T db pg_dump -U signal_user signal_db | gzip > $BACKUP_DIR/signal_db_$TIMESTAMP.sql.gz

# 保留最近 7 天
find $BACKUP_DIR -name "signal_db_*.sql.gz" -mtime +7 -delete
```

### 5.4 资源监控

**Docker 资源使用**:
```bash
docker stats
```

**数据库监控**:
```sql
-- 连接数
SELECT COUNT(*) FROM pg_stat_activity;

-- 表大小
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## 6. 故障排查

### 6.1 常见问题

#### 问题: 后端启动失败

**症状**: `docker-compose up` 后后端服务退出

**排查**:
```bash
docker-compose logs backend
```

**常见原因**:
1. 数据库连接失败 - 检查 DATABASE_URL
2. 缺少环境变量 - 检查必填变量
3. 端口占用 - 检查 8000 端口

#### 问题: 前端无法连接后端

**症状**: API 请求返回网络错误

**排查**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 CORS 配置
# 确保 FRONTEND_URL 正确
```

#### 问题: LLM 调用失败

**症状**: 内容分析返回错误

**排查**:
```bash
# 检查 API Key
curl -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  https://api.moonshot.cn/v1/models
```

**常见原因**:
1. API Key 无效
2. 额度用尽
3. 网络问题

#### 问题: 采集任务不运行

**症状**: 数据不更新

**排查**:
```bash
# 检查调度器状态
docker-compose logs backend | grep -i scheduler

# 手动触发
curl -X POST http://localhost:8000/api/tasks/pipeline/trigger \
  -H "Content-Type: application/json" \
  -d '{"pipeline": "article"}'
```

### 6.2 性能优化

**数据库优化**:
```sql
-- 创建缺失索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resource_published_at
ON resource (published_at DESC);

-- 分析表
ANALYZE resource;

-- 清理死行
VACUUM ANALYZE resource;
```

**Redis 优化**:
```bash
# 检查内存使用
docker-compose exec redis redis-cli INFO memory

# 清理过期键
docker-compose exec redis redis-cli --scan --pattern '*' | head
```

### 6.3 紧急操作

**重启所有服务**:
```bash
docker-compose restart
```

**强制重建**:
```bash
docker-compose down
docker-compose up -d --build
```

**回滚部署** (Railway):
```bash
railway rollback
```

---

## 附录: 服务端口

| 服务 | 端口 | 协议 |
|------|------|------|
| 前端 | 3000 | HTTP |
| 后端 | 8000 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| pgAdmin | 5050 | HTTP |

---

*部署流程变更时请同步更新此文档*
