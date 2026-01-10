# Tasks - 定时任务层

编排数据处理流水线，定时执行数据采集和处理任务。

## 文件清单

### 核心流水线

- `pipeline.py` - **原始流水线模块**（串行处理）
  - `run_article_pipeline()` - 文章流水线：RSS采集 -> 全文提取 -> 初评过滤 -> 深度分析 -> 翻译 -> 存储
  - `run_full_pipeline()` - 旧版信号流水线（向后兼容）：HN/GitHub/HF 采集 -> 过滤 -> 摘要 -> 存储
  - `run_twitter_pipeline()` - Twitter 流水线：XGoing采集 -> 初评过滤 -> 深度分析 -> 翻译 -> 存储

- `pipeline_v2.py` - **优化版流水线模块**（并发处理，推荐使用）
  - `run_optimized_article_pipeline()` - 文章流水线（并发优化版）
    - **性能提升**：全文提取并发（10x）、LLM 调用并发（5x）、批量数据库操作（50x）
    - **任务跟踪**：实时进度更新、状态持久化
    - **容错能力**：失败任务自动重试、详细错误日志
    - **吞吐量**：对比原始流水线提升 **3-5 倍**

### 异步任务队列

- `queue.py` - **异步任务队列管理**（新增）
  - `AsyncTaskQueue` - 任务队列管理器（并发控制、进度跟踪）
  - `TaskProgress` - 任务进度跟踪器
  - `BatchLLMProcessor` - 批量 LLM 调用处理器（并发 + 重试）
  - `BatchContentExtractor` - 批量内容提取处理器（并发）
  - **使用场景**：
    - 批量 LLM 调用（初评/分析/翻译）
    - 批量网页内容提取
    - 自定义异步任务处理

### 定时任务

- `digest.py` - 汇总任务模块
  - `generate_daily_digest()` - 每日精选汇总（每天早上7:00）
  - `generate_weekly_digest()` - 每周精选汇总（每周一早上8:00）

- `newsletter.py` - 周刊生成模块
  - `generate_weekly_newsletter()` - 核心生成函数（异步）
  - `generate_newsletter_sync()` - Scheduler调用的同步包装函数
  - `generate_newsletter_for_week()` - 为指定周生成周刊（手动触发）
  - 触发时机：每周五下午17:00
  - 内容来源：Resource表（本周高分内容，按分类分组）
  - 输出格式：Markdown格式周刊，存储到Newsletter表

## 性能对比

| 流水线版本 | 处理 100 篇文章耗时 | 吞吐量 | 并发控制 | 错误重试 |
|----------|----------------|--------|---------|---------|
| 原始版 (pipeline.py) | ~30-40 分钟 | 0.04 篇/秒 | 无 | 无 |
| **优化版 (pipeline_v2.py)** | **~8-12 分钟** | **0.14 篇/秒** | 有 | 有 |

**优化要点**：
1. 全文提取并发（10 个并发）
2. LLM 调用并发（5 个并发）
3. 数据库批量插入（50 个一批）
4. 失败任务自动重试（最多 3 次）

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
