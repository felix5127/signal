# backend/app/agents/mindmap/
> L2 | 父级: backend/app/agents/CLAUDE.md

## 职责
概念图/思维导图生成模块，将研究内容转化为 Mermaid 格式的可视化图表。

## 成员清单
agent.py: MindmapAgent 概念图生成 Agent

## 模块详情

### agent.py
- **MindmapAgent**: 概念图生成
  - generate_mindmap(): 生成指定类型的图表
  - generate_summary_mindmap(): 生成内容摘要思维导图
- **DiagramType**: 图表类型枚举
  - MINDMAP: 思维导图
  - FLOWCHART: 流程图
  - SEQUENCE: 时序图
  - CLASS: 类图
  - ER: ER 图
- **MindmapResult**: 生成结果
  - success, diagram_type, mermaid_code, title, description

## 数据流
```
研究内容
    ↓
MindmapAgent.generate_mindmap()
    ↓
KimiClient.chat() (提取概念关系)
    ↓
MindmapResult (Mermaid 代码)
    ↓
前端 Mermaid.js 渲染
```

## 配置
环境变量:
- KIMI_API_KEY: Kimi K2 API Key (通过 llm/kimi_client)

## 使用示例
```python
from app.agents.mindmap import mindmap_agent, DiagramType

result = await mindmap_agent.generate_mindmap(
    content="研究报告内容...",
    diagram_type=DiagramType.FLOWCHART,
)

if result.success:
    print(result.mermaid_code)
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
