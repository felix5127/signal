# backend/app/processors/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
内容处理引擎，负责 LLM 调用、规则匹配、数据转换等单一责任处理。

## 成员清单
initial_filter.py: 两阶段过滤器，规则预筛(Keywords/WhiteList) + LLM 初评(0-5评分)
analyzer.py: 三步深度分析器，全文分析 → 反思检查 → 优化改进
translator.py: 多语言翻译器，English → 中文(摘要/观点/金句)
generator.py: 摘要生成器
filter.py: 规则过滤器，基于标题/来源/关键词的硬规则
batch_processor.py: 批量处理协调器
transcriber.py: 音频转写器 (播客/视频)

deep_research/: 深度研究引擎子模块
  ├── base.py: BaseResearchEngine 抽象类
  ├── v1_lightweight.py: 轻量级研究引擎 (当前实现)
  └── search_providers.py: 搜索提供商 (Tavily)

## 处理流程

### 初评过滤 (InitialFilter)
```
输入: title + content + url + source
  ↓
Phase 1: 规则预筛 (关键词匹配 + 来源白名单) → 减少 70% LLM 调用
  ↓
Phase 2: LLM 初评 → 0-5 分 + 语言检测 (zh/en)
  ↓
输出: InitialFilterResult (value, language, ignore, reason)
```

### 三步分析 (Analyzer)
```
Step 1: 全文分析 → 摘要(200-400字) + 观点(3-5) + 金句(3-5) + 标签 + 评分(0-100)
  ↓
Step 2: 反思检查 → LLM 审视 Step1 结果，提出改进建议
  ↓
Step 3: 优化改进 → 整合反思意见，输出最终版本
```

### 深度研究 (LightweightResearchEngine)
```
1. 生成研究问题 (3-5 个)
2. Tavily 搜索每个问题
3. 整合搜索结果 + 原文内容
4. LLM 生成 1500 字研究报告
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
