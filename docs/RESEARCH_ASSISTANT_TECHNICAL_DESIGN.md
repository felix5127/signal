# Signal Hunter 研究助手 - 技术方案

> 版本: 2.0 | 日期: 2026-01-18 | 状态: 设计中

---

## 目录

1. [系统架构](#1-系统架构)
2. [技术选型](#2-技术选型)
3. [数据模型](#3-数据模型)
4. [API 设计](#4-api-设计)
5. [Agent 架构](#5-agent-架构)
6. [前端架构](#6-前端架构)
7. [多模态处理](#7-多模态处理)
8. [播客生成](#8-播客生成)

---

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户层 (User Layer)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │   Web Browser   │  │   Mobile (PWA)  │  │   API Client    │      │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘      │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      前端层 (Frontend Layer)                         │
│                         Next.js 14 App Router                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │   Pages    │ │ Components │ │   Hooks    │ │   Stores   │       │
│  │ /research  │ │ Workspace  │ │ useResearch│ │  Zustand   │       │
│  │ /research/ │ │ ChatPanel  │ │ useChat    │ │ AuthStore  │       │
│  │   [id]     │ │ OutputPanel│ │ useStream  │ │ UIStore    │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API 层 (API Layer)                             │
│                           FastAPI                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │   /auth    │ │ /research  │ │   /chat    │ │  /podcast  │       │
│  │   /users   │ │ /projects  │ │  /sources  │ │  /outputs  │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     服务层 (Service Layer)                           │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐          │
│  │ ProjectService │ │ ResearchService│ │  ChatService   │          │
│  │ SourceService  │ │ PodcastService │ │ EmbeddingService│         │
│  └────────────────┘ └────────────────┘ └────────────────┘          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent 层 (Agent Layer)                            │
│                        DeepAgents Framework                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Research Agent                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│  │  │ Planning │ │ Analysis │ │ Synthesis│ │ Output   │        │   │
│  │  │ Module   │ │ Module   │ │ Module   │ │ Module   │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                       Sub-Agents                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│  │  │ Summary  │ │ MindMap  │ │ Podcast  │ │  Search  │        │   │
│  │  │ Agent    │ │ Agent    │ │ Agent    │ │  Agent   │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│   PostgreSQL    │ │  Cloudflare R2  │ │     External APIs       │
│   + pgvector    │ │  (File Storage) │ │                         │
│                 │ │                 │ │ Kimi K2 (Moonshot)      │
│ - users         │ │ - audio/        │ │ Tavily                  │
│ - projects      │ │ - video/        │ │ 听悟 (阿里云)           │
│ - sources       │ │ - podcast/      │ │ 通义千问 Omni (可选)    │
│ - embeddings    │ │ - exports/      │ │ CosyVoice (百炼)        │
│ - outputs       │ │                 │ │ 百炼嵌入                │
└─────────────────┘ └─────────────────┘ └─────────────────────────┘
```

### 1.2 数据流图

```
研究任务数据流:

用户发起研究
    │
    ▼
┌───────────────────┐
│  创建研究任务      │
│  (research_tasks) │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│  加载源材料        │────▶│  向量检索相关内容   │
│  (research_sources)│     │  (source_embeddings)│
└─────────┬─────────┘     └───────────────────┘
          │
          ▼
┌───────────────────┐
│  Research Agent   │
│  规划任务步骤      │
│  (write_todos)    │
└─────────┬─────────┘
          │
          ├──────────────────┬──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐
│  Tavily Search  │ │  Vector Search  │
│  (网络搜索)      │ │  (知识库)        │
└────────┬────────┘ └────────┬────────┘
         │                   │
         └───────────────────┘
                             │
                             ▼
                   ┌───────────────────┐
                   │  综合分析生成      │
                   │  结构化输出        │
                   └─────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  结构化摘要      │ │   思维导图       │ │   研究报告      │
│  (summary)      │ │   (mindmap)     │ │   (report)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
                   ┌───────────────────┐
                   │  保存到数据库      │
                   │  (research_outputs)│
                   └───────────────────┘
```

---

## 2. 技术选型

### 2.1 LLM 选型

| 用途 | 模型 | 理由 |
|------|------|------|
| **研究 Agent** | kimi-k2-thinking-turbo | 1T参数MoE，256K上下文，原生工具调用，推理模式 |
| **对话 Agent** | kimi-k2-turbo-preview | 高速版，40 t/s，快速响应 |
| **摘要生成** | kimi-k2-turbo-preview | 性价比高 |
| **长文档** | kimi-k2-thinking-turbo | 256K 上下文已足够 |

### 2.2 嵌入模型

| 模型 | 维度 | 优势 |
|------|------|------|
| 百炼 通用文本向量-v3 | 512 (默认) | 阿里云百炼，中文优化，搜索快速 |

### 2.3 搜索引擎

| 引擎 | 用途 |
|------|------|
| Tavily | 网络搜索，返回原始内容 |
| pgvector | 本地向量搜索 |

### 2.4 多模态处理

| 类型 | 服务 | 理由 |
|------|------|------|
| 音频转写 | 听悟 API (阿里云) | 用户已有，支持中英文，高精度 |
| 视频理解 | 通义千问 Omni (可选) | 阿里云全模态模型 |
| TTS | 百炼 CosyVoice | 多音色支持，自然度高，成本低 |

### 2.5 基础设施

| 组件 | 选型 |
|------|------|
| 数据库 | PostgreSQL 16 + pgvector |
| 文件存储 | Cloudflare R2 |
| 后端 | FastAPI + Python 3.12 |
| 前端 | Next.js 14 + TypeScript |
| 部署 | Railway + Cloudflare |

---

## 3. 数据模型

### 3.1 ER 图

```
┌─────────────────┐       ┌─────────────────┐
│      users      │       │ research_projects│
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──────▶│ id (PK)         │
│ email           │       │ owner_id (FK)   │
│ password_hash   │       │ name            │
│ name            │       │ description     │
│ avatar_url      │       │ status          │
│ created_at      │       │ created_at      │
└─────────────────┘       └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │ research_sources│ │ research_outputs│ │  chat_sessions  │
          ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
          │ id (PK)         │ │ id (PK)         │ │ id (PK)         │
          │ project_id (FK) │ │ project_id (FK) │ │ project_id (FK) │
          │ resource_id     │ │ output_type     │ │ title           │
          │ source_type     │ │ title           │ │ messages (JSONB)│
          │ title           │ │ content         │ │ context_sources │
          │ full_text       │ │ file_path       │ │ message_count   │
          │ metadata        │ │ metadata        │ │ created_at      │
          └────────┬────────┘ └─────────────────┘ └─────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │source_embeddings│
          ├─────────────────┤
          │ id (PK)         │
          │ source_id (FK)  │
          │ chunk_index     │
          │ chunk_text      │
          │ embedding       │
          └─────────────────┘
```

### 3.2 表结构详细设计

#### users 表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(100),
    avatar_url TEXT,

    -- OAuth
    github_id VARCHAR(50) UNIQUE,
    google_id VARCHAR(50) UNIQUE,

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
```

#### research_projects 表

```sql
CREATE TABLE research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',  -- active, archived

    -- 统计
    source_count INTEGER DEFAULT 0,
    output_count INTEGER DEFAULT 0,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_researched_at TIMESTAMPTZ
);

CREATE INDEX idx_projects_owner ON research_projects(owner_id);
CREATE INDEX idx_projects_status ON research_projects(status);
```

#### research_sources 表

```sql
CREATE TABLE research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES resources(id),  -- 关联 Signal

    -- 源信息
    source_type VARCHAR(50) NOT NULL,  -- url, pdf, audio, video, text
    title VARCHAR(500),
    original_url TEXT,
    file_path TEXT,

    -- 内容
    full_text TEXT,
    summary TEXT,
    metadata JSONB DEFAULT '{}',

    -- 处理
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_sources_project ON research_sources(project_id);
CREATE INDEX idx_sources_status ON research_sources(processing_status);
```

#### source_embeddings 表

```sql
CREATE TABLE source_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES research_sources(id) ON DELETE CASCADE,

    -- 分块
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tokens INTEGER,

    -- 向量 (百炼 通用文本向量-v3，512维)
    embedding vector(512) NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_id, chunk_index)
);

-- HNSW 索引 (比 IVFFlat 更快)
CREATE INDEX idx_embeddings_vector ON source_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

#### research_outputs 表

```sql
CREATE TABLE research_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,

    -- 输出信息
    output_type VARCHAR(50) NOT NULL,  -- summary, mindmap, report, podcast
    title VARCHAR(500),
    content TEXT,
    content_format VARCHAR(50) DEFAULT 'markdown',

    -- 文件
    file_path TEXT,
    file_size INTEGER,
    duration INTEGER,  -- 秒 (音频)

    -- 元数据
    metadata JSONB DEFAULT '{}',
    source_refs UUID[],

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outputs_project ON research_outputs(project_id);
CREATE INDEX idx_outputs_type ON research_outputs(output_type);
```

#### chat_sessions 表

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,

    -- 会话信息
    title VARCHAR(255),
    context_source_ids UUID[] DEFAULT '{}',

    -- 消息
    messages JSONB DEFAULT '[]',

    -- 统计
    message_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,

    -- 时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_project ON chat_sessions(project_id);
```

---

## 4. API 设计

### 4.1 API 概览

| 模块 | 端点 | 方法 | 描述 |
|------|------|------|------|
| **认证** | /auth/register | POST | 注册 |
| | /auth/login | POST | 登录 |
| | /auth/me | GET | 当前用户 |
| **项目** | /projects | GET | 项目列表 |
| | /projects | POST | 创建项目 |
| | /projects/{id} | GET | 项目详情 |
| | /projects/{id} | DELETE | 删除项目 |
| **源材料** | /projects/{id}/sources | GET | 源列表 |
| | /projects/{id}/sources | POST | 添加源 |
| | /sources/{id} | DELETE | 删除源 |
| | /sources/upload | POST | 上传文件 |
| **研究** | /projects/{id}/research | POST | 发起研究 (SSE) |
| | /projects/{id}/research/{tid} | GET | 任务状态 |
| **对话** | /projects/{id}/chat | POST | 发送消息 (SSE) |
| | /projects/{id}/chat/sessions | GET | 会话列表 |
| **输出** | /projects/{id}/outputs | GET | 输出列表 |
| | /outputs/{id} | GET | 输出详情 |
| | /outputs/{id}/export | GET | 导出 |
| **播客** | /projects/{id}/podcast | POST | 生成播客 |
| | /podcasts/{id} | GET | 播客详情 |

### 4.2 核心 API 详细设计

#### POST /projects/{id}/research

发起研究任务，返回 SSE 流。

**请求**:
```json
{
  "source_ids": ["uuid1", "uuid2"],
  "output_types": ["summary", "mindmap"],
  "task": "深度分析这些材料的核心观点"
}
```

**SSE 响应**:
```
event: start
data: {"task_id": "uuid", "status": "started"}

event: progress
data: {"step": 1, "total": 5, "message": "分析材料...", "todos": [...]}

event: partial
data: {"type": "summary", "content": "## 核心发现\n..."}

event: complete
data: {"task_id": "uuid", "outputs": [...]}

event: error
data: {"error": "错误信息"}
```

#### POST /projects/{id}/chat

对话接口，返回 SSE 流。

**请求**:
```json
{
  "message": "能详细解释第一个观点吗？",
  "session_id": "uuid",
  "context_source_ids": ["uuid1", "uuid2"]
}
```

**SSE 响应**:
```
event: start
data: {"session_id": "uuid"}

event: token
data: {"content": "当然"}

event: token
data: {"content": "，让我"}

event: done
data: {"full_content": "当然，让我...", "tokens_used": 150}
```

---

## 5. Agent 架构

### 5.1 Agent 层级结构

```
Research Agent (主 Agent)
│
├── 能力
│   ├── 任务规划 (write_todos)
│   ├── 上下文管理 (自动压缩)
│   ├── 工具调用 (搜索、读取、写入)
│   └── 子Agent调度
│
├── 工具 (Tools)
│   ├── tavily_search      - 网络搜索
│   ├── vector_search      - 向量检索
│   ├── read_source        - 读取源材料
│   ├── write_output       - 写入输出
│   └── delegate_task      - 委派子Agent
│
├── Skills (按需加载)
│   ├── research/SKILL.md      - 研究技能
│   ├── summarization/SKILL.md - 摘要技能
│   ├── mindmap/SKILL.md       - 思维导图技能
│   └── podcast/SKILL.md       - 播客技能
│
└── Sub-Agents (子Agent)
    ├── Summary Agent    - 生成摘要
    ├── MindMap Agent    - 生成思维导图
    ├── Podcast Agent    - 生成播客
    └── Search Agent     - 深度搜索
```

### 5.2 Agent 配置

```python
# 研究 Agent 配置 (kimi-k2-thinking-turbo)
RESEARCH_AGENT_CONFIG = {
    "model": "kimi-k2-thinking-turbo",
    "max_tokens": 8192,
    "temperature": 1.0,  # Thinking 模型推荐
    "recursion_limit": 50,
    "context_limit": 250000,  # 256K - buffer
    "summarization_threshold": 0.85,
    "stream": True,  # 必须启用流式
}

# 对话 Agent / 子 Agent 配置 (kimi-k2-turbo-preview)
SUB_AGENT_CONFIGS = {
    "chat": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 4096,
        "temperature": 1.0,
    },
    "summary": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 4096,
        "temperature": 1.0,
    },
    "mindmap": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 2048,
        "temperature": 1.0,
    },
    "podcast": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 8192,
        "temperature": 1.0,
    },
    "search": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 4096,
        "temperature": 1.0,
    },
}
```

### 5.3 Skills 设计

#### research/SKILL.md

```markdown
---
name: deep-research
description: 深度研究材料，生成结构化分析
---

## 研究流程

1. **材料阅读**: 仔细阅读所有源材料
2. **信息提取**: 提取关键概念、数据、观点
3. **外部搜索**: 搜索相关背景信息补充
4. **综合分析**: 对比、关联、总结
5. **输出生成**: 按要求格式输出

## 输出规范

### 结构化摘要
- 一句话总结 (30字以内)
- 核心观点 (3-5点)
- 关键数据 (如有)
- 结论与启发

### 思维导图
使用 Markdown 缩进列表，层级不超过4层

### 研究报告
- 背景介绍 (200字)
- 主要内容 (500字)
- 分析评论 (300字)
- 总结建议 (200字)
```

---

## 6. 前端架构

### 6.1 目录结构

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── research/
│   │   │   ├── page.tsx           # 研究项目列表
│   │   │   └── [id]/
│   │   │       └── page.tsx       # 研究工作台
│   │   └── layout.tsx
│   ├── api/
│   │   └── auth/[...nextauth]/route.ts
│   └── layout.tsx
├── components/
│   ├── research/
│   │   ├── project-list.tsx
│   │   ├── project-card.tsx
│   │   ├── workspace.tsx          # 研究工作台
│   │   ├── panels/
│   │   │   ├── source-panel.tsx   # 左栏: 材料
│   │   │   ├── output-panel.tsx   # 中栏: 输出
│   │   │   └── chat-panel.tsx     # 右栏: 对话
│   │   ├── source-selector.tsx    # 材料选择器
│   │   ├── research-progress.tsx  # 研究进度
│   │   └── output-viewer.tsx      # 输出查看器
│   └── ui/
│       └── ... (shadcn组件)
├── hooks/
│   ├── use-projects.ts
│   ├── use-research.ts
│   ├── use-chat.ts
│   └── use-sse.ts
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── projects.ts
│   │   ├── research.ts
│   │   └── chat.ts
│   └── stores/
│       ├── auth-store.ts
│       └── research-store.ts
└── types/
    └── research.ts
```

### 6.2 状态管理

```typescript
// lib/stores/research-store.ts
import { create } from 'zustand'

interface ResearchState {
  // 当前项目
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void

  // 选中的源
  selectedSourceIds: string[]
  toggleSource: (id: string) => void

  // 研究任务
  currentTask: ResearchTask | null
  taskProgress: TaskProgress | null

  // 对话
  chatMessages: Message[]
  addMessage: (message: Message) => void
}

export const useResearchStore = create<ResearchState>((set) => ({
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  selectedSourceIds: [],
  toggleSource: (id) => set((state) => ({
    selectedSourceIds: state.selectedSourceIds.includes(id)
      ? state.selectedSourceIds.filter(s => s !== id)
      : [...state.selectedSourceIds, id]
  })),

  currentTask: null,
  taskProgress: null,

  chatMessages: [],
  addMessage: (message) => set((state) => ({
    chatMessages: [...state.chatMessages, message]
  })),
}))
```

### 6.3 SSE 客户端

```typescript
// hooks/use-sse.ts
import { useState, useCallback, useRef } from 'react'

interface UseSSEOptions<T> {
  onMessage?: (data: T) => void
  onError?: (error: Error) => void
  onComplete?: () => void
}

export function useSSE<T>(url: string, options: UseSSEOptions<T> = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [data, setData] = useState<T | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const connect = useCallback(() => {
    const es = new EventSource(url, { withCredentials: true })
    eventSourceRef.current = es

    es.onopen = () => setIsConnected(true)

    es.onmessage = (event) => {
      const parsed = JSON.parse(event.data)
      setData(parsed)
      options.onMessage?.(parsed)
    }

    es.onerror = (error) => {
      setIsConnected(false)
      options.onError?.(new Error('SSE connection error'))
      es.close()
    }

    es.addEventListener('complete', () => {
      options.onComplete?.()
      es.close()
    })

    return es
  }, [url, options])

  const disconnect = useCallback(() => {
    eventSourceRef.current?.close()
    setIsConnected(false)
  }, [])

  return { connect, disconnect, isConnected, data }
}
```

---

*技术方案文档继续在下一部分...*
