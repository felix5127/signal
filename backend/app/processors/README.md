# Processors - 数据处理层

处理原始数据，包括去重、过滤、分析、翻译和生成摘要。

## 文件清单

### 原始处理器（单条处理）

- `dedup.py` - 去重逻辑（URL Hash + SimHash 标题相似度）
- `filter.py` - 两阶段过滤（规则预筛 + LLM 深度过滤，A/B/C 条件判断）
- `initial_filter.py` - **初评模块**（规则预筛 + LLM 初评 + 中英文分流，BestBlogs 风格）
- `analyzer.py` - **三步分析模块**（全文分析 → 检查反思 → 优化改进，BestBlogs 风格）
- `generator.py` - 摘要生成（LLM 生成 summary + scores + category）
- `translator.py` - **三步翻译模块**（初译 → 检查反思 → 意译优化，BestBlogs 风格）+ 标题专用翻译

### 批量处理器（并发优化，新增）

- `batch_processor.py` - **批量处理器模块**（并发优化版）
  - `BatchFilterProcessor` - 批量初评（并发 LLM 调用，5 个并发）
  - `BatchAnalyzerProcessor` - 批量深度分析（并发 LLM 调用，3 个并发）
  - `BatchTranslatorProcessor` - 批量翻译（并发 LLM 调用，5 个并发）
  - **性能提升**：对比原始处理器提升 **3-5 倍**吞吐量
  - **容错能力**：失败任务自动重试（最多 2 次）

## 子目录

### `deep_research/`
Deep Research 深度研究功能模块，采用可扩展架构设计。详见 [deep_research/README.md](deep_research/README.md)

主要文件：
- `base.py` - 抽象基类和数据结构
- `v1_lightweight.py` - V1 轻量级引擎（3步流程）
- `search_providers.py` - 搜索提供商实现（Tavily/Jina）

## 使用示例

### 原始处理器（串行）

```python
from app.processors import InitialFilter, Analyzer, Translator

initial_filter = InitialFilter()
analyzer = Analyzer()
translator = Translator()

# 单条处理（串行）
for item in items:
    filter_result = await initial_filter.filter(...)
    analysis = await analyzer.full_analyze(...)
    translation = await translator.translate_analysis(...)
```

### 批量处理器（并发）

```python
from app.processors import BatchFilterProcessor, BatchAnalyzerProcessor, BatchTranslatorProcessor

batch_filter = BatchFilterProcessor(max_concurrent=5)
batch_analyzer = BatchAnalyzerProcessor(max_concurrent=3)
batch_translator = BatchTranslatorProcessor(max_concurrent=5)

# 批量处理（并发）
filter_results = await batch_filter.filter_batch(items)
analysis_results = await batch_analyzer.analyze_batch(items, use_full_analysis=True)
translated_results = await batch_translator.translate_batch(items)
```

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
