# backend/app/processors/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
内容处理引擎，负责 LLM 调用、规则匹配、数据转换等单一责任处理。

## 成员清单
unified_filter.py: 统一过滤器，合并 SignalFilter + InitialFilter，0-5 评分制 (>=3 通过)
initial_filter.py: [DEPRECATED] 两阶段过滤器，已被 unified_filter.py 取代
analyzer.py: 三步深度分析器，全文分析 → 反思检查 → 优化改进
translator.py: 多语言翻译器，English → 中文(摘要/观点/金句)
generator.py: 摘要生成器
filter.py: [DEPRECATED] 规则过滤器，已被 unified_filter.py 取代
deduper.py: 三层去重器，URL精确匹配 + 标题Jaccard相似度(>0.8) + 内容指纹(可选)
batch_processor.py: 批量处理协调器
transcriber.py: 音频转写器 (播客/视频)
podcast_analyzer.py: 播客内容分析器，从转录文本提取章节(chapters)和问答对(qa_pairs)

## 处理流程

### 统一过滤 (UnifiedFilter) [推荐]
```
输入: title + content + url + source_name + source_is_whitelist
  ↓
Step 1: 白名单检查 → 白名单源直接通过 (score=5)
  ↓
Step 2: 语言检测 → 非中英文直接拒绝 (score=0)
  ↓
Step 3: 领域排除 → 命中排除词直接拒绝 (score=0)
  ↓
Step 4: LLM 评分 → 0-5 分 + 理由
  ↓
输出: FilterResult (score, reason, passed, is_whitelist, language, prompt_version)
阈值: score >= 3 通过
```

### [DEPRECATED] 初评过滤 (InitialFilter)
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

## 使用示例

### 批量处理器 (并发)
```python
from app.processors import BatchFilterProcessor, BatchAnalyzerProcessor, BatchTranslatorProcessor

batch_filter = BatchFilterProcessor(max_concurrent=5)
batch_analyzer = BatchAnalyzerProcessor(max_concurrent=3)
batch_translator = BatchTranslatorProcessor(max_concurrent=5)

filter_results = await batch_filter.filter_batch(items)
analysis_results = await batch_analyzer.analyze_batch(items, use_full_analysis=True)
translated_results = await batch_translator.translate_batch(items)
```
性能提升 3-5 倍吞吐量，失败任务自动重试 (最多 2 次)。

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
