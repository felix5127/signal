# Signal Hunter 研究助手 - 产品规范文档

> 版本: 1.1 | 日期: 2026-01-17 | 状态: 待评审

---

## 1. 项目概述

### 1.1 愿景

将 Signal Hunter 从"信号聚合工具"升级为"AI 研究助手"，融合 Open Notebook 的知识管理能力和 DeepAgents 的智能 Agent 能力，打造一个能够**持续对话、深度研究、多资源综合分析**的个人研究平台。

### 1.2 核心定位

| 维度 | 描述 |
|------|------|
| **目标用户** | 超级个体、技术研究者、知识工作者 |
| **核心价值** | 从"信息消费"到"知识生产"的升级 |
| **差异化** | 渐进式研究 + 多模态支持 + AI 持续对话 |

### 1.3 与现有系统的关系

```
Signal Hunter 现有功能 (保留)
├── 信号采集 (RSS/HN/GitHub/arXiv/HuggingFace)
├── 初评过滤 (UnifiedFilter)
├── 资源列表展示
└── 基础统计

新增: 研究助手模块 (融合)
├── 笔记本系统 (参考 Open Notebook)
├── 深度研究引擎 (DeepAgents 重构)
├── 多模态处理 (音视频转写)
└── 对话式研究 (持续交互)
```

---

## 2. 功能架构

### 2.1 四层功能模型

```
┌─────────────────────────────────────────────────────────────┐
│ L4: 自主规划任务 (后续迭代)                                    │
│     Agent 自主规划研究步骤、多轮执行、任务追踪                   │
├─────────────────────────────────────────────────────────────┤
│ L3: 对话式学习                                               │
│     基于笔记本上下文的多轮对话、答疑解惑、深入追问               │
├─────────────────────────────────────────────────────────────┤
│ L2: 深度研究                                                 │
│     结构化摘要、思维导图(MD)、概念图/PPT、研究报告、播客生成      │
├─────────────────────────────────────────────────────────────┤
│ L1: 材料汇总                                                 │
│     多源采集、多模态导入、智能过滤、笔记本组织                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 L1: 材料汇总

#### 2.2.1 输入源支持

| 类型 | 格式 | 处理方式 | 优先级 |
|------|------|----------|--------|
| **网页/文章** | URL | Jina/Firecrawl 提取 | P0 |
| **PDF/文档** | PDF, DOCX, TXT | 文本提取 + OCR | P0 |
| **音频/播客** | MP3, WAV, M4A | 听悟 API 转写 | P0 |
| **视频** | MP4, WebM, YouTube URL | 音轨提取 + 听悟转写 | P0 |

#### 2.2.2 笔记本组织

```python
# 数据模型
class Notebook:
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    owner_id: str  # 用户 ID

class Source:
    id: str
    notebook_id: str
    source_type: Enum["url", "pdf", "audio", "video", "text"]
    title: str
    original_url: str
    full_text: str
    embeddings: List[float]  # 向量化
    metadata: dict

class Note:
    id: str
    notebook_id: str
    note_type: Enum["human", "ai"]
    title: str
    content: str  # Markdown
    source_refs: List[str]  # 关联的 Source ID
```

### 2.3 L2: 深度研究

#### 2.3.1 输出类型

| 输出 | 描述 | 优先级 |
|------|------|--------|
| **结构化摘要** | 标题 + 核心观点 + 关键数据 + 结论 | P0 必须 |
| **思维导图** | Markdown 格式的层级结构 | P0 必须 |
| **概念图/PPT** | AI 生成的可视化展示 | P0 必须 |
| **研究报告** | 1500+ 字的完整分析报告 | P1 可选 |
| **播客** | 1-4 人对话式音频内容 | P1 想要 |

#### 2.3.2 研究引擎架构 (DeepAgents)

```python
# 基于 DeepAgents 的研究引擎
research_agent = create_deep_agent(
    model="kimi-k2-thinking-turbo",  # 主研究 Agent (Kimi K2 Thinking)
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    tools=[
        search_tool,      # Tavily 搜索
        read_source,      # 读取源材料
        write_note,       # 写入笔记
        generate_summary, # 生成摘要
        generate_mindmap, # 生成思维导图
    ],
    memory=["./notebooks/{notebook_id}/AGENTS.md"],
    skills=["./skills/research/"],
    backend=FilesystemBackend(root_dir="./research_data/"),
)
```

#### 2.3.3 研究工作流

```
用户选择材料 → 创建研究任务
    ↓
Agent 规划 (write_todos):
  - [ ] 提取核心观点
  - [ ] 识别关键概念
  - [ ] 搜索背景资料
  - [ ] 综合分析
  - [ ] 生成输出
    ↓
多轮执行 (可中断、可追问)
    ↓
生成多种输出格式
    ↓
保存到笔记本
```

### 2.4 L3: 对话式学习

#### 2.4.1 对话上下文

```python
class ChatSession:
    id: str
    notebook_id: str
    messages: List[Message]
    context_sources: List[str]  # 当前对话包含的 Source ID
    model_override: Optional[str]
```

#### 2.4.2 对话能力

| 能力 | 描述 |
|------|------|
| **基于知识库** | 对话基于笔记本内的所有材料 |
| **多轮追问** | 支持连续深入追问 |
| **上下文管理** | 自动压缩长对话，保持高效 |
| **引用溯源** | 回答时标注信息来源 |

### 2.5 L4: 自主规划任务 (后续迭代)

```
# 未来能力
用户: "帮我研究 Rust vs Go 在微服务场景的选型"
    ↓
Agent 自主规划:
  1. 搜索两者的性能对比数据
  2. 收集大厂使用案例
  3. 分析各自的生态成熟度
  4. 对比学习曲线和团队成本
  5. 生成选型建议报告
    ↓
多轮自主执行 (可监控进度)
    ↓
生成完整研究报告
```

---

## 3. 技术架构

### 3.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Signal  │ │Notebook │ │Research │ │  Chat   │ │ Podcast │   │
│  │  List   │ │ Manager │ │Workspace│ │Interface│ │Generator│   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼──────────┼──────────┼──────────┼──────────┼────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │/signals │ │/notebook│ │/research│ │  /chat  │ │/podcast │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼──────────┼──────────┼──────────┼──────────┼────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │ResourceSvc  │ │NotebookSvc  │ │   ResearchAgentSvc      │   │
│  │(现有)       │ │(新增)       │ │   (DeepAgents 驱动)      │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌─────────────────┐          ┌─────────────────────────────────┐
│   PostgreSQL    │          │         DeepAgents Core          │
│   + pgvector    │          │  ┌─────────┐ ┌─────────────┐    │
│                 │          │  │Middleware│ │   Backend   │    │
│ - notebooks     │          │  │  Stack   │ │ (Filesystem)│    │
│ - sources       │          │  └─────────┘ └─────────────┘    │
│ - notes         │          │  ┌─────────┐ ┌─────────────┐    │
│ - embeddings    │          │  │  Skills │ │  SubAgents  │    │
│ - chat_sessions │          │  └─────────┘ └─────────────┘    │
└─────────────────┘          └─────────────────────────────────┘
                                       │
                                       ▼
                             ┌─────────────────────┐
                             │    External APIs     │
                             │ - Kimi K2 (LLM)      │
                             │ - Tavily (Search)    │
                             │ - 听悟 (STT)         │
                             │ - CosyVoice (TTS)    │
                             └─────────────────────┘
```

### 3.2 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **前端框架** | Next.js 14 (App Router) | 现有 Signal Hunter 架构 |
| **后端框架** | FastAPI | 现有架构 + 异步优先 |
| **数据库** | PostgreSQL + pgvector | 延续现有 + 向量搜索 |
| **Agent 框架** | DeepAgents + LangGraph | 规划 + 多轮 + 上下文管理 |
| **LLM 主模型** | Kimi K2 (kimi-k2-thinking-turbo) | 用户已有账号 + 256K 长上下文 |
| **对话 LLM** | Kimi K2 (kimi-k2-turbo-preview) | 高速对话场景 |
| **搜索增强** | Tavily API | 现有集成 |
| **音视频转写** | 听悟 API | 用户已有账号，中文优化 |
| **向量化** | 百炼 通用文本向量-v3 | 用户已有百炼账号 |
| **TTS (播客)** | 百炼 CosyVoice | 成本低，支持多音色 |

### 3.3 DeepAgents 集成方案

```python
# backend/app/agents/research_agent.py

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

class ResearchAgentService:
    """基于 DeepAgents 的研究 Agent 服务"""

    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id
        self.backend = FilesystemBackend(
            root_dir=f"./research_data/{notebook_id}/"
        )

    def create_agent(self, context_sources: List[str]):
        """创建研究 Agent"""
        return create_deep_agent(
            model="kimi-k2-thinking-turbo",  # Kimi K2 主研究模型
            system_prompt=self._build_system_prompt(context_sources),
            tools=self._get_tools(),
            memory=[f"./notebooks/{self.notebook_id}/AGENTS.md"],
            skills=["./skills/research/", "./skills/summarization/"],
            backend=self.backend,
        )

    async def research(
        self,
        task: str,
        sources: List[Source],
        stream: bool = True
    ):
        """执行研究任务"""
        agent = self.create_agent([s.id for s in sources])

        # 构建上下文
        context = self._build_context(sources)

        # 执行 Agent
        async for chunk in agent.astream({
            "messages": [
                {"role": "user", "content": f"{context}\n\n任务: {task}"}
            ]
        }):
            if stream:
                yield chunk

        return chunk  # 最终结果

    async def chat(
        self,
        message: str,
        session: ChatSession,
        stream: bool = True
    ):
        """对话式研究"""
        agent = self.create_agent(session.context_sources)

        # 加载历史消息
        messages = session.messages + [
            {"role": "user", "content": message}
        ]

        async for chunk in agent.astream({"messages": messages}):
            if stream:
                yield chunk

        # 保存对话历史
        session.messages.append({"role": "user", "content": message})
        session.messages.append({"role": "assistant", "content": chunk})

        return chunk
```

### 3.4 数据库扩展

```sql
-- 新增表结构

-- 用户表 (完整用户系统)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 笔记本表
CREATE TABLE notebooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 源材料表
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID REFERENCES notebooks(id),
    resource_id UUID REFERENCES resources(id),  -- 可选关联 Signal
    source_type VARCHAR(50) NOT NULL,  -- url, pdf, audio, video, text
    title VARCHAR(500),
    original_url TEXT,
    full_text TEXT,
    metadata JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 源材料向量表
CREATE TABLE source_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id),
    chunk_index INTEGER,
    chunk_text TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 笔记表
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID REFERENCES notebooks(id),
    note_type VARCHAR(50) NOT NULL,  -- human, ai, summary, mindmap
    title VARCHAR(500),
    content TEXT,
    source_refs UUID[],  -- 关联的 source ID 列表
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 对话会话表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID REFERENCES notebooks(id),
    title VARCHAR(255),
    messages JSONB DEFAULT '[]',
    context_sources UUID[],
    model_override VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 播客表
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID REFERENCES notebooks(id),
    title VARCHAR(500),
    description TEXT,
    speakers JSONB,  -- 发言人配置
    transcript TEXT,  -- 对话稿
    audio_url TEXT,   -- 音频文件 URL
    duration INTEGER,  -- 秒
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_sources_notebook ON sources(notebook_id);
CREATE INDEX idx_notes_notebook ON notes(notebook_id);
CREATE INDEX idx_source_embeddings_source ON source_embeddings(source_id);
CREATE INDEX idx_source_embeddings_vector ON source_embeddings
    USING ivfflat (embedding vector_cosine_ops);
```

---

## 4. UI/UX 设计

### 4.1 入口设计

**核心变更**: 现有的"深入研究"按钮升级为"研究工作台"入口，导航栏新增"研究"入口。

```
┌─────────────────────────────────────────────────────────────────┐
│  导航栏                                                          │
│  Logo  [文章] [播客] [视频] [推文] [研究] [精选]    [搜索] [用户] │
│                                      ↑                          │
│                               新增入口：研究                      │
└─────────────────────────────────────────────────────────────────┘
```

**两个入口**：

| 入口 | 位置 | 作用 |
|------|------|------|
| **导航栏 [研究]** | 全局导航 | 查看所有研究项目，管理历史研究 |
| **资源详情页 [研究]** | 资源卡片/详情 | 快速将当前资源加入研究项目 |

### 4.2 研究项目列表页 (导航栏入口)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 我的研究                                        [+ 新建研究] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📓 AI 2026 趋势                              3 个材料   │   │
│  │  上次研究: 2 小时前  |  状态: 进行中                      │   │
│  │  材料: GPT-5 解读, Claude 4 报告, Gemini 2 发布         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📓 投资笔记                                  8 个材料   │   │
│  │  上次研究: 昨天  |  状态: 已完成                         │   │
│  │  材料: YC Demo Day, a16z 报告...                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📓 Rust 学习                                 5 个材料   │   │
│  │  上次研究: 3 天前  |  状态: 已完成                       │   │
│  │  材料: Rust Book, 播客 #123...                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 研究工作台 (三栏布局)

```
┌─────────────────────────────────────────────────────────────────┐
│  ← 返回研究列表    📓 AI 2026 趋势                    [设置] ⚙️  │
├─────────┬───────────────────────────────────────┬───────────────┤
│         │                                       │               │
│ 材料     │         研究内容 / 输出               │   对话区      │
│ 列表     │                                       │               │
│         │  ┌─────────────────────────────────┐  │  ┌─────────┐  │
│ ☑ GPT-5 │  │  📝 综合摘要                    │  │  │ 对话    │  │
│ ☑ Claude│  │  ────────────────────────────   │  │  │ 历史    │  │
│ ☐ Gemini│  │  ## 核心发现                    │  │  │         │  │
│         │  │  1. GPT-5 推理能力提升 300%     │  │  │ > 上下文│  │
│ [+添加] │  │  2. Claude 4 强调安全性...      │  │  │   已加载│  │
│         │  │  ...                            │  │  │         │  │
│─────────│  └─────────────────────────────────┘  │  └─────────┘  │
│         │                                       │               │
│ 输出     │  ┌─────────────────────────────────┐  │  ┌─────────┐  │
│         │  │  🗺️ 思维导图 (Markdown)          │  │  │         │  │
│ ☑ 摘要  │  │  ────────────────────────────   │  │  │ 输入框  │  │
│ ☑ 导图  │  │  - AI 2026                      │  │  │         │  │
│ ☐ 播客  │  │    - GPT-5                      │  │  │ [发送]  │  │
│         │  │      - 推理能力 +300%           │  │  │         │  │
│         │  │    - Claude 4                   │  │  └─────────┘  │
│         │  │      - 安全性优先               │  │               │
│         │  └─────────────────────────────────┘  │               │
│         │                                       │               │
│         │  [重新生成] [导出] [生成播客]          │               │
└─────────┴───────────────────────────────────────┴───────────────┘
```

### 4.4 资源详情页的研究入口

**现有按钮升级**：原"深入研究"按钮 → 新"研究"按钮

```
┌─────────────────────────────────────────────────────────────────┐
│  📄 GPT-5 发布，性能提升 300%                                    │
│  ────────────────────────────────────────────────────────────   │
│  ⭐ 评分: 92  |  📅 今天  |  来源: Hacker News                   │
│                                                                 │
│  摘要:                                                          │
│  OpenAI 今日发布 GPT-5，在推理能力上相比 GPT-4 提升 300%...      │
│                                                                 │
│  ────────────────────────────────────────────────────────────   │
│                                                                 │
│  [研究] ← 点击后弹出选择器                                       │
│                                                                 │
│  ┌─────────────────────────────────┐                           │
│  │  选择研究项目:                   │                           │
│  │                                  │                           │
│  │  ○ AI 2026 趋势 (3 个材料)       │                           │
│  │  ○ 投资笔记 (8 个材料)           │                           │
│  │  ● + 新建研究项目                │                           │
│  │    [项目名称: ___________ ]      │                           │
│  │                                  │                           │
│  │  [取消]            [加入并研究]  │                           │
│  └─────────────────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 渐进式研究工作流

```
流程 A: 从资源列表进入 (快速研究单资源)
──────────────────────────────────────
Signal 列表 → 点击资源 → 资源详情页 → [研究] → 选择/新建项目 → 研究工作台
                                                                    ↓
                                                            可继续添加材料
                                                                    ↓
                                                            多资源综合研究

流程 B: 从导航栏进入 (管理研究项目)
──────────────────────────────────────
导航栏 [研究] → 研究项目列表 → 选择项目 → 研究工作台
                    ↓
               [+ 新建研究]
                    ↓
              添加材料 → 开始研究
```

**研究过程**：

```
Step 1: 进入研究工作台
┌──────────────────────────────────────┐
│  📓 AI 2026 趋势                      │
│  ────────────────────────────────    │
│  材料:                               │
│  ☑ 📄 GPT-5 发布解读                  │
│  ☑ 📄 Claude 4 技术报告               │
│  ☐ 🎧 AI 播客 #420                    │
│                                      │
│  [+ 添加更多材料]                     │
│                                      │
│  ────────────────────────────────    │
│  生成:                               │
│  ☑ 结构化摘要                        │
│  ☑ 思维导图                          │
│  ☐ 播客                              │
│                                      │
│              [开始研究]               │
└──────────────────────────────────────┘
         ↓ 点击 [开始研究]

Step 2: AI 研究中 (实时进度)
┌──────────────────────────────────────┐
│  🤖 正在研究...                       │
│  ────────────────────────────────    │
│  ☑ 分析 GPT-5 发布解读                │
│  ☑ 分析 Claude 4 技术报告             │
│  ▶ 搜索相关背景资料...               │
│  ☐ 综合对比分析                       │
│  ☐ 生成结构化摘要                     │
│  ☐ 生成思维导图                       │
│                                      │
│  [暂停] [取消]                        │
└──────────────────────────────────────┘
         ↓ 完成后

Step 3: 查看结果 + 持续对话
┌──────────────────────────────────────┐
│  研究完成！                           │
│  ────────────────────────────────    │
│  📝 结构化摘要 ✅                      │
│  🗺️ 思维导图 ✅                        │
│                                      │
│  ────────────────────────────────    │
│  💬 有什么问题想深入了解？             │
│  ┌────────────────────────────────┐  │
│  │ 能详细解释 GPT-5 的推理提升吗？  │  │
│  └────────────────────────────────┘  │
│                          [发送]      │
└──────────────────────────────────────┘
         ↓ AI 基于研究上下文回答
         ↓ 可持续追问...
```

### 4.3 设计系统

延续 Signal Hunter 现有的微拟物设计 + Apple 级 Spring 动效：

- **卡片**: 三层阴影 + 渐变背景
- **动画**: Spring 物理引擎 (snappy/gentle/bouncy)
- **交互**: hover scale-[1.02], active scale-[0.97]
- **圆角**: 16px - 32px 大圆角

---

## 5. API 设计

### 5.1 新增 API 端点

```yaml
# 笔记本管理
POST   /api/notebooks              # 创建笔记本
GET    /api/notebooks              # 获取用户的所有笔记本
GET    /api/notebooks/{id}         # 获取笔记本详情
PUT    /api/notebooks/{id}         # 更新笔记本
DELETE /api/notebooks/{id}         # 删除笔记本

# 源材料管理
POST   /api/notebooks/{id}/sources        # 添加材料
GET    /api/notebooks/{id}/sources        # 获取笔记本的所有材料
DELETE /api/notebooks/{id}/sources/{sid}  # 删除材料
POST   /api/sources/upload                # 上传文件 (PDF/音频/视频)
POST   /api/sources/import-url            # 导入 URL

# 研究任务
POST   /api/notebooks/{id}/research       # 发起研究任务
GET    /api/notebooks/{id}/research/{rid} # 获取研究状态
POST   /api/notebooks/{id}/research/{rid}/cancel  # 取消研究

# 笔记管理
POST   /api/notebooks/{id}/notes          # 创建笔记
GET    /api/notebooks/{id}/notes          # 获取笔记列表
PUT    /api/notes/{id}                    # 更新笔记
DELETE /api/notes/{id}                    # 删除笔记

# 对话
POST   /api/notebooks/{id}/chat           # 发送消息 (SSE 流式响应)
GET    /api/notebooks/{id}/chat/sessions  # 获取对话历史
DELETE /api/chat/sessions/{sid}           # 删除对话

# 播客生成
POST   /api/notebooks/{id}/podcast        # 生成播客
GET    /api/podcasts/{id}                 # 获取播客详情
GET    /api/podcasts/{id}/audio           # 下载音频

# 搜索
POST   /api/search                        # 全局搜索 (全文 + 向量)

# 用户认证
POST   /api/auth/register                 # 注册
POST   /api/auth/login                    # 登录
POST   /api/auth/logout                   # 登出
GET    /api/auth/me                       # 获取当前用户信息
```

### 5.2 研究任务请求/响应

```python
# 请求
class ResearchRequest(BaseModel):
    task: str  # 研究任务描述
    source_ids: List[str]  # 要研究的材料 ID
    output_types: List[str] = ["summary", "mindmap"]  # 输出类型
    stream: bool = True  # 是否流式返回

# 流式响应 (SSE)
event: progress
data: {"step": "analyzing", "message": "正在分析 GPT-5 发布解读..."}

event: progress
data: {"step": "searching", "message": "搜索相关背景资料..."}

event: partial
data: {"type": "summary", "content": "## 核心发现\n1. GPT-5 在..."}

event: complete
data: {"research_id": "xxx", "outputs": {...}}
```

---

## 6. 开发路线图

### 6.1 Phase 0 - 基础设施 (2 周)

**目标**: 数据库扩展 + 存储设置

| 周 | 任务 |
|------|------|
| W1 | 数据库 schema 扩展 (笔记本/源材料/笔记表) |
| W2 | R2 存储配置 + 基础 API 框架 |

### 6.2 Phase 1 - MVP (6 周)

**目标**: 核心研究助手功能可用

| 周 | 任务 |
|------|------|
| W3-4 | 笔记本管理 + 材料导入 (URL/PDF) |
| W5-6 | DeepAgents 集成 (Kimi K2) + 基础研究功能 |
| W7 | 对话式研究 + UI 整合 |
| W8 | 测试 + 修复 + 部署 |

**MVP 交付物**:
- ✅ 笔记本 CRUD
- ✅ URL/PDF 导入
- ✅ 结构化摘要生成
- ✅ Markdown 思维导图
- ✅ 基础对话

### 6.3 Phase 2 - 多模态 + 播客 (4 周)

**目标**: 多模态处理 + 播客生成

| 周 | 任务 |
|------|------|
| W9-10 | 音频/视频转写 (听悟 API) |
| W11-12 | 播客生成功能 (CosyVoice TTS) |

**交付物**:
- ✅ 播客/音频导入并转写
- ✅ YouTube 视频导入
- ✅ 播客生成 (多角色对话)

### 6.4 Phase 3 - 高级功能 (4 周)

**目标**: 高级功能完善

| 周 | 任务 |
|------|------|
| W13-14 | 概念图/PPT 生成 |
| W15-16 | 向量搜索优化 + 性能调优 |

**交付物**:
- ✅ AI 生成概念图
- ✅ 跨笔记本搜索
- ✅ 性能优化

### 6.5 Phase 4-6 (后续迭代)

- L4 自主规划任务
- 原生 App (iOS/Android)
- 团队协作功能

### 6.6 Phase 7 - 用户认证 (可选，2 周)

> **注意**: 用户认证系统为可选功能，优先级最低。
> 初期可使用 API Key 或简单 Token 方式进行访问控制。

| 周 | 任务 |
|------|------|
| W-1 | 用户表设计 + 注册登录 API |
| W-2 | JWT 认证 + 权限控制 |

**交付物**:
- ✅ 用户注册/登录
- ✅ JWT 认证
- ✅ 资源权限隔离

---

## 7. 成本估算

### 7.1 API 成本 (每月)

| 服务 | 用量估算 | 单价 | 月成本 |
|------|---------|------|--------|
| Kimi K2 (Thinking) | 5M tokens | ¥0.008-0.032/1K | ¥40-160 |
| Kimi K2 (Turbo) | 5M tokens | ¥0.008-0.032/1K | ¥40-160 |
| 百炼嵌入 | 10M tokens | ¥0.0007/1K | ¥7 |
| Tavily Search | 1000 次 | $0.01/次 | $10 |
| 听悟 API | 10 小时音频 | ¥0.015/分钟 | ¥9 |
| CosyVoice TTS | 100K 字符 | ¥2/万字符 | ¥20 |
| **总计** | | | **~¥200-350/月** |

> **成本优势**: 使用国产 API (Kimi K2 + 百炼) 相比 OpenAI/ElevenLabs 成本降低 50%+。

### 7.2 基础设施

| 服务 | 规格 | 月成本 |
|------|------|--------|
| Railway (Backend) | Starter | $5 |
| Railway (PostgreSQL) | 1GB | $5 |
| Cloudflare Pages (Frontend) | Free | $0 |
| 文件存储 (R2/S3) | 10GB | $0.5 |
| **总计** | | **~$10.5/月** |

---

## 8. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| DeepAgents 学习曲线 | 开发延期 | 先用简化版，逐步深入 |
| LLM 成本超预期 | 预算超支 | 增加缓存、限制使用量 |
| 多模态处理性能 | 体验差 | 异步处理 + 进度反馈 |
| 用户体验割裂 | 用户流失 | 渐进式功能引入 |

---

## 9. 成功指标

| 指标 | 目标 (MVP) | 目标 (6个月) |
|------|------------|-------------|
| 笔记本创建数 | 10+ | 100+ |
| 材料导入数 | 50+ | 500+ |
| 研究任务数 | 20+ | 200+ |
| 对话轮次 | 100+ | 1000+ |
| 播客生成数 | 5+ | 50+ |

---

## 10. 附录

### 10.1 参考项目

| 项目 | 借鉴点 |
|------|--------|
| [Open Notebook](https://github.com/lfnovo/open-notebook) | 笔记本组织、多模态处理、播客生成 |
| [DeepAgents](https://github.com/langchain-ai/deepagents) | Agent 框架、任务规划、上下文管理 |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | 研究循环设计 |

### 10.2 技术文档

- [DeepAgents 文档](https://github.com/langchain-ai/deepagents)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Kimi K2 API 文档](https://platform.moonshot.cn/docs)
- [阿里云百炼文档](https://help.aliyun.com/document_detail/dashscope)
- [听悟 API 文档](https://help.aliyun.com/document_detail/tingwu)

---

**文档状态**: 待评审
**下一步**: 产品评审 → 技术方案细化 → 开发启动
