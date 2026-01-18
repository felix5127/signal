# backend/app/agents/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
研究助手 Agent 系统，包含 LLM 客户端、工具集、嵌入服务和核心 Agent 实现。

## 成员清单
llm/: LLM 客户端模块 (Kimi K2)
tools/: Agent 工具集 (Tavily 搜索, 向量搜索)
embeddings/: 嵌入服务模块 (百炼 通用文本向量-v3)
research/: 研究 Agent (ResearchAgent, ChatAgent)
chat/: 对话 Agent (ChatAgent 重导出)

## 模块详情

### llm/kimi_client.py
- **KimiClient**: Kimi K2 LLM 客户端
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

### research/agent.py
- **ResearchAgent**: 研究 Agent
  - research(): 执行研究任务
  - research_stream(): 流式执行
  - 工具: tavily_search, vector_search
- **ChatAgent**: 对话 Agent
  - chat(): 项目内问答

## 数据流
```
用户查询
    ↓
ResearchAgent.research()
    ↓
KimiClient.chat() + Tools
    ├── TavilySearchTool.search() → 网络搜索结果
    └── VectorSearchTool.search() → 项目材料
    ↓
综合生成研究报告
```

## 配置
环境变量:
- KIMI_API_KEY: Kimi K2 API Key
- TAVILY_API_KEY: Tavily API Key
- DASHSCOPE_API_KEY: 百炼 API Key

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
