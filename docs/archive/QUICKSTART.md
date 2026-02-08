# 异步任务队列 - 快速开始

## 5 分钟上手

### 步骤 1: 创建数据库表

```bash
cd backend
python create_task_status_table.py
```

**预期输出**:
```
正在创建 task_status 表...
✓ task_status 表创建成功

表结构:
  - id: INTEGER
  - task_id: VARCHAR(100)
  - task_type: VARCHAR(50)
  - status: VARCHAR(20)
  - progress: FLOAT
  ...

✓ 迁移完成
```

---

### 步骤 2: 使用优化版流水线

```python
# 在你的脚本或 API 中使用
from app.tasks import run_optimized_article_pipeline

stats = await run_optimized_article_pipeline(
    opml_path="path/to/blogs.opml",
    min_value_score=3,
    use_full_analysis=True,
)

print(f"处理完成: {stats.saved_count} 篇文章")
print(f"耗时: {stats.total_duration_seconds:.1f}秒")
```

**预期输出**:
```
============================================================
[OptimizedPipeline] Starting at 2026-01-02 15:30:00
============================================================

[OptimizedPipeline] Step 1: Scraping RSS feeds...
[OptimizedPipeline] Scraped 100 articles

[OptimizedPipeline] Step 2: Checking for duplicates (batch query)...
[OptimizedPipeline] Found 10 duplicates, 90 new articles

[OptimizedPipeline] Step 3: Extracting full content (concurrent)...
[OptimizedPipeline] Extracted 85/90 articles

[OptimizedPipeline] Step 4: Initial filtering (concurrent LLM)...
[OptimizedPipeline] 60/85 passed filter

[OptimizedPipeline] Step 5: Deep analysis (concurrent LLM)...
[OptimizedPipeline] Analyzed 58/60 articles

[OptimizedPipeline] Step 6: Translating English content (concurrent)...
[OptimizedPipeline] Translated 40 English articles

[OptimizedPipeline] Step 7: Bulk saving to database...
[OptimizedPipeline] Saved 58 resources

============================================================
[OptimizedPipeline] Summary:
  - RSS Scraped: 100
  - Duplicates: 10
  - Content Extracted: 85 (failed: 5)
  - Filter Passed: 60 (rejected: 25)
  - Analyzed: 58 (failed: 2)
  - Translated: 40 (failed: 0)
  - Saved: 58
  - Failed: 0
  - Input tokens: 245,000
  - Output tokens: 85,000
  - Total tokens: 330,000
  - Duration: 480.5s (8.0m)
  - Throughput: 0.21 articles/sec
============================================================
```

---

### 步骤 3: 查询任务状态

```python
from app.models import TaskStatus
from app.database import SessionLocal

db = SessionLocal()

# 查询最近的任务
tasks = db.query(TaskStatus).order_by(
    TaskStatus.created_at.desc()
).limit(10).all()

for task in tasks:
    print(f"{task.task_id[:8]}... | {task.task_type} | {task.status} | {task.progress:.0f}%")

db.close()
```

---

## 常见使用场景

### 场景 1: 批量初评

```python
from app.processors import BatchFilterProcessor

batch_filter = BatchFilterProcessor(max_concurrent=5)

items = [
    {
        "title": "文章标题",
        "content": "文章内容...",
        "url": "https://example.com",
        "source": "source_name",
    },
    # ... 更多文章
]

results = await batch_filter.filter_batch(items)

for success, filter_result in results:
    if success and filter_result.value >= 3:
        print(f"通过: {filter_result.value}")
```

### 场景 2: 批量分析

```python
from app.processors import BatchAnalyzerProcessor

batch_analyzer = BatchAnalyzerProcessor(max_concurrent=3)

items = [
    {
        "content": "文章全文...",
        "title": "文章标题",
        "source": "source_name",
        "url": "https://example.com",
        "language": "en",
    },
    # ... 更多文章
]

results = await batch_analyzer.analyze_batch(
    items=items,
    use_full_analysis=True,
)

for success, analysis in results:
    if success:
        print(f"分数: {analysis.score}")
```

### 场景 3: 批量翻译

```python
from app.processors import BatchTranslatorProcessor

batch_translator = BatchTranslatorProcessor(max_concurrent=5)

items = [
    {
        "title": "Article Title",
        "analysis_dict": {
            "oneSentenceSummary": "...",
            "summary": "...",
            "mainPoints": [...],
            "keyQuotes": [...],
        },
    },
    # ... 更多文章
]

results = await batch_translator.translate_batch(items)

for success, translated in results:
    if success:
        print(f"标题: {translated['title_translated']}")
```

---

## 性能对比

运行性能对比脚本：

```bash
python benchmark_pipelines.py --opml-path path/to/blogs.opml --mode both
```

**预期输出**:
```
============================================================
性能对比测试 - 原始流水线 vs 优化版流水线
开始时间: 2026-01-02 15:30:00
OPML 路径: path/to/blogs.opml
============================================================

============================================================
测试原始流水线 (pipeline.py)
============================================================

... (处理过程)

原始流水线 - 统计总结
============================================================
采集: 100 篇
耗时: 2017.0秒 (33.6分钟)
吞吐量: 0.05 篇/秒
============================================================

============================================================
测试优化版流水线 (pipeline_v2.py)
============================================================

... (处理过程)

优化版流水线 - 统计总结
============================================================
采集: 100 篇
耗时: 480.5秒 (8.0分钟)
吞吐量: 0.21 篇/秒
============================================================

============================================================
性能对比总结
============================================================

原始流水线:
  耗时: 2017.0秒 (33.6分钟)
  吞吐量: 0.05 篇/秒

优化版流水线:
  耗时: 480.5秒 (8.0分钟)
  吞吐量: 0.21 篇/秒

提升效果:
  加速比: 4.20x
  时间节省: 1536.5秒 (25.6分钟)
  吞吐量提升: 4.20x

============================================================
✓ 性能对比完成
============================================================
```

---

## 调整并发数

根据你的 API 限制和服务器性能调整并发数：

```python
stats = await run_optimized_article_pipeline(
    opml_path="path/to/blogs.opml",
    max_concurrent_extraction=10,  # 全文提取并发（默认 10）
    max_concurrent_analysis=3,     # LLM 分析并发（默认 3）
    max_concurrent_translation=5,  # 翻译并发（默认 5）
)
```

**推荐配置**:

| API 提供商 | 推荐并发数 | 说明 |
|----------|----------|------|
| OpenAI (标准) | 5 | 标准 tier 限制 |
| OpenAI (Pro) | 10 | Pro tier 支持更高并发 |
| Kimi (免费) | 3 | 免费版限流严格 |
| Kimi (付费) | 5 | 付费版限制较松 |
| 全文提取 | 10-20 | 根据浏览器性能调整 |

---

## 测试和调试

### 单元测试

```bash
python test_async_queue.py
```

**预期输出**:
```
============================================================
异步任务队列和批量处理器测试
开始时间: 2026-01-02 15:30:00
============================================================

============================================================
测试 1: 任务队列基本功能
============================================================
✓ 创建任务: a1b2c3d4...
✓ 启动任务
✓ 处理完成: 10 个任务
✓ 任务状态: completed
✓ 进度: 100%
✓ 处理: 10/10

✓ 测试 1 通过

============================================================
✓ 所有测试通过
结束时间: 2026-01-02 15:30:05
============================================================
```

---

## 问题排查

### 问题 1: API 限流

**症状**: 大量 429 错误

**解决方案**:
```python
# 降低并发数
batch_analyzer = BatchAnalyzerProcessor(max_concurrent=2)
```

### 问题 2: 内存不足

**症状**: OOM 错误

**解决方案**:
```python
# 分批处理
for i in range(0, len(items), 50):
    batch = items[i:i+50]
    results = await processor.process_batch(batch)
```

### 问题 3: 任务卡住

**症状**: 任务状态一直是 running

**解决方案**:
```python
# 查询任务详情
task = db.query(TaskStatus).filter(...).first()
print(f"错误: {task.error}")

# 重启任务
# ...
```

---

## 下一步

1. 查看 [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) 了解更多使用示例
2. 查看 [ASYNC_QUEUE_IMPLEMENTATION.md](../../ASYNC_QUEUE_IMPLEMENTATION.md) 了解实现细节
3. 运行 `benchmark_pipelines.py` 进行性能对比

---

## 支持

如有问题，请查看：
- 使用示例: `backend/app/tasks/USAGE_EXAMPLES.md`
- 实现报告: `ASYNC_QUEUE_IMPLEMENTATION.md`
- 任务 README: `backend/app/tasks/README.md`

祝使用愉快！🚀
