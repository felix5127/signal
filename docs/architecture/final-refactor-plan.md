# Signal 最终重构方案

> 基于 4 个调研 Agent 并行分析的系统诊断结果
> 日期: 2026-02-22

---

## Phase 1: 修复数据 Pipeline（让系统跑起来）

> 优先级: 🔴 CRITICAL — 系统核心功能不工作

### 1.1 Scheduler 接入新版 Pipeline
**问题**: `startup.py` 的定时任务调用旧版 `tasks/pipeline.py:run_full_pipeline`，新版 `pipeline/article_pipeline.py` 从未被 Scheduler 执行。

**修改文件**:
- `backend/app/scheduler_jobs.py` — 将 `scheduled_main_pipeline` 改为调用新版 pipeline
- `backend/app/startup.py` — 确认 scheduler 注册正确

**验证**: Scheduler 启动后日志应显示新版 pipeline 的 structlog 输出

### 1.2 清理旧版 Pipeline 入口
**修改文件**:
- `backend/app/tasks/pipeline.py` — 删除旧版 `run_full_pipeline`（或重定向到新版）
- 确认无其他代码引用旧版入口

### 1.3 Playwright 版本对齐
**修改文件**:
- `backend/Dockerfile` — 确认 `COPY --from=builder /ms-playwright /ms-playwright` 存在
- `backend/requirements.txt` — 锁定 playwright 版本与基础镜像一致

### 1.4 OPML 文件确认
**检查**: `BestBlog/` 目录是否在 git 中（不在 .gitignore 中）
**修改**: 如缺失，确保 Dockerfile COPY 路径正确

---

## Phase 2: 修复排序（用户体验）

> 优先级: 🔴 HIGH — 用户可见的排序问题

### 2.1 前端排序接通
**问题**: `resource-list-page.tsx` 硬编码 `sort: 'default'`，排序 UI 无效

**修改文件**:
- `frontend/components/resource-list-page.tsx`:
  - 将 `sort` 改为 state 变量，默认值 `'time'`
  - 连接 CompactFilterToolbar 的排序选择到 fetch 参数
  - 排序变化时重置 currentPage 为 1

**验证**: 文章列表默认按时间倒序，切换排序后数据正确刷新

---

## Phase 3: 删除研究模块（代码清理）

> 优先级: 🟡 MEDIUM — 减少维护负担和部署复杂度

### 3.1 前端 — 删除页面和组件（~15 文件）
**完整删除**:
- `frontend/app/research/` (整个目录, 3 个页面)
- `frontend/components/research/` (整个目录, 8 个文件)
- `frontend/components/deep-research-button.tsx`
- `frontend/components/research-page-content.tsx`

### 3.2 前端 — 修改引用文件（6 文件）
- `frontend/components/navbar.tsx` — 删除"研究"导航项
- `frontend/components/ClientLayout.tsx` — 删除 isResearchWorkspace 逻辑
- `frontend/components/resource-detail.tsx` — 删除 DeepResearchButton 导入和使用
- `frontend/components/video/video-detail.tsx` — 删除 DeepResearchButton
- `frontend/components/podcast/podcast-detail.tsx` — 删除 DeepResearchButton
- `frontend/components/global-search.tsx` — 删除 research 路由 case

### 3.3 后端 — 删除模块（~12 文件）
**完整删除**:
- `backend/app/agents/research/` (整个目录, 5 个文件)
- `backend/app/processors/deep_research/` (整个目录, 5 个文件)
- `backend/app/api/research.py`
- `backend/app/services/deep_research_service.py`
- `backend/app/models/research.py`
- `backend/test_agent_sdk_compat.py`
- `backend/test_zhipu_compat.py`

### 3.4 后端 — 修改引用文件（6 文件）
- `backend/app/main.py` — 删除 research_router import 和 include_router
- `backend/app/models/__init__.py` — 删除 research 模型 import
- `backend/app/models/resource.py` — 删除 7 个 deep_research_* 字段
- `backend/app/api/resources.py` — 删除 deep-research 端点
- `backend/app/background_tasks.py` — 删除 deep_research 任务函数
- `backend/app/database.py` — 删除 pgvector 检测 + research 表创建逻辑

### 3.5 依赖清理
- `backend/requirements.txt` — 移除: `pgvector>=0.2.0`, `claude-agent-sdk>=0.1.33`, `dashscope` (如仅用于 research)
- `docker-compose.yml` — db 镜像从 `pgvector/pgvector:pg15` 改为 `postgres:15`

### 3.6 文档删除
- `docs/research/` (整个目录)
- `docs/architecture/sdk-migration-design.md`
- `docs/review/sdk-migration-review.md`

---

## Phase 4: 收尾优化

> 优先级: 🟢 LOW — 代码质量和维护性

### 4.1 删除死页面
- `frontend/app/design-system/` (整个目录)
- `frontend/app/neumorphic-showcase/` (整个目录)

### 4.2 统一前端包管理（npm）
- `frontend/Dockerfile` (生产) — 从 pnpm 改为 npm
- `frontend/Dockerfile.dev` — 确认使用 npm

### 4.3 修复容器健康检查
- `frontend/Dockerfile.dev` — `wget` 改为 `node -e "fetch('http://localhost:3000')"` 或 `curl`

### 4.4 更新文档
- `CLAUDE.md` — 删除研究模块相关文档引用
- `docs/DEPLOYMENT.md` — 删除研究模块环境变量
- `docs/FEATURES.md` — 删除深度研究功能描述
- `docs/API.md` — 删除研究 API 文档
- `docs/ARCHITECTURE.md` — 删除研究模块架构描述

---

## 执行策略

建议使用 Agent Team 并行执行:
- **Developer A (前端)**: Phase 2 + Phase 3.1-3.2 + Phase 4.1
- **Developer B (后端)**: Phase 1 + Phase 3.3-3.5 + Phase 4.2-4.3
- **Doc Updater**: Phase 3.6 + Phase 4.4

预计修改: ~30 文件删除 + ~15 文件修改
