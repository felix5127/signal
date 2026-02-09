# backend/app/agents/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
Agent 系统，包含 LLM 客户端、工具集、嵌入服务、研究 Agent 和播客生成。

## 成员清单
llm/: LLM 客户端模块 (Kimi K2，Pipeline 使用)
tools/: Agent 工具集 (Tavily 搜索, 向量搜索)
embeddings/: 嵌入服务模块 (百炼 通用文本向量-v3)
multimodal/: 多模态处理模块 (听悟转写, 源材料处理)
research/: 研究 Agent (Claude SDK — sdk_service, tools, prompts, session_store)
mindmap/: 概念图生成 Agent (MindmapAgent，被 api/mindmap.py 使用)
podcast/: 播客生成模块 (大纲/对话/TTS/合成)

## 模块详情

### llm/kimi_client.py
- **KimiClient**: Kimi K2 LLM 客户端 (Pipeline 继续使用)
  - 支持模型: kimi-k2-thinking-turbo (研究), kimi-k2-turbo-preview (对话)
  - 功能: chat(), chat_stream(), research(), summarize(), chat_turn()
  - Tool Calling: OpenAI 兼容格式

### tools/tavily_search.py
- **TavilySearchTool**: 网络搜索工具
  - search(): 执行搜索
  - execute(): LLM Tool Calling 入口
  - 支持: 域名过滤、深度搜索、答案生成

### tools/vector_search.py
- **VectorSearchTool**: 向量相似度搜索
  - search(): pgvector 向量搜索
  - execute(): LLM Tool Calling 入口
  - 支持: 项目范围限定、相似度阈值

### embeddings/bailian_embedding.py
- **BailianEmbeddingService**: 百炼嵌入服务
  - embed_text(): 单文本嵌入
  - embed_texts(): 批量嵌入
  - 维度: 512 (默认), 可选 256/128/64
- **TextSplitter**: 文本分块器
  - split_text(): 按分隔符分块
  - split_by_sentences(): 按句子分块

### research/ (Claude SDK 架构)
- **sdk_service.py**: ResearchSDKService — 核心服务层
  - chat_stream(): SSE 流式对话 (claude-sonnet-4-5)
  - report_stream(): SSE 流式报告生成 (claude-opus-4-6)
  - mindmap_stream(): SSE 流式思维导图 (claude-sonnet-4-5)
  - 使用智谱 BigModel Anthropic 兼容代理
- **tools.py**: 5 个 Anthropic 格式工具定义
  - search_vectors: 项目知识库向量搜索
  - tavily_search: 网络搜索
  - list_sources: 列出项目源材料
  - read_source: 读取源材料内容
  - save_output: 保存研究输出
- **prompts.py**: Agent 系统提示词 + 模型配置常量
- **session_store.py**: 会话历史加载 (从 ChatMessage 表)

### mindmap/agent.py
- **MindmapAgent**: 概念图生成 Agent (Kimi 驱动)
  - generate_mindmap(): 生成 Mermaid 格式图表
  - generate_summary_mindmap(): 生成摘要思维导图
  - 被 api/mindmap.py 端点直接使用

### podcast/
- **cosyvoice_client.py**: CosyVoice TTS 客户端
  - synthesize_text(): 单段文本转语音
  - synthesize_dialogue(): 多段对话合成
  - VoicePreset: 预设音色枚举 (10+ 中英文音色)
- **outline_agent.py**: 播客大纲生成
  - generate_outline(): 生成 PodcastOutline
- **dialogue_agent.py**: 播客对话生成
  - generate_dialogue(): 生成 PodcastDialogue
- **synthesizer.py**: 完整播客流水线
  - generate_podcast(): 同步生成
  - generate_podcast_stream(): 流式生成

## 数据流

### 研究模块 (Claude SDK)
```
用户查询 (SSE POST)
    ↓
ResearchSDKService.chat_stream()
    ↓
Anthropic API (智谱代理) + Tool Use 循环
    ├── search_vectors → pgvector 向量搜索
    ├── tavily_search → 网络搜索
    ├── list_sources / read_source → 源材料读取
    └── save_output → 保存研究输出到 DB
    ↓
SSE 事件流 (text/tool_start/tool_end/done/error)
```

### 播客生成流
```
研究内容
    ↓
OutlineAgent.generate_outline()
    ↓
DialogueAgent.generate_dialogue()
    ↓
CosyVoiceClient.synthesize_dialogue()
    ↓
播客音频 (MP3)
```

## 配置
环境变量:
- ANTHROPIC_API_KEY: Claude API Key (研究模块，通过智谱代理)
- MOONSHOT_API_KEY: Kimi K2 API Key (Pipeline + 概念图)
- TAVILY_API_KEY: Tavily API Key (研究 + Pipeline 共用)
- DASHSCOPE_API_KEY: 百炼 API Key (嵌入服务)

## 变更日志

### 2026-02-09 - Claude SDK 迁移 (研究模块)
- 新增 sdk_service.py, tools.py, prompts.py, session_store.py
- 删除旧 agent.py (ResearchAgent + ChatAgent，使用 Kimi)
- 删除 chat/ 目录 (仅含 ChatAgent 重导出)
- __init__.py 改为导出 ResearchSDKService
- 研究模块从 Kimi → Claude (智谱 Anthropic 兼容代理)
- Pipeline/概念图/播客继续使用 Kimi

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
