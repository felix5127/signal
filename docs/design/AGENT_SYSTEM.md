# Signal Hunter Agent 系统技术方案

> 版本: 1.1 | 日期: 2026-01-17 | 状态: 设计中

---

## 目录

1. [DeepAgents 集成架构](#1-deepagents-集成架构)
2. [Middleware 配置](#2-middleware-配置)
3. [Backend 实现](#3-backend-实现)
4. [Tools 设计](#4-tools-设计)
5. [Skills 设计](#5-skills-设计)
6. [代码示例](#6-代码示例)

---

## 1. DeepAgents 集成架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent Orchestration Layer                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Research Agent (主 Agent)                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│  │  │  Planning    │ │  Execution   │ │  Synthesis   │ │   Output   │  │   │
│  │  │  Module      │ │  Module      │ │  Module      │ │   Module   │  │   │
│  │  │ (write_todos)│ │ (tool_calls) │ │ (summarize)  │ │ (write)    │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│                    ┌────────────────┼────────────────┐                      │
│                    ▼                ▼                ▼                      │
│  ┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐       │
│  │    Chat Agent       │ │  Summary Agent  │ │   MindMap Agent     │       │
│  │   (对话式交互)       │ │   (摘要生成)     │ │   (思维导图)         │       │
│  └─────────────────────┘ └─────────────────┘ └─────────────────────┘       │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                           Middleware Stack                                   │
│  ┌──────────────┐ ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  TodoList    │ │  Summarization   │ │   Skills     │ │   Logging    │   │
│  │  Middleware  │ │   Middleware     │ │  Middleware  │ │  Middleware  │   │
│  └──────────────┘ └──────────────────┘ └──────────────┘ └──────────────┘   │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Tool Layer                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐                   │
│  │   tavily    │ │   vector    │ │   read    │  write   │                   │
│  │   _search   │ │   _search   │ │  _source  │ _output  │                   │
│  └─────────────┘ └─────────────┘ └──────────────────────┘                   │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                            Backend Layer                                     │
│                   ┌────────────────────────────────┐                        │
│                   │       PostgresBackend          │                        │
│                   │  (State + Memory + Checkpoints)│                        │
│                   └────────────────────────────────┘                        │
│                                     │                                        │
│           ┌─────────────────────────┼─────────────────────────┐             │
│           ▼                         ▼                         ▼             │
│    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐       │
│    │ agent_state │          │   memory    │          │ checkpoints │       │
│    │   (JSONB)   │          │   (JSONB)   │          │   (JSONB)   │       │
│    └─────────────┘          └─────────────┘          └─────────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   ▼                 ▼                 ▼
            ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
            │   Kimi K2   │  │   pgvector  │  │  External APIs  │
            │  (Moonshot) │  │  (embeddings) │  │     Tavily      │
            └─────────────┘  └─────────────┘  └─────────────────┘
```

### 1.2 Research Agent 设计

Research Agent 是系统核心，负责研究任务的规划、执行和输出。

#### 设计原则

```
┌────────────────────────────────────────────────────────────────┐
│                    Research Agent 核心循环                      │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │  PLAN    │───▶│ EXECUTE  │───▶│ REFLECT  │───▶│  OUTPUT  │ │
│   │ 任务规划  │    │ 工具执行  │    │ 反思检查  │    │ 生成输出  │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│        ▲                                              │        │
│        └──────────────────────────────────────────────┘        │
│                       (迭代优化)                                │
└────────────────────────────────────────────────────────────────┘
```

#### Agent 配置

```python
# ============================================================================
# Research Agent Configuration
# ============================================================================

RESEARCH_AGENT_CONFIG = {
    # LLM 配置 (Kimi K2 Thinking)
    "model": "kimi-k2-thinking-turbo",       # 主研究模型: 1T MoE, 推理模式
    "fallback_model": "kimi-k2-turbo-preview",  # 降级模型
    "max_tokens": 8192,
    "temperature": 1.0,                       # Thinking 模型推荐

    # 执行控制
    "recursion_limit": 50,           # 最大递归深度
    "max_iterations": 20,            # 单任务最大迭代
    "timeout_seconds": 600,          # 10 分钟超时

    # 上下文管理
    "context_limit": 250000,         # 256K 上下文 (预留 buffer)
    "summarization_threshold": 0.85, # 触发压缩的阈值

    # 成本控制
    "max_cost_per_task": 5.0,        # 单任务成本上限 (¥)
    "max_tool_calls": 30,            # 单任务工具调用上限
    "stream": True,                  # 必须启用流式
}
```

#### 系统提示词设计

```python
RESEARCH_SYSTEM_PROMPT = """
你是 Signal Hunter 研究助手，一个专业的技术情报分析 Agent。

## 核心能力
1. **深度阅读**: 仔细分析源材料，提取关键信息
2. **外部搜索**: 使用搜索工具获取背景知识和最新动态
3. **综合分析**: 对比、关联、总结多个信息源
4. **结构化输出**: 生成摘要、思维导图、研究报告

## 工作流程
1. 使用 write_todos 规划研究步骤
2. 使用 read_source 阅读源材料
3. 使用 tavily_search 搜索相关信息
4. 使用 vector_search 检索知识库
5. 综合分析并使用 write_output 生成结果

## 输出规范
- 摘要: 一句话总结 + 核心观点(3-5点) + 关键数据 + 结论
- 思维导图: Markdown 缩进列表，层级不超过 4 层
- 报告: 背景(200字) + 主要内容(500字) + 分析(300字) + 建议(200字)

## 注意事项
- 所有结论必须有来源支撑，标注引用
- 保持客观中立，区分事实与观点
- 优先使用最新的信息
"""
```

### 1.3 Chat Agent 设计

Chat Agent 负责基于研究上下文的对话式交互。

```python
# ============================================================================
# Chat Agent Configuration
# ============================================================================

CHAT_AGENT_CONFIG = {
    "model": "kimi-k2-turbo-preview",  # 高速版，用于对话
    "max_tokens": 4096,
    "temperature": 0.7,

    # 对话管理
    "max_history_turns": 20,         # 保留的历史轮次
    "context_window_messages": 10,   # 直接包含的消息数

    # 上下文增强
    "enable_rag": True,              # 启用向量检索增强
    "rag_top_k": 5,                  # 检索 Top K 结果
    "enable_citations": True,        # 启用引用标注
}

CHAT_SYSTEM_PROMPT = """
你是 Signal Hunter 研究助手，基于用户的研究项目进行对话。

## 上下文
当前研究项目包含以下材料:
{context_sources}

## 能力
1. 回答用户关于材料内容的问题
2. 提供深入解释和分析
3. 对比不同材料的观点
4. 建议进一步研究方向

## 规范
- 回答必须基于项目材料或搜索结果
- 使用 [来源] 格式标注引用
- 承认不确定性，不编造信息
- 主动提供深入探索的建议
"""
```

### 1.4 Sub-Agent 设计模式

Sub-Agent 采用专业化设计，每个 Sub-Agent 专注单一任务。

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Sub-Agent 委派模式                              │
│                                                                        │
│   Research Agent (Coordinator)                                         │
│        │                                                               │
│        │  delegate_task("summary", sources, instructions)              │
│        ▼                                                               │
│   ┌─────────────────────────────────────────────────────────────┐     │
│   │                    Sub-Agent Pool                            │     │
│   │                                                              │     │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │     │
│   │  │ SummaryAgent │  │ MindMapAgent │  │ PodcastAgent │       │     │
│   │  │              │  │              │  │              │       │     │
│   │  │ - 结构化摘要 │  │ - 层级思维图 │  │ - 对话脚本   │       │     │
│   │  │ - 观点提取   │  │ - 概念关联   │  │ - 多角色编排 │       │     │
│   │  │ - 金句标注   │  │ - 可视化结构 │  │ - 音频合成   │       │     │
│   │  └──────────────┘  └──────────────┘  └──────────────┘       │     │
│   │                                                              │     │
│   │  ┌──────────────┐  ┌──────────────┐                         │     │
│   │  │ SearchAgent  │  │ ReportAgent  │                         │     │
│   │  │              │  │              │                         │     │
│   │  │ - 多源搜索   │  │ - 长文写作   │                         │     │
│   │  │ - 结果聚合   │  │ - 章节组织   │                         │     │
│   │  │ - 可信度评估 │  │ - 引用管理   │                         │     │
│   │  └──────────────┘  └──────────────┘                         │     │
│   └─────────────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────────┘
```

#### Sub-Agent 配置模板

```python
SUB_AGENT_CONFIGS = {
    "summary": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 4096,
        "temperature": 0.7,
        "skill": "summarization/SKILL.md",
        "tools": ["read_source", "write_output"],
    },
    "mindmap": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 2048,
        "temperature": 0.7,
        "skill": "mindmap/SKILL.md",
        "tools": ["read_source", "write_output"],
    },
    "search": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 4096,
        "temperature": 0.7,
        "skill": "research/SKILL.md",
        "tools": ["tavily_search", "vector_search"],
    },
    "podcast": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 8192,
        "temperature": 0.8,     # 高温度，创意输出
        "skill": "podcast/SKILL.md",
        "tools": ["read_source", "write_output"],
    },
    "report": {
        "model": "kimi-k2-turbo-preview",
        "max_tokens": 8192,
        "temperature": 0.7,
        "skill": "research/SKILL.md",
        "tools": ["read_source", "tavily_search", "write_output"],
    },
}
```

---

## 2. Middleware 配置

### 2.1 Middleware Stack 架构

```
┌────────────────────────────────────────────────────────────────────┐
│                      Middleware Execution Flow                      │
│                                                                     │
│   User Message                                                      │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 1. LoggingMiddleware                                         │  │
│   │    - 记录请求/响应                                            │  │
│   │    - 性能监控                                                 │  │
│   │    - Token 统计                                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 2. SkillsMiddleware                                          │  │
│   │    - 加载 SKILL.md                                           │  │
│   │    - 注入系统提示词                                           │  │
│   │    - 工具集绑定                                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 3. TodoListMiddleware                                        │  │
│   │    - 任务规划 (write_todos)                                   │  │
│   │    - 进度追踪                                                 │  │
│   │    - 状态更新                                                 │  │
│   └─────────────────────────────────────────────────────────────┘  │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ 4. SummarizationMiddleware                                   │  │
│   │    - 上下文长度检测                                           │  │
│   │    - 智能压缩                                                 │  │
│   │    - 关键信息保留                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│        │                                                            │
│        ▼                                                            │
│   Agent Core Execution                                              │
│        │                                                            │
│        ▼                                                            │
│   Response                                                          │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 TodoListMiddleware

任务规划中间件，为 Agent 提供结构化任务管理能力。

```python
# ============================================================================
# TodoList Middleware Configuration
# ============================================================================

class TodoItem(BaseModel):
    """任务项数据结构"""
    id: str
    content: str                           # 任务描述 (祈使句)
    active_form: str                       # 进行时描述
    status: Literal["pending", "in_progress", "completed"]
    created_at: datetime
    completed_at: Optional[datetime] = None

class TodoListMiddlewareConfig(BaseModel):
    """中间件配置"""

    # 功能开关
    enabled: bool = True
    auto_create: bool = True               # 自动创建任务列表

    # 任务限制
    max_todos: int = 10                    # 最大任务数
    max_in_progress: int = 1               # 同时进行的任务数

    # 持久化
    persist_to_backend: bool = True        # 保存到 Backend

    # 工具配置
    tool_name: str = "write_todos"
    tool_description: str = "规划和更新任务列表"
```

#### TodoList 工具定义

```python
def create_todo_tool(config: TodoListMiddlewareConfig):
    """创建 TodoList 工具"""

    @tool
    def write_todos(
        todos: List[Dict[str, str]],
        reason: Optional[str] = None
    ) -> str:
        """
        规划或更新任务列表。

        Args:
            todos: 任务列表，每项包含:
                - content: 任务描述 (祈使句，如 "分析源材料")
                - active_form: 进行时描述 (如 "正在分析源材料")
                - status: pending / in_progress / completed
            reason: 更新原因

        Returns:
            当前任务列表状态

        Example:
            write_todos([
                {"content": "阅读源材料", "active_form": "正在阅读源材料", "status": "completed"},
                {"content": "搜索背景信息", "active_form": "正在搜索背景信息", "status": "in_progress"},
                {"content": "生成摘要", "active_form": "正在生成摘要", "status": "pending"},
            ])
        """
        # 实现逻辑
        pass

    return write_todos
```

### 2.3 SummarizationMiddleware

上下文压缩中间件，防止 Token 超限。

```python
# ============================================================================
# Summarization Middleware Configuration
# ============================================================================

class SummarizationMiddlewareConfig(BaseModel):
    """上下文压缩配置"""

    # 触发条件
    enabled: bool = True
    threshold_ratio: float = 0.85          # 占用比例阈值
    context_limit: int = 180000            # 上下文限制

    # 压缩策略
    strategy: Literal["truncate", "summarize", "hybrid"] = "hybrid"
    preserve_recent_turns: int = 3         # 保留最近轮次
    preserve_system_prompt: bool = True    # 保留系统提示词

    # 摘要模型
    summary_model: str = "kimi-k2-turbo-preview"
    summary_max_tokens: int = 2048

    # 压缩目标
    target_ratio: float = 0.5              # 压缩后目标比例
```

#### 压缩策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Context Compression Strategies                    │
│                                                                      │
│   Strategy: "truncate"                                               │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ [System Prompt] [Recent 3 turns] [Current Message]            │ │
│   │ 直接截断旧消息，保留最近内容                                     │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│   Strategy: "summarize"                                              │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ [System Prompt] [Summary of History] [Current Message]        │ │
│   │ 使用 LLM 压缩历史对话为摘要                                      │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│   Strategy: "hybrid" (推荐)                                          │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ [System Prompt] [Summary] [Recent 3 turns] [Current Message]  │ │
│   │ 结合截断和摘要，平衡效率和信息保留                                │ │
│   └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.4 SkillsMiddleware

技能加载中间件，动态注入 SKILL.md 定义的能力。

```python
# ============================================================================
# Skills Middleware Configuration
# ============================================================================

class SkillsMiddlewareConfig(BaseModel):
    """技能加载配置"""

    # 技能目录
    skills_dir: str = "./skills/"

    # 加载模式
    lazy_load: bool = True                 # 按需加载
    cache_skills: bool = True              # 缓存已加载技能

    # 技能验证
    validate_schema: bool = True           # 验证 SKILL.md 格式

    # 技能路径映射
    skill_paths: Dict[str, str] = {
        "research": "research/SKILL.md",
        "summarization": "summarization/SKILL.md",
        "mindmap": "mindmap/SKILL.md",
        "podcast": "podcast/SKILL.md",
    }
```

---

## 3. Backend 实现

### 3.1 PostgresBackend 设计

替代 FilesystemBackend，实现基于 PostgreSQL 的状态持久化。

```
┌────────────────────────────────────────────────────────────────────────┐
│                       PostgresBackend Architecture                      │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        PostgresBackend                           │  │
│   │                                                                  │  │
│   │  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐  │  │
│   │  │  StateManager │ │ MemoryManager │ │  CheckpointManager    │  │  │
│   │  │               │ │               │ │                       │  │  │
│   │  │ - get_state() │ │ - get_memory()│ │ - save_checkpoint()   │  │  │
│   │  │ - set_state() │ │ - add_memory()│ │ - load_checkpoint()   │  │  │
│   │  │ - delete()    │ │ - search()    │ │ - list_checkpoints()  │  │  │
│   │  └───────────────┘ └───────────────┘ └───────────────────────┘  │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                     │                                   │
│                                     ▼                                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        PostgreSQL                                │  │
│   │                                                                  │  │
│   │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │  │
│   │  │  agent_states   │ │  agent_memories │ │ agent_checkpoints│   │  │
│   │  │                 │ │                 │ │                  │   │  │
│   │  │ - session_id    │ │ - session_id    │ │ - checkpoint_id  │   │  │
│   │  │ - state (JSONB) │ │ - memories      │ │ - state_snapshot │   │  │
│   │  │ - updated_at    │ │ - embeddings    │ │ - created_at     │   │  │
│   │  └─────────────────┘ └─────────────────┘ └─────────────────┘   │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据库表设计

```sql
-- ============================================================================
-- Agent States Table
-- 存储 Agent 运行时状态
-- ============================================================================

CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,                    -- 关联 research_task / chat_session
    agent_type VARCHAR(50) NOT NULL,             -- research / chat / summary / mindmap

    -- 状态数据
    state JSONB NOT NULL DEFAULT '{}',
    messages JSONB NOT NULL DEFAULT '[]',        -- 消息历史
    todos JSONB DEFAULT '[]',                    -- 任务列表

    -- 元数据
    model_name VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    tool_calls INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 约束
    UNIQUE(session_id, agent_type)
);

CREATE INDEX idx_agent_states_session ON agent_states(session_id);
CREATE INDEX idx_agent_states_type ON agent_states(agent_type);

-- ============================================================================
-- Agent Memories Table
-- 存储 Agent 长期记忆 (带向量索引)
-- ============================================================================

CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,

    -- 记忆内容
    memory_type VARCHAR(50) NOT NULL,            -- fact / insight / decision / summary
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- 向量嵌入 (用于相似性搜索)
    embedding vector(3072),

    -- 重要性和时效性
    importance_score FLOAT DEFAULT 0.5,
    decay_factor FLOAT DEFAULT 1.0,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_memories_session ON agent_memories(session_id);
CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_agent_memories_vector ON agent_memories
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- Agent Checkpoints Table
-- 存储 Agent 检查点 (支持恢复和回滚)
-- ============================================================================

CREATE TABLE agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    checkpoint_name VARCHAR(255),

    -- 完整状态快照
    state_snapshot JSONB NOT NULL,
    messages_snapshot JSONB NOT NULL,
    todos_snapshot JSONB,

    -- 触发信息
    trigger_type VARCHAR(50),                    -- manual / auto / error
    trigger_reason TEXT,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_checkpoints_session ON agent_checkpoints(session_id);
CREATE INDEX idx_agent_checkpoints_created ON agent_checkpoints(created_at DESC);
```

### 3.3 状态持久化策略

```python
# ============================================================================
# Persistence Strategy Configuration
# ============================================================================

class PersistenceConfig(BaseModel):
    """持久化策略配置"""

    # 自动保存
    auto_save: bool = True
    save_interval_seconds: int = 30            # 定时保存间隔
    save_on_tool_call: bool = True             # 工具调用后保存
    save_on_message: bool = False              # 每条消息后保存 (高频)

    # 检查点
    checkpoint_on_complete: bool = True        # 任务完成时创建检查点
    checkpoint_on_error: bool = True           # 错误时创建检查点
    max_checkpoints_per_session: int = 10      # 每会话最大检查点数

    # 清理策略
    state_ttl_hours: int = 168                 # 状态保留时间 (7天)
    memory_ttl_hours: int = 720                # 记忆保留时间 (30天)
    auto_cleanup: bool = True


class PostgresBackend:
    """
    PostgreSQL Backend 实现

    职责:
      - 状态管理 (CRUD)
      - 记忆存储 (带向量搜索)
      - 检查点管理 (恢复/回滚)
    """

    def __init__(self, db_session: Session, config: PersistenceConfig):
        self.db = db_session
        self.config = config

    # ========================================================================
    # State Operations
    # ========================================================================

    async def get_state(self, session_id: str, agent_type: str) -> Optional[Dict]:
        """获取 Agent 状态"""
        pass

    async def set_state(self, session_id: str, agent_type: str, state: Dict):
        """保存 Agent 状态"""
        pass

    async def delete_state(self, session_id: str, agent_type: str):
        """删除 Agent 状态"""
        pass

    # ========================================================================
    # Memory Operations
    # ========================================================================

    async def add_memory(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        embedding: Optional[List[float]] = None,
        importance: float = 0.5
    ):
        """添加记忆"""
        pass

    async def search_memories(
        self,
        session_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """向量搜索相关记忆"""
        pass

    async def get_recent_memories(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取最近记忆"""
        pass

    # ========================================================================
    # Checkpoint Operations
    # ========================================================================

    async def save_checkpoint(
        self,
        session_id: str,
        name: Optional[str] = None,
        trigger_type: str = "manual",
        trigger_reason: Optional[str] = None
    ) -> str:
        """创建检查点"""
        pass

    async def load_checkpoint(self, checkpoint_id: str) -> Dict:
        """加载检查点"""
        pass

    async def list_checkpoints(self, session_id: str) -> List[Dict]:
        """列出所有检查点"""
        pass

    async def rollback_to_checkpoint(self, checkpoint_id: str):
        """回滚到检查点"""
        pass
```

---

## 4. Tools 设计

### 4.1 工具架构

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Tool Architecture                             │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                     Search Tools (外部搜索)                       │  │
│   │                                                                  │  │
│   │  ┌─────────────┐  ┌─────────────────────┐                       │  │
│   │  │   tavily    │  │      vector         │                       │  │
│   │  │   _search   │  │      _search        │                       │  │
│   │  │             │  │                     │                       │  │
│   │  │ 快速网络搜索 │  │   本地知识库检索     │                       │  │
│   │  │ 返回摘要    │  │   语义相似度匹配     │                       │  │
│   │  └─────────────┘  └─────────────────────┘                       │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                      I/O Tools (读写操作)                         │  │
│   │                                                                  │  │
│   │  ┌────────────────────────────┐  ┌────────────────────────────┐ │  │
│   │  │       read_source          │  │       write_output         │ │  │
│   │  │                            │  │                            │ │  │
│   │  │ 读取研究材料:               │  │ 写入研究输出:               │ │  │
│   │  │ - 源材料全文                │  │ - 摘要                     │ │  │
│   │  │ - 向量分块                  │  │ - 思维导图                 │ │  │
│   │  │ - 元数据                    │  │ - 研究报告                 │ │  │
│   │  └────────────────────────────┘  └────────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Agent Tools (Agent 协作)                       │  │
│   │                                                                  │  │
│   │  ┌────────────────────────────────────────────────────────────┐ │  │
│   │  │                    delegate_task                            │ │  │
│   │  │                                                             │ │  │
│   │  │  委派任务给专业 Sub-Agent:                                   │ │  │
│   │  │  - summary: 摘要生成                                        │ │  │
│   │  │  - mindmap: 思维导图                                        │ │  │
│   │  │  - search: 深度搜索                                         │ │  │
│   │  │  - podcast: 播客脚本                                        │ │  │
│   │  └────────────────────────────────────────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 tavily_search

快速网络搜索工具。

```python
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class TavilySearchResult(BaseModel):
    """搜索结果"""
    title: str
    url: str
    snippet: str
    score: float

@tool
def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> List[TavilySearchResult]:
    """
    使用 Tavily API 进行网络搜索。

    Args:
        query: 搜索查询词
        max_results: 最大返回结果数 (1-10)
        search_depth: 搜索深度 ("basic" 或 "advanced")
        include_domains: 仅搜索这些域名
        exclude_domains: 排除这些域名

    Returns:
        搜索结果列表，每个结果包含标题、URL、摘要和相关度评分

    Example:
        results = tavily_search("GPT-5 发布新特性", max_results=5)
    """
    from tavily import TavilyClient

    client = TavilyClient(api_key=config.tavily_api_key)

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
    )

    return [
        TavilySearchResult(
            title=r["title"],
            url=r["url"],
            snippet=r["content"],
            score=r.get("score", 0.0),
        )
        for r in response["results"]
    ]
```

### 4.3 vector_search

本地向量知识库检索工具。

```python
from typing import List, Optional
from pydantic import BaseModel

class VectorSearchResult(BaseModel):
    """向量检索结果"""
    source_id: str
    source_title: str
    chunk_text: str
    similarity_score: float
    metadata: dict

@tool
def vector_search(
    query: str,
    project_id: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    source_ids: Optional[List[str]] = None,
) -> List[VectorSearchResult]:
    """
    在项目知识库中进行向量相似度搜索。

    Args:
        query: 搜索查询
        project_id: 研究项目 ID
        top_k: 返回最相似的 K 个结果
        similarity_threshold: 最低相似度阈值 (0-1)
        source_ids: 可选，限制在特定源材料中搜索

    Returns:
        相似度排序的检索结果列表

    Example:
        results = vector_search(
            "大模型推理能力提升",
            project_id="xxx",
            top_k=5
        )
    """
    from openai import OpenAI
    from sqlalchemy import text

    # 1. 生成查询向量
    client = OpenAI(api_key=config.openai_api_key)
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=query,
        dimensions=3072,
    )
    query_embedding = response.data[0].embedding

    # 2. 向量搜索
    sql = text("""
        SELECT
            se.source_id,
            rs.title as source_title,
            se.chunk_text,
            1 - (se.embedding <=> :query_embedding) as similarity_score,
            rs.metadata
        FROM source_embeddings se
        JOIN research_sources rs ON se.source_id = rs.id
        WHERE rs.project_id = :project_id
            AND (:source_ids IS NULL OR se.source_id = ANY(:source_ids))
            AND 1 - (se.embedding <=> :query_embedding) >= :threshold
        ORDER BY se.embedding <=> :query_embedding
        LIMIT :top_k
    """)

    results = db.execute(sql, {
        "query_embedding": query_embedding,
        "project_id": project_id,
        "source_ids": source_ids,
        "threshold": similarity_threshold,
        "top_k": top_k,
    }).fetchall()

    return [
        VectorSearchResult(
            source_id=r.source_id,
            source_title=r.source_title,
            chunk_text=r.chunk_text,
            similarity_score=r.similarity_score,
            metadata=r.metadata or {},
        )
        for r in results
    ]
```

### 4.4 read_source

读取源材料工具。

```python
from typing import Optional, Literal
from pydantic import BaseModel

class SourceContent(BaseModel):
    """源材料内容"""
    source_id: str
    title: str
    source_type: str               # url / pdf / audio / video / text
    full_text: str
    summary: Optional[str]
    metadata: dict
    chunk_count: int               # 分块数量

@tool
def read_source(
    source_id: str,
    content_type: Literal["full", "summary", "chunks"] = "full",
    chunk_indices: Optional[List[int]] = None,
) -> SourceContent:
    """
    读取研究项目中的源材料。

    Args:
        source_id: 源材料 ID
        content_type: 读取类型
            - "full": 完整内容
            - "summary": 仅摘要
            - "chunks": 指定分块
        chunk_indices: 当 content_type="chunks" 时，指定分块索引列表

    Returns:
        源材料内容，包含标题、类型、文本、摘要和元数据

    Example:
        # 读取完整内容
        source = read_source("xxx", content_type="full")

        # 只读取摘要
        source = read_source("xxx", content_type="summary")

        # 读取特定分块
        source = read_source("xxx", content_type="chunks", chunk_indices=[0, 1, 2])
    """
    from sqlalchemy import text

    # 1. 获取源材料基本信息
    source = db.query(ResearchSource).filter(ResearchSource.id == source_id).first()

    if not source:
        raise ValueError(f"Source not found: {source_id}")

    # 2. 根据 content_type 获取内容
    if content_type == "full":
        full_text = source.full_text
    elif content_type == "summary":
        full_text = source.summary or source.full_text[:500]
    elif content_type == "chunks":
        chunks = db.query(SourceEmbedding).filter(
            SourceEmbedding.source_id == source_id,
            SourceEmbedding.chunk_index.in_(chunk_indices or []),
        ).order_by(SourceEmbedding.chunk_index).all()
        full_text = "\n\n".join([c.chunk_text for c in chunks])

    # 3. 获取分块数量
    chunk_count = db.query(SourceEmbedding).filter(
        SourceEmbedding.source_id == source_id
    ).count()

    return SourceContent(
        source_id=source_id,
        title=source.title,
        source_type=source.source_type,
        full_text=full_text,
        summary=source.summary,
        metadata=source.metadata or {},
        chunk_count=chunk_count,
    )
```

### 4.5 write_output

写入研究输出工具。

```python
from typing import Optional, Literal, List
from pydantic import BaseModel

class OutputResult(BaseModel):
    """输出结果"""
    output_id: str
    output_type: str
    title: str
    file_path: Optional[str]
    created_at: datetime

@tool
def write_output(
    project_id: str,
    output_type: Literal["summary", "mindmap", "report", "podcast_script"],
    title: str,
    content: str,
    source_refs: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> OutputResult:
    """
    将研究输出保存到项目中。

    Args:
        project_id: 研究项目 ID
        output_type: 输出类型
            - "summary": 结构化摘要
            - "mindmap": 思维导图 (Markdown 格式)
            - "report": 研究报告
            - "podcast_script": 播客脚本
        title: 输出标题
        content: 输出内容 (Markdown 格式)
        source_refs: 引用的源材料 ID 列表
        metadata: 额外元数据

    Returns:
        创建的输出记录信息

    Example:
        # 保存摘要
        result = write_output(
            project_id="xxx",
            output_type="summary",
            title="AI 2026 趋势分析摘要",
            content="## 核心发现\n1. GPT-5 推理能力提升 300%...",
            source_refs=["source_id_1", "source_id_2"],
        )
    """
    from datetime import datetime
    import uuid

    # 1. 创建输出记录
    output = ResearchOutput(
        id=str(uuid.uuid4()),
        project_id=project_id,
        output_type=output_type,
        title=title,
        content=content,
        content_format="markdown",
        source_refs=source_refs or [],
        metadata=metadata or {},
        created_at=datetime.now(),
    )

    db.add(output)
    db.commit()

    # 2. 更新项目统计
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if project:
        project.output_count += 1
        project.updated_at = datetime.now()
        db.commit()

    return OutputResult(
        output_id=output.id,
        output_type=output_type,
        title=title,
        file_path=None,
        created_at=output.created_at,
    )
```

---

## 5. Skills 设计

### 5.1 Skill 文件格式规范

```yaml
# SKILL.md 标准格式

---
name: skill-name                    # 技能唯一标识
description: 技能描述                # 简短描述
version: "1.0"                      # 版本号
author: Signal Hunter               # 作者
tags: [research, analysis]          # 标签
---

## 技能说明

详细描述技能的用途和适用场景。

## 输入规范

描述输入数据的格式要求。

## 输出规范

描述输出数据的格式要求。

## 工作流程

1. 步骤一
2. 步骤二
3. ...

## 示例

提供使用示例。
```

### 5.2 research/SKILL.md

```markdown
---
name: deep-research
description: 深度研究材料，生成结构化分析
version: "1.0"
author: Signal Hunter
tags: [research, analysis, synthesis]
---

## 技能说明

深度研究技能用于分析多个源材料，提取关键信息，结合外部搜索，生成结构化的研究输出。

## 输入规范

- 源材料列表 (1-10 个)
- 研究问题或目标
- 输出类型偏好 (摘要/导图/报告)

## 输出规范

根据请求生成:
- **结构化摘要**: 一句话总结 + 核心观点 + 关键数据 + 结论
- **思维导图**: Markdown 缩进列表，层级不超过 4 层
- **研究报告**: 背景 + 主要内容 + 分析评论 + 总结建议

## 工作流程

```
1. 任务规划
   ├── 分析研究目标
   ├── 识别信息需求
   └── 制定研究步骤 (write_todos)

2. 材料阅读
   ├── 逐一阅读源材料 (read_source)
   ├── 提取关键概念和数据
   └── 标记不明确或需要深入的点

3. 外部搜索
   ├── 针对知识空白进行搜索 (tavily_search)
   └── 检索项目知识库 (vector_search)

4. 综合分析
   ├── 对比不同来源的观点
   ├── 识别共识和分歧
   └── 形成综合结论

5. 输出生成
   ├── 按指定格式生成输出
   ├── 添加引用和来源标注
   └── 保存到项目 (write_output)
```

## 输出格式示例

### 结构化摘要

```markdown
# [主题名称]

## 一句话总结
[30字以内的核心要点]

## 核心观点
1. [观点1] — 来源: [Source A]
2. [观点2] — 来源: [Source B]
3. [观点3] — 来源: [搜索结果]

## 关键数据
- [数据点1]: [具体数值或趋势]
- [数据点2]: [具体数值或趋势]

## 结论与启发
[2-3 段总结，包含对用户的建议]
```

### 思维导图

```markdown
# [主题名称]

- 主题
  - 子主题 A
    - 要点 1
    - 要点 2
  - 子主题 B
    - 要点 3
      - 细节 a
      - 细节 b
    - 要点 4
  - 子主题 C
    - 要点 5
```

## 注意事项

- 所有结论必须有来源支撑
- 区分事实陈述和主观分析
- 优先使用最新的信息
- 承认不确定性，不编造信息
```

### 5.3 summarization/SKILL.md

```markdown
---
name: summarization
description: 生成结构化内容摘要
version: "1.0"
author: Signal Hunter
tags: [summary, extraction, nlp]
---

## 技能说明

摘要技能专注于从长文本中提取关键信息，生成不同长度和格式的结构化摘要。

## 输入规范

- 源材料 (单个或多个)
- 摘要长度偏好 (简短/标准/详细)
- 关注重点 (可选)

## 输出规范

### 简短摘要 (50 字)
一句话概括核心内容。

### 标准摘要 (200-300 字)
```markdown
## 概要
[1-2 句核心概括]

## 要点
- 要点 1
- 要点 2
- 要点 3

## 关键数据
- [数据点]
```

### 详细摘要 (500-800 字)
```markdown
## 背景
[100 字背景介绍]

## 核心内容
[200-300 字主要内容]

## 观点与分析
1. [观点 1 + 分析]
2. [观点 2 + 分析]

## 关键引用
> "引用原文" — 来源

## 总结
[100 字结论]
```

## 工作流程

```
1. 内容理解
   ├── 阅读完整材料
   ├── 识别文章类型 (新闻/论文/博客/报告)
   └── 确定核心主题

2. 信息提取
   ├── 提取核心论点
   ├── 标记关键数据
   ├── 识别精彩引用
   └── 注意作者立场

3. 结构组织
   ├── 按重要性排序
   ├── 分类组织信息
   └── 建立逻辑关联

4. 摘要生成
   ├── 按模板生成
   ├── 控制字数
   └── 确保完整性
```

## 质量标准

- **准确性**: 摘要必须忠实反映原文
- **完整性**: 覆盖主要观点，不遗漏关键信息
- **简洁性**: 用最少的字数传达最多的信息
- **可读性**: 结构清晰，易于快速浏览
```

### 5.4 mindmap/SKILL.md

```markdown
---
name: mindmap
description: 生成结构化思维导图
version: "1.0"
author: Signal Hunter
tags: [mindmap, structure, visualization]
---

## 技能说明

思维导图技能将复杂信息组织成层级结构，便于理解和记忆。输出 Markdown 格式，支持转换为可视化导图。

## 输入规范

- 源材料 (支持多个)
- 导图深度偏好 (2-4 层)
- 关注维度 (可选)

## 输出规范

### Markdown 思维导图格式

```markdown
# [中心主题]

- 一级主题 A
  - 二级主题 A1
    - 三级要点 A1a
    - 三级要点 A1b
  - 二级主题 A2
- 一级主题 B
  - 二级主题 B1
  - 二级主题 B2
    - 三级要点 B2a
```

### 结构规范

- **层级限制**: 最多 4 层 (中心 + 3 层子节点)
- **每层节点数**: 建议 3-7 个
- **节点文字**: 简洁明了，10 字以内

## 工作流程

```
1. 主题识别
   ├── 确定中心主题
   └── 识别主要维度

2. 结构规划
   ├── 确定一级分支 (3-7 个)
   ├── 规划二级内容
   └── 控制层级深度

3. 内容填充
   ├── 提取关键概念
   ├── 建立层级关系
   └── 简化节点文字

4. 优化调整
   ├── 检查逻辑一致性
   ├── 平衡分支数量
   └── 确保覆盖完整
```

## 组织维度建议

根据内容类型选择组织维度:

| 内容类型 | 推荐维度 |
|---------|---------|
| 技术文章 | 问题-方案-实现-效果 |
| 产品分析 | 定位-功能-优势-不足 |
| 研究论文 | 背景-方法-结果-结论 |
| 新闻报道 | 事件-原因-影响-展望 |
| 教程指南 | 准备-步骤-注意事项-进阶 |

## 示例输出

```markdown
# GPT-5 技术解读

- 核心能力
  - 推理能力
    - 数学推理 +300%
    - 逻辑推理 +250%
  - 长文理解
    - 200K 上下文
    - 跨文档推理
  - 工具使用
    - 原生函数调用
    - 多工具编排

- 技术架构
  - 模型规模
    - 参数量 (未公开)
    - MoE 架构
  - 训练方法
    - RLHF 改进
    - 新型对齐技术

- 应用场景
  - 企业级
    - 文档分析
    - 代码生成
  - 消费级
    - 智能助手
    - 内容创作

- 竞争格局
  - 与 Claude 4 对比
  - 与 Gemini 2 对比
  - 开源模型追赶
```

## 质量标准

- **层级清晰**: 父子关系明确
- **覆盖全面**: 主要内容无遗漏
- **节点简洁**: 易于快速浏览
- **逻辑一致**: 同层级内容平行
```

---

## 6. 代码示例

### 6.1 完整 Agent 服务实现

```python
# ============================================================================
# backend/app/agents/research_agent_service.py
#
# [INPUT]: 依赖 langchain, langgraph, openai, app/config
# [OUTPUT]: 对外提供 ResearchAgentService 类
# [POS]: agents/ 核心服务，被 API 层调用
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
# ============================================================================

from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver
from pydantic import BaseModel, Field

from app.config import config
from app.database import SessionLocal
from app.models.research import ResearchProject, ResearchSource, ResearchOutput


# ============================================================================
# Agent State Definition
# ============================================================================

class ResearchState(BaseModel):
    """Research Agent 状态定义"""

    # 消息历史
    messages: List[Dict] = Field(default_factory=list)

    # 任务追踪
    todos: List[Dict] = Field(default_factory=list)
    current_todo_index: int = 0

    # 上下文
    project_id: str = ""
    source_ids: List[str] = Field(default_factory=list)

    # 输出
    outputs: List[Dict] = Field(default_factory=list)

    # 统计
    tokens_used: int = 0
    tool_calls: int = 0

    # 控制
    should_end: bool = False


# ============================================================================
# Tools Implementation
# ============================================================================

def create_tools(db_session):
    """创建工具集"""

    @tool
    def write_todos(
        todos: List[Dict[str, str]],
        reason: Optional[str] = None
    ) -> str:
        """
        规划或更新任务列表。

        Args:
            todos: 任务列表，每项包含:
                - content: 任务描述 (祈使句)
                - active_form: 进行时描述
                - status: pending / in_progress / completed
            reason: 更新原因
        """
        # 任务验证和处理
        validated_todos = []
        for todo in todos:
            validated_todos.append({
                "id": str(uuid.uuid4()),
                "content": todo.get("content", ""),
                "active_form": todo.get("active_form", ""),
                "status": todo.get("status", "pending"),
                "created_at": datetime.now().isoformat(),
            })

        return f"任务列表已更新: {len(validated_todos)} 项任务"

    @tool
    def tavily_search(
        query: str,
        max_results: int = 5,
    ) -> List[Dict]:
        """
        使用 Tavily API 进行网络搜索。

        Args:
            query: 搜索查询词
            max_results: 最大返回结果数
        """
        from tavily import TavilyClient

        client = TavilyClient(api_key=config.tavily_api_key)
        response = client.search(query=query, max_results=max_results)

        return [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["content"][:500],
            }
            for r in response["results"]
        ]

    @tool
    def vector_search(
        query: str,
        project_id: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        在项目知识库中进行向量相似度搜索。

        Args:
            query: 搜索查询
            project_id: 研究项目 ID
            top_k: 返回结果数量
        """
        from sqlalchemy import text
        from app.services.embedding_service import get_embedding

        # 生成查询向量 (百炼 通用文本向量-v3)
        query_embedding = get_embedding(query, dimensions=512)

        # 向量搜索
        sql = text("""
            SELECT
                se.source_id,
                rs.title,
                se.chunk_text,
                1 - (se.embedding <=> :embedding) as score
            FROM source_embeddings se
            JOIN research_sources rs ON se.source_id = rs.id
            WHERE rs.project_id = :project_id
            ORDER BY se.embedding <=> :embedding
            LIMIT :top_k
        """)

        results = db_session.execute(sql, {
            "embedding": str(query_embedding),
            "project_id": project_id,
            "top_k": top_k,
        }).fetchall()

        return [
            {
                "source_id": r.source_id,
                "title": r.title,
                "content": r.chunk_text,
                "score": float(r.score),
            }
            for r in results
        ]

    @tool
    def read_source(source_id: str) -> Dict:
        """
        读取研究项目中的源材料。

        Args:
            source_id: 源材料 ID
        """
        source = db_session.query(ResearchSource).filter(
            ResearchSource.id == source_id
        ).first()

        if not source:
            return {"error": f"Source not found: {source_id}"}

        return {
            "source_id": source_id,
            "title": source.title,
            "source_type": source.source_type,
            "full_text": source.full_text,
            "summary": source.summary,
        }

    @tool
    def write_output(
        project_id: str,
        output_type: str,
        title: str,
        content: str,
        source_refs: Optional[List[str]] = None,
    ) -> Dict:
        """
        将研究输出保存到项目中。

        Args:
            project_id: 研究项目 ID
            output_type: 输出类型 (summary/mindmap/report)
            title: 输出标题
            content: 输出内容 (Markdown 格式)
            source_refs: 引用的源材料 ID 列表
        """
        output = ResearchOutput(
            id=str(uuid.uuid4()),
            project_id=project_id,
            output_type=output_type,
            title=title,
            content=content,
            source_refs=source_refs or [],
            created_at=datetime.now(),
        )

        db_session.add(output)
        db_session.commit()

        return {
            "output_id": output.id,
            "output_type": output_type,
            "title": title,
            "status": "saved",
        }

    return [write_todos, tavily_search, vector_search, read_source, write_output]


# ============================================================================
# Research Agent Service
# ============================================================================

class ResearchAgentService:
    """
    研究 Agent 服务

    职责:
      - 创建和管理 Research Agent
      - 执行研究任务 (支持流式输出)
      - 状态持久化 (PostgresBackend)
    """

    def __init__(self):
        self.db = SessionLocal()
        self.tools = create_tools(self.db)

        # 初始化 LLM (Kimi K2 Thinking)
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(
            model="kimi-k2-thinking-turbo",
            api_key=config.moonshot_api_key,
            base_url="https://api.moonshot.cn/v1",
            max_tokens=8192,
            temperature=1.0,  # Thinking 模型推荐
            streaming=True,
        )

        # 绑定工具
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # 初始化 PostgreSQL Checkpointer
        self.checkpointer = PostgresSaver.from_conn_string(
            config.database_url
        )

        # 构建 Graph
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建 LangGraph 工作流"""

        # 定义节点函数
        def call_model(state: ResearchState) -> ResearchState:
            """调用模型"""
            messages = [
                SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
                *[self._dict_to_message(m) for m in state.messages],
            ]

            response = self.llm_with_tools.invoke(messages)

            state.messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": getattr(response, "tool_calls", []),
            })

            return state

        def should_continue(state: ResearchState) -> str:
            """判断是否继续"""
            last_message = state.messages[-1]

            # 如果有工具调用，继续
            if last_message.get("tool_calls"):
                return "tools"

            return "end"

        # 构建 Graph
        workflow = StateGraph(ResearchState)

        # 添加节点
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(self.tools))

        # 添加边
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END,
            }
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=self.checkpointer)

    async def research(
        self,
        project_id: str,
        task: str,
        source_ids: List[str],
        output_types: List[str],
        stream: bool = True,
    ) -> AsyncGenerator[Dict, None]:
        """
        执行研究任务

        Args:
            project_id: 研究项目 ID
            task: 研究任务描述
            source_ids: 源材料 ID 列表
            output_types: 期望的输出类型
            stream: 是否流式返回

        Yields:
            进度和结果事件
        """

        # 1. 构建初始消息
        sources_summary = await self._get_sources_summary(source_ids)

        initial_message = f"""
## 研究任务
{task}

## 源材料
{sources_summary}

## 期望输出
{', '.join(output_types)}

请开始研究，首先使用 write_todos 规划研究步骤。
"""

        # 2. 创建初始状态
        initial_state = ResearchState(
            messages=[{"role": "user", "content": initial_message}],
            project_id=project_id,
            source_ids=source_ids,
        )

        # 3. 创建线程配置 (用于持久化)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # 4. 执行并流式返回
        yield {"event": "start", "task_id": thread_id}

        async for event in self.graph.astream(initial_state, config):
            # 解析事件类型
            if "agent" in event:
                agent_output = event["agent"]

                # 检查是否有任务更新
                if agent_output.todos:
                    yield {
                        "event": "progress",
                        "todos": agent_output.todos,
                    }

                # 检查是否有输出
                if agent_output.outputs:
                    for output in agent_output.outputs:
                        yield {
                            "event": "partial",
                            "type": output["type"],
                            "content": output["content"],
                        }

            elif "tools" in event:
                tool_output = event["tools"]
                yield {
                    "event": "tool_call",
                    "tool": tool_output.get("tool_name"),
                    "result": tool_output.get("result"),
                }

        # 5. 返回完成事件
        final_state = await self.graph.aget_state(config)
        yield {
            "event": "complete",
            "task_id": thread_id,
            "outputs": final_state.values.get("outputs", []),
            "tokens_used": final_state.values.get("tokens_used", 0),
        }

    async def chat(
        self,
        project_id: str,
        message: str,
        session_id: Optional[str] = None,
        context_source_ids: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        对话式研究

        Args:
            project_id: 研究项目 ID
            message: 用户消息
            session_id: 会话 ID (可选，新会话则创建)
            context_source_ids: 上下文源材料 ID

        Yields:
            Token 流和完成事件
        """

        # 1. 获取或创建会话
        thread_id = session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # 2. 构建上下文
        context = ""
        if context_source_ids:
            context = await self._get_sources_summary(context_source_ids)

        # 3. 构建消息
        user_message = f"""
{f'## 参考材料\n{context}\n' if context else ''}

{message}
"""

        # 4. 流式调用
        yield {"event": "start", "session_id": thread_id}

        full_response = ""
        async for chunk in self.llm.astream([
            SystemMessage(content=CHAT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]):
            if chunk.content:
                full_response += chunk.content
                yield {
                    "event": "token",
                    "content": chunk.content,
                }

        # 5. 保存到会话历史
        # (实现省略)

        yield {
            "event": "done",
            "full_content": full_response,
            "session_id": thread_id,
        }

    async def _get_sources_summary(self, source_ids: List[str]) -> str:
        """获取源材料摘要"""
        summaries = []
        for source_id in source_ids:
            source = self.db.query(ResearchSource).filter(
                ResearchSource.id == source_id
            ).first()
            if source:
                summaries.append(f"- **{source.title}**: {source.summary or '(无摘要)'}")

        return "\n".join(summaries)

    def _dict_to_message(self, msg: Dict):
        """字典转消息对象"""
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)

        return HumanMessage(content=content)


# ============================================================================
# System Prompts
# ============================================================================

RESEARCH_SYSTEM_PROMPT = """
你是 Signal Hunter 研究助手，一个专业的技术情报分析 Agent。

## 核心能力
1. **深度阅读**: 仔细分析源材料，提取关键信息
2. **外部搜索**: 使用搜索工具获取背景知识和最新动态
3. **综合分析**: 对比、关联、总结多个信息源
4. **结构化输出**: 生成摘要、思维导图、研究报告

## 工作流程
1. 使用 write_todos 规划研究步骤
2. 使用 read_source 阅读源材料
3. 使用 tavily_search 搜索相关信息
4. 使用 vector_search 检索知识库
5. 综合分析并使用 write_output 生成结果

## 输出规范
- 摘要: 一句话总结 + 核心观点(3-5点) + 关键数据 + 结论
- 思维导图: Markdown 缩进列表，层级不超过 4 层
- 报告: 背景(200字) + 主要内容(500字) + 分析(300字) + 建议(200字)

## 注意事项
- 所有结论必须有来源支撑，标注引用
- 保持客观中立，区分事实与观点
- 优先使用最新的信息
"""

CHAT_SYSTEM_PROMPT = """
你是 Signal Hunter 研究助手，基于用户的研究项目进行对话。

## 能力
1. 回答用户关于材料内容的问题
2. 提供深入解释和分析
3. 对比不同材料的观点
4. 建议进一步研究方向

## 规范
- 回答必须基于项目材料或搜索结果
- 使用 [来源] 格式标注引用
- 承认不确定性，不编造信息
- 主动提供深入探索的建议
"""
```

### 6.2 API 路由实现

```python
# ============================================================================
# backend/app/api/research.py
#
# [INPUT]: 依赖 FastAPI, app/agents/research_agent_service
# [OUTPUT]: 对外提供 /research API 端点
# [POS]: api/ 层，HTTP 入口
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
# ============================================================================

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.agents.research_agent_service import ResearchAgentService
from app.middlewares.auth import get_current_user


router = APIRouter(prefix="/research", tags=["research"])

# 单例服务
_agent_service: Optional[ResearchAgentService] = None

def get_agent_service() -> ResearchAgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = ResearchAgentService()
    return _agent_service


# ============================================================================
# Request/Response Models
# ============================================================================

class ResearchRequest(BaseModel):
    """研究任务请求"""
    task: str                              # 研究任务描述
    source_ids: List[str]                  # 源材料 ID 列表
    output_types: List[str] = ["summary", "mindmap"]  # 输出类型

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: Optional[str] = None
    context_source_ids: Optional[List[str]] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/projects/{project_id}/research")
async def start_research(
    project_id: str,
    request: ResearchRequest,
    agent_service: ResearchAgentService = Depends(get_agent_service),
    current_user = Depends(get_current_user),
):
    """
    发起研究任务 (SSE 流式返回)

    返回格式:
    - event: start, data: {"task_id": "xxx"}
    - event: progress, data: {"todos": [...]}
    - event: partial, data: {"type": "summary", "content": "..."}
    - event: complete, data: {"outputs": [...]}
    """

    async def generate():
        async for event in agent_service.research(
            project_id=project_id,
            task=request.task,
            source_ids=request.source_ids,
            output_types=request.output_types,
        ):
            event_type = event.get("event", "message")
            event_data = json.dumps(event, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {event_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/projects/{project_id}/chat")
async def chat(
    project_id: str,
    request: ChatRequest,
    agent_service: ResearchAgentService = Depends(get_agent_service),
    current_user = Depends(get_current_user),
):
    """
    对话接口 (SSE 流式返回)

    返回格式:
    - event: start, data: {"session_id": "xxx"}
    - event: token, data: {"content": "..."}
    - event: done, data: {"full_content": "...", "session_id": "xxx"}
    """

    async def generate():
        async for event in agent_service.chat(
            project_id=project_id,
            message=request.message,
            session_id=request.session_id,
            context_source_ids=request.context_source_ids,
        ):
            event_type = event.get("event", "token")
            event_data = json.dumps(event, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {event_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/projects/{project_id}/research/{task_id}")
async def get_research_status(
    project_id: str,
    task_id: str,
    agent_service: ResearchAgentService = Depends(get_agent_service),
    current_user = Depends(get_current_user),
):
    """获取研究任务状态"""

    # 从 PostgresBackend 获取状态
    state = await agent_service.checkpointer.aget_state({
        "configurable": {"thread_id": task_id}
    })

    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "project_id": project_id,
        "status": "completed" if state.values.get("should_end") else "running",
        "todos": state.values.get("todos", []),
        "outputs": state.values.get("outputs", []),
        "tokens_used": state.values.get("tokens_used", 0),
    }
```

### 6.3 使用示例

```python
# ============================================================================
# 使用示例
# ============================================================================

import asyncio
import httpx

async def demo_research():
    """研究任务示例"""

    async with httpx.AsyncClient() as client:
        # 1. 创建研究项目
        project = await client.post(
            "http://localhost:8000/api/projects",
            json={"name": "AI 2026 趋势研究"},
            headers={"Authorization": "Bearer xxx"}
        )
        project_id = project.json()["id"]

        # 2. 添加源材料
        sources = []
        for url in [
            "https://example.com/gpt5-release",
            "https://example.com/claude4-report",
        ]:
            source = await client.post(
                f"http://localhost:8000/api/projects/{project_id}/sources",
                json={"url": url},
            )
            sources.append(source.json()["id"])

        # 3. 发起研究任务 (SSE)
        async with client.stream(
            "POST",
            f"http://localhost:8000/api/research/projects/{project_id}/research",
            json={
                "task": "对比分析 GPT-5 和 Claude 4 的技术特点",
                "source_ids": sources,
                "output_types": ["summary", "mindmap"],
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.split(":")[1].strip()
                elif line.startswith("data:"):
                    data = json.loads(line[5:])
                    print(f"[{event_type}] {data}")


async def demo_chat():
    """对话示例"""

    async with httpx.AsyncClient() as client:
        project_id = "xxx"

        # 发送消息 (SSE)
        async with client.stream(
            "POST",
            f"http://localhost:8000/api/research/projects/{project_id}/chat",
            json={
                "message": "能详细解释 GPT-5 的推理能力提升吗？",
                "context_source_ids": ["source_id_1"],
            },
        ) as response:
            full_response = ""
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    if data.get("event") == "token":
                        print(data["content"], end="", flush=True)
                        full_response += data["content"]

            print(f"\n\n完整回答: {full_response}")


if __name__ == "__main__":
    asyncio.run(demo_research())
```

---

## 附录

### A. 依赖清单

```txt
# requirements.txt (新增)

# LangChain + LangGraph
langchain>=0.2.0
langchain-openai>=0.2.0
langgraph>=0.2.0
langgraph-checkpoint>=0.2.0
langgraph-checkpoint-postgres>=0.2.0

# 搜索
tavily-python>=0.4.0
httpx>=0.27.0

# 向量
pgvector>=0.2.0
numpy>=1.26.0

# 其他
pydantic>=2.0.0
```

### B. 环境变量

```bash
# .env (新增)

# LLM API Keys
MOONSHOT_API_KEY=sk-xxx              # Kimi K2 (Moonshot)

# Embedding (阿里云百炼)
DASHSCOPE_API_KEY=sk-xxx             # 百炼 通用文本向量-v3

# Search API Keys
TAVILY_API_KEY=tvly-xxx              # 网络搜索

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/signal
```

### C. 参考资料

| 资源 | 链接 |
|------|------|
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ |
| Moonshot (Kimi K2) | https://platform.moonshot.cn/ |
| 阿里云百炼 | https://dashscope.aliyun.com/ |
| Tavily API | https://docs.tavily.com/ |
| pgvector | https://github.com/pgvector/pgvector |

---

**文档状态**: 设计中
**下一步**: 技术评审 -> 原型开发 -> 迭代优化

[PROTOCOL]: 变更时更新此头部，然后检查 docs/CLAUDE.md
