# Signal 数据爬取系统重构设计方案

> Architect: Opus
> Date: 2026-02-08
> Status: Draft (Pending Lead Approval)
> Based on: docs/research/findings.md

---

## 1. 设计目标

### 核心问题
基于调研报告 (findings.md) 确认的 5 类问题，按严重程度排序：

| # | 问题域 | 严重程度 | 核心缺陷 |
|---|--------|---------|----------|
| 1 | 转写系统 | CRITICAL | SDK 缺失/同步阻塞/限额过低 |
| 2 | AI 调用层 | HIGH | LLM 失败策略不一致，错误处理碎片化 |
| 3 | 数据抓取可靠性 | HIGH | ContentExtractor 无重试/无复用，健康检查残缺 |
| 4 | 任务透明度 | HIGH | print() 日志、假暂停/恢复、无实时状态 |
| 5 | 系统可控性 | MEDIUM | 无中止/重跑/dry-run、配置分散 |

### 设计原则

1. **渐进式重构** -- 不重写，逐模块替换，保持系统始终可运行
2. **向后兼容** -- 新模块与旧模块共存，通过 feature flag 切换
3. **单一事实源** -- 每个概念只有一个权威实现
4. **fail-safe over fail-open** -- AI 不确定时宁可拒绝，不可放行

---

## 2. 架构概览

### 2.1 当前架构

```
APScheduler ─→ pipeline.py (1398 行单文件)
                ├── ArticlePipeline (函数式)
                ├── TwitterPipeline (函数式)
                ├── PodcastPipeline (函数式)
                └── VideoPipeline   (函数式)

LLM 调用: 各 Processor 直接调用 llm_client (全局单例)
日志: print() 散落各处
状态: 内存 PipelineState + DB SourceRun (事后记录)
控制: BackgroundTasks / threading.Thread (fire-and-forget)
```

### 2.2 目标架构

```
APScheduler / API Trigger
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  PipelineOrchestrator                                │
│  (任务生命周期管理: 创建 → 运行 → 暂停 → 恢复 → 取消) │
│  ┌────────────────────────────────────────────────┐  │
│  │ CancellationToken  (threading.Event)           │  │
│  │ PipelineContext    (运行时上下文+结构化日志)      │  │
│  │ CheckpointManager  (步骤间检查点)               │  │
│  └────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
 StepBasedPipeline   StepBasedPipeline
 (ArticlePipeline)   (PodcastPipeline)
        │                   │
        ▼                   ▼
┌───────────────┐   ┌──────────────┐
│ Scraper Layer │   │ Transcription│
│ (RSS/XGoing)  │   │ Service      │
└───────┬───────┘   └──────┬───────┘
        │                   │
        ▼                   ▼
┌───────────────────────────────────┐
│ AIService (统一 AI 调用层)         │
│ ┌──────────┐ ┌─────────────────┐ │
│ │ LLMClient│ │ FailurePolicy   │ │
│ │ (重试)   │ │ (统一失败策略)   │ │
│ └──────────┘ └─────────────────┘ │
│ ┌──────────┐ ┌─────────────────┐ │
│ │ JSONParser│ │ CostTracker     │ │
│ │ (统一解析)│ │ (成本追踪)      │ │
│ └──────────┘ └─────────────────┘ │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ ObservabilityLayer                │
│ ┌──────────┐ ┌─────────────────┐ │
│ │ structlog│ │ PipelineTracker │ │
│ │ (结构化) │ │ (实时状态+历史) │ │
│ └──────────┘ └─────────────────┘ │
└───────────────────────────────────┘
```

---

## 3. 模块设计

### 3.1 转写系统 (P0 - CRITICAL)

#### 3.1.1 问题根因
- 阿里云 SDK 同步调用阻塞事件循环
- 环境变量缺失时静默失败
- 每日限额硬编码为 5 条
- 每次轮询重建 AcsClient

#### 3.1.2 设计方案

**新模块: `backend/app/processors/transcription_service.py`**

```python
class TranscriptionService:
    """
    转写服务 (替代 Transcriber)

    改进点:
    1. 同步 SDK 调用包装为 asyncio.to_thread()
    2. AcsClient 单例复用
    3. 启动时配置校验 + 明确告警
    4. 可配置限额 (从 config.yaml 读取)
    5. 结构化日志 + 状态追踪
    """

    def __init__(self, config: TingwuConfig):
        self._client: Optional[AcsClient] = None
        self._config = config
        self._daily_count = 0
        self._daily_reset_date = None

    def validate_config(self) -> list[str]:
        """启动时校验配置，返回缺失项列表"""
        ...

    async def transcribe(
        self,
        media_url: str,
        media_type: str = "audio",
        cancellation_token: Optional[CancellationToken] = None,
    ) -> TranscriptionResult:
        """
        异步转写 (非阻塞)

        改进:
        - SDK 调用通过 asyncio.to_thread() 包装
        - 支持 CancellationToken 中途取消
        - 结构化错误返回 (不再返回 None)
        """
        ...

    async def _submit_task_async(self, media_url: str) -> str:
        """将同步 AcsClient 调用放入线程池"""
        return await asyncio.to_thread(self._submit_task_sync, media_url)

    async def _poll_task_async(
        self, task_id: str, cancellation_token: Optional[CancellationToken] = None
    ) -> TranscriptionResult:
        """异步轮询，支持取消"""
        while not (cancellation_token and cancellation_token.is_cancelled):
            status = await asyncio.to_thread(self._query_task_sync, task_id)
            if status == "COMPLETED":
                return await self._download_result(task_id)
            if status == "FAILED":
                raise TranscriptionError(...)
            await asyncio.sleep(self._config.poll_interval)
```

**配置变更: `config.yaml`**

```yaml
podcast:
  max_daily_items: 10          # 从 5 提升到 10
  transcribe_max_concurrent: 2  # 同时转写数量
  transcribe_timeout: 2400      # 40 分钟超时
```

#### 3.1.3 迁移策略
1. 新建 `TranscriptionService`，不修改现有 `Transcriber`
2. 在 `PodcastPipeline` 中通过配置开关切换
3. 验证稳定后删除旧 `Transcriber`

---

### 3.2 AI 调用层 (P0 - HIGH)

#### 3.2.1 问题根因
- LLM 失败时各模块行为不一致 (放行 vs 拦截)
- JSON 解析策略不统一
- 无成本追踪和预算控制

#### 3.2.2 设计方案

**新模块: `backend/app/services/ai_service.py`**

统一的 AI 调用层，所有 Processor 通过此层调用 LLM。

```python
@dataclass
class AICallResult:
    """AI 调用结果 (统一返回类型)"""
    success: bool
    data: Optional[dict] = None       # 解析后的 JSON
    raw_response: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    retries: int = 0


class FailurePolicy(Enum):
    """AI 调用失败时的行为策略"""
    REJECT = "reject"           # 失败即拒绝 (用于 filter)
    PENDING_REVIEW = "pending"  # 标记为待人工审核
    RETRY_THEN_SKIP = "skip"   # 重试后跳过 (用于非关键步骤)
    FALLBACK = "fallback"      # 使用降级值


class AIService:
    """
    统一 AI 调用服务

    职责:
    1. 统一的 LLM 调用接口 (call_json / call_text)
    2. 统一的失败策略 (FailurePolicy)
    3. 统一的 JSON 解析 (多策略 fallback)
    4. 成本追踪 (按任务/按模型)
    5. 调用统计 (成功率/延迟/Token)
    """

    def __init__(self, llm_client: LLMClient):
        self._client = llm_client
        self._cost_tracker = CostTracker()

    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        failure_policy: FailurePolicy = FailurePolicy.REJECT,
        fallback_value: Optional[dict] = None,
        task_id: Optional[str] = None,
        temperature: float = 0.3,
    ) -> AICallResult:
        """
        统一的 JSON 调用接口

        改进:
        - 统一的失败策略 (不再各模块自行决定)
        - 多层 JSON 解析: markdown代码块 → 正则 → 大括号匹配
        - 自动成本追踪
        - 结构化日志
        """
        try:
            raw = await self._client.call(system_prompt, user_prompt, temperature=temperature)
            data = self._parse_json(raw)
            cost = self._cost_tracker.estimate(raw, task_id)
            return AICallResult(success=True, data=data, raw_response=raw, cost_usd=cost)
        except Exception as e:
            logger.warning("ai_call_failed", error=str(e), policy=failure_policy.value)
            return self._apply_failure_policy(failure_policy, fallback_value, e)

    def _parse_json(self, raw: str) -> dict:
        """
        多策略 JSON 解析

        优先级:
        1. 提取 ```json ... ``` 代码块
        2. 正则匹配 JSON 对象
        3. 查找首个 { 到末尾的 } 的平衡匹配
        4. 全部失败则抛出 JSONParseError
        """
        ...

    def _apply_failure_policy(
        self, policy: FailurePolicy, fallback: Optional[dict], error: Exception
    ) -> AICallResult:
        """根据策略返回失败结果"""
        if policy == FailurePolicy.REJECT:
            return AICallResult(success=False, error=str(error))
        elif policy == FailurePolicy.PENDING_REVIEW:
            return AICallResult(success=False, error=str(error), data={"status": "pending_review"})
        elif policy == FailurePolicy.FALLBACK and fallback:
            return AICallResult(success=True, data=fallback)
        else:
            return AICallResult(success=False, error=str(error))


class CostTracker:
    """LLM 调用成本追踪"""

    # 价格表 (per 1M tokens)
    PRICING = {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        # ... 其他模型
    }

    def __init__(self):
        self._daily_cost = 0.0
        self._daily_calls = 0
        self._daily_reset_date = None
        self._task_costs: dict[str, float] = {}

    def estimate(self, response: str, task_id: Optional[str] = None) -> float:
        """估算单次调用成本"""
        ...

    def get_daily_summary(self) -> dict:
        """获取每日成本摘要"""
        ...
```

#### 3.2.3 Processor 迁移

现有 Processor 逐步迁移到使用 `AIService`:

```python
# BEFORE (unified_filter.py)
class UnifiedFilter:
    async def _llm_score(self, ...):
        try:
            response = await llm_client.call_json(...)
            ...
        except Exception as e:
            return FilterResult(score=3, ...)  # 失败放行!

# AFTER
class UnifiedFilter:
    def __init__(self, ai_service: AIService):
        self._ai = ai_service

    async def _llm_score(self, ...):
        result = await self._ai.call_json(
            system_prompt, user_prompt,
            failure_policy=FailurePolicy.REJECT,  # 失败即拒绝
        )
        if not result.success:
            return FilterResult(score=0, reason=f"LLM unavailable: {result.error}", passed=False, ...)
        ...
```

**关键决策: 统一失败策略**

| Processor | 当前策略 | 新策略 | 理由 |
|-----------|---------|--------|------|
| UnifiedFilter | 失败放行 (score=3) | **REJECT** (score=0) | 质量关卡，不可放行 |
| Analyzer | 失败跳过 | **RETRY_THEN_SKIP** | 非关卡，跳过该条即可 |
| Translator | 失败用原文 | **FALLBACK** (原文) | 有合理降级值 |
| PodcastAnalyzer | 失败返回空 | **RETRY_THEN_SKIP** | 非关键，不影响存储 |

---

### 3.3 爬虫可靠性层 (P1 - HIGH)

#### 3.3.1 ContentExtractor 增强

**改进: `backend/app/scrapers/content_extractor.py`**

```python
class ContentExtractor:
    """
    增强版全文提取器

    改进:
    1. Playwright 浏览器连接池 (复用而非每次新建)
    2. 重试机制 (最多 2 次, 指数退避)
    3. 提取结果缓存 (同一 URL 不重复提取)
    4. 失败统计 (按域名聚合)
    5. Jina Reader 降级 (Playwright 失败时回退到 Jina)
    """

    def __init__(self, pool_size: int = 3):
        self._browser_pool: Optional[BrowserPool] = None
        self._pool_size = pool_size
        self._failure_stats: dict[str, int] = {}  # domain -> failure_count

    async def _ensure_pool(self):
        """延迟初始化浏览器池"""
        if self._browser_pool is None:
            self._browser_pool = BrowserPool(size=self._pool_size)
            await self._browser_pool.initialize()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(3))
    async def extract(self, url: str) -> ExtractedContent:
        """
        提取全文 (带重试 + 降级)

        流程:
        1. 尝试 Playwright 提取
        2. Playwright 失败 → 尝试 Jina Reader
        3. 都失败 → 返回带 error 标记的 ExtractedContent
        """
        ...

    async def close(self):
        """关闭浏览器池"""
        if self._browser_pool:
            await self._browser_pool.close()


class BrowserPool:
    """Playwright 浏览器连接池"""

    def __init__(self, size: int = 3):
        self._size = size
        self._browsers: list = []
        self._semaphore = asyncio.Semaphore(size)

    async def acquire(self) -> Browser:
        """获取一个浏览器实例"""
        ...

    async def release(self, browser: Browser):
        """归还浏览器实例"""
        ...
```

#### 3.3.2 源健康检查恢复

**改进: `backend/app/services/source_health.py`**

```python
class SourceHealthChecker:
    """
    增强版健康检查

    改进:
    1. RSS Feed 可达性探测 (HEAD 请求)
    2. 基于历史成功率的健康评估
    3. 周期性检查调度 (每 30 分钟)
    4. 告警阈值 (连续 3 次失败)
    """

    async def check_feed_reachability(self, feed_url: str) -> HealthCheck:
        """检查 RSS Feed 是否可达"""
        ...

    async def check_source_history(self, source_type: str, hours: int = 24) -> HealthCheck:
        """基于历史运行记录评估健康度"""
        ...
```

---

### 3.4 任务透明度 (P1 - HIGH)

#### 3.4.1 结构化日志

**改进: 全面切换到 structlog**

```python
import structlog

logger = structlog.get_logger()

# BEFORE (pipeline.py)
print(f"[ArticlePipeline] Scraped {stats.scraped_count} articles from RSS feeds")

# AFTER
logger.info(
    "pipeline.scrape.completed",
    pipeline="article",
    scraped_count=stats.scraped_count,
    duration_ms=elapsed_ms,
)
```

日志命名规范: `{module}.{action}.{status}`

| 示例 | 含义 |
|------|------|
| `pipeline.scrape.started` | 流水线采集开始 |
| `pipeline.filter.rejected` | 内容被过滤拒绝 |
| `ai.call.failed` | AI 调用失败 |
| `transcription.poll.timeout` | 转写轮询超时 |

#### 3.4.2 Pipeline 运行上下文

**新模块: `backend/app/tasks/pipeline_context.py`**

```python
@dataclass
class PipelineContext:
    """
    流水线运行上下文

    职责:
    1. 持久化运行状态 (DB-backed，重启不丢失)
    2. 步骤级进度追踪
    3. CancellationToken 支持
    4. 结构化日志绑定 (自动附加 pipeline_id)
    """
    pipeline_id: str
    pipeline_type: str         # article/twitter/podcast/video
    status: str                # pending/running/paused/cancelled/completed/failed
    current_step: str          # scrape/dedupe/filter/analyze/translate/save
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    started_at: Optional[datetime] = None
    steps_log: list[StepLog] = field(default_factory=list)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)

    def check_cancelled(self):
        """在步骤间调用，支持优雅取消"""
        if self.cancellation_token.is_cancelled:
            self.status = "cancelled"
            self._persist()
            raise PipelineCancelled(self.pipeline_id)

    def advance_step(self, step_name: str):
        """推进到下一步骤"""
        self.current_step = step_name
        self.steps_log.append(StepLog(step=step_name, started_at=datetime.now()))
        self._persist()

    def _persist(self):
        """持久化到 DB (TaskStatus 表)"""
        ...


class CancellationToken:
    """线程安全的取消令牌"""

    def __init__(self):
        self._event = threading.Event()

    def cancel(self):
        """发出取消信号"""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()


@dataclass
class StepLog:
    """步骤日志"""
    step: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    items_in: int = 0
    items_out: int = 0
    error: Optional[str] = None
```

#### 3.4.3 PipelineOrchestrator

**新模块: `backend/app/tasks/orchestrator.py`**

```python
class PipelineOrchestrator:
    """
    流水线编排器

    职责:
    1. 创建并管理 PipelineContext
    2. 防止重叠执行 (同类型同时只能运行一个)
    3. 提供暂停/恢复/取消能力
    4. 统一的触发入口 (替代 scheduler_jobs.py 中的全局函数)
    """

    def __init__(self):
        self._running: dict[str, PipelineContext] = {}  # type -> context
        self._lock = threading.Lock()

    async def start(self, pipeline_type: str, **kwargs) -> str:
        """
        启动流水线

        Returns:
            pipeline_id: 用于后续查询/控制
        """
        with self._lock:
            if pipeline_type in self._running:
                raise PipelineAlreadyRunning(pipeline_type)

            ctx = PipelineContext(
                pipeline_id=str(uuid.uuid4()),
                pipeline_type=pipeline_type,
                status="running",
                current_step="init",
                started_at=datetime.now(),
            )
            self._running[pipeline_type] = ctx

        try:
            pipeline = self._create_pipeline(pipeline_type, ctx)
            await pipeline.run()
            ctx.status = "completed"
        except PipelineCancelled:
            ctx.status = "cancelled"
        except Exception as e:
            ctx.status = "failed"
            logger.error("pipeline.failed", pipeline_type=pipeline_type, error=str(e))
        finally:
            with self._lock:
                self._running.pop(pipeline_type, None)
            ctx._persist()

        return ctx.pipeline_id

    def cancel(self, pipeline_type: str) -> bool:
        """取消运行中的流水线"""
        ctx = self._running.get(pipeline_type)
        if ctx:
            ctx.cancellation_token.cancel()
            return True
        return False

    def get_status(self, pipeline_type: str) -> Optional[dict]:
        """获取运行状态"""
        ctx = self._running.get(pipeline_type)
        return ctx.to_dict() if ctx else None

    def get_all_status(self) -> list[dict]:
        """获取所有运行中流水线的状态"""
        return [ctx.to_dict() for ctx in self._running.values()]


# 全局单例
orchestrator = PipelineOrchestrator()
```

---

### 3.5 管理控制面板 (P2 - MEDIUM)

#### 3.5.1 增强控制 API

**扩展: `backend/app/api/sources.py`**

```python
# 新增端点

@router.post("/cancel/{source_type}")
async def cancel_pipeline(source_type: str):
    """取消运行中的流水线"""
    success = orchestrator.cancel(source_type)
    ...

@router.get("/pipeline-status")
async def get_pipeline_status():
    """获取所有流水线的实时状态"""
    return orchestrator.get_all_status()

@router.post("/trigger/{source_type}")
async def trigger_pipeline(
    source_type: str,
    dry_run: bool = Query(default=False),
    feed_filter: Optional[str] = Query(default=None),
):
    """
    增强触发 (带 dry-run 和 feed 过滤)

    Args:
        dry_run: 模拟执行，不实际保存
        feed_filter: 只处理匹配的 feed (正则)
    """
    ...

@router.post("/retry/{pipeline_id}")
async def retry_failed(pipeline_id: str):
    """重跑指定流水线中失败的项"""
    ...
```

#### 3.5.2 启动时配置校验

**改进: `backend/app/startup.py`**

```python
def validate_config_on_startup(config: AppConfig):
    """
    启动时校验关键配置

    校验项:
    1. DATABASE_URL 格式和连接
    2. LLM API Key 存在且格式正确
    3. OPML 文件存在且可解析
    4. 转写 API 配置 (如果 podcast.transcribe_enabled=true)
    5. Redis 连接 (如果 redis.enabled=true)
    """
    warnings = []
    errors = []

    # LLM
    if not config.openai_api_key:
        errors.append("OPENAI_API_KEY not set (LLM calls will fail)")

    # Transcription
    if config.podcast.transcribe_enabled:
        transcription_service = TranscriptionService(config.tingwu)
        missing = transcription_service.validate_config()
        if missing:
            warnings.append(f"Transcription config incomplete: {missing}")

    # OPML files
    for source_type in ["blog", "podcast", "twitter"]:
        source_conf = getattr(config, source_type, None)
        if source_conf and source_conf.enabled:
            opml = getattr(source_conf, "opml_path", None)
            if opml and not os.path.exists(opml):
                warnings.append(f"{source_type} OPML not found: {opml}")

    for w in warnings:
        logger.warning("config.validation.warning", message=w)
    for e in errors:
        logger.error("config.validation.error", message=e)

    if errors:
        raise ConfigurationError(f"Critical config errors: {errors}")
```

---

## 4. 数据流图

### 4.1 重构后的 ArticlePipeline 数据流

```
APScheduler / POST /sources/trigger/blog
          │
          ▼
 PipelineOrchestrator.start("blog")
          │
          ▼ (创建 PipelineContext, 检查重叠)
          │
 ┌────────┴────────────────────────────────────────────────────────┐
 │ ArticlePipeline (extends StepBasedPipeline)                     │
 │                                                                 │
 │  Step 1: scrape() ──→ RSSScraper ──→ RawSignal[]               │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 2: dedupe() ──→ Deduper ──→ 三层去重                      │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 3: extract() ──→ ContentExtractor (池化+重试+Jina降级)     │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 4: filter() ──→ UnifiedFilter via AIService               │
 │     │    failure_policy=REJECT                                  │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 5: analyze() ──→ Analyzer via AIService                   │
 │     │    failure_policy=RETRY_THEN_SKIP                         │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 6: translate() ──→ Translator via AIService               │
 │     │    failure_policy=FALLBACK (原文)                          │
 │     │    ctx.check_cancelled()                                  │
 │     ▼                                                           │
 │  Step 7: save() ──→ DB 批量写入 + SourceService.record_run()    │
 │     │                                                           │
 │     ▼                                                           │
 │  Step 8: track() ──→ DataTracker.flush() (飞书)                 │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
          │
          ▼
 PipelineContext.status = "completed"
 structlog: pipeline.completed {scraped: N, saved: M, cost: $X.XX}
```

### 4.2 重构后的 PodcastPipeline 数据流

```
 POST /sources/trigger/podcast
          │
          ▼
 PipelineOrchestrator.start("podcast")
          │
 ┌────────┴────────────────────────────────────────────────────────┐
 │ PodcastPipeline (extends StepBasedPipeline)                     │
 │                                                                 │
 │  Step 1: scrape() ──→ PodcastScraper ──→ RawSignal[]           │
 │     ▼                                                           │
 │  Step 2: dedupe() ──→ URL hash 去重                             │
 │     ▼                                                           │
 │  Step 3: transcribe() ──→ TranscriptionService (异步+可取消)    │
 │     │    asyncio.to_thread() 包装同步 SDK                       │
 │     │    ctx.check_cancelled() 在每次轮询间检查                  │
 │     ▼                                                           │
 │  Step 4: analyze() ──→ PodcastAnalyzer via AIService            │
 │     │    failure_policy=RETRY_THEN_SKIP                         │
 │     ▼                                                           │
 │  Step 5: save() ──→ DB 批量写入                                 │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 5. 接口定义

### 5.1 AIService 接口

```python
class IAIService(ABC):
    """AI 服务接口"""

    @abstractmethod
    async def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        failure_policy: FailurePolicy,
        fallback_value: Optional[dict] = None,
        task_id: Optional[str] = None,
    ) -> AICallResult:
        ...

    @abstractmethod
    async def call_text(
        self,
        system_prompt: str,
        user_prompt: str,
        failure_policy: FailurePolicy,
        task_id: Optional[str] = None,
    ) -> AICallResult:
        ...

    @abstractmethod
    def get_daily_cost(self) -> float:
        ...
```

### 5.2 Pipeline 接口

```python
class IPipeline(ABC):
    """流水线接口"""

    @abstractmethod
    async def run(self, ctx: PipelineContext) -> PipelineStats:
        ...
```

所有 4 个 Pipeline 继承 `StepBasedPipeline` 并实现 `scrape()` 和 `save()`:

| Pipeline | scrape() | 额外步骤 | save() |
|----------|----------|---------|--------|
| ArticlePipeline | RSSScraper | extract + filter + analyze + translate | Resource(type=article) |
| TwitterPipeline | XGoingScraper | (无) | Resource(type=tweet) |
| PodcastPipeline | PodcastScraper | transcribe + analyze | Resource(type=podcast) |
| VideoPipeline | VideoScraper | transcribe + analyze | Resource(type=video) |

### 5.3 管理 API 接口

```
# 流水线控制
POST   /api/sources/trigger/{type}?dry_run=false&feed_filter=
POST   /api/sources/cancel/{type}
POST   /api/sources/retry/{pipeline_id}
GET    /api/sources/pipeline-status

# 已有 (保持不变)
GET    /api/sources/status
GET    /api/sources/funnel
GET    /api/sources/runs
POST   /api/sources/toggle/{type}
```

---

## 6. 分阶段实施计划

### Phase 1: 基础设施 (P0)

**目标**: 修复最关键的转写和 AI 失败问题

| # | 任务 | 改动文件 | 依赖 |
|---|------|---------|------|
| 1.1 | 创建 AIService + FailurePolicy | `services/ai_service.py` (新) | 无 |
| 1.2 | 创建 CostTracker | `services/ai_service.py` 内 | 1.1 |
| 1.3 | UnifiedFilter 迁移到 AIService | `processors/unified_filter.py` | 1.1 |
| 1.4 | 创建 TranscriptionService | `processors/transcription_service.py` (新) | 无 |
| 1.5 | PodcastPipeline 使用新 TranscriptionService | `tasks/pipeline.py` | 1.4 |
| 1.6 | 启动时配置校验 | `startup.py` | 1.4 |

**交付物**: AIService 统一调用层 + 转写系统可用

### Phase 2: 可观测性 (P1)

**目标**: 结构化日志 + 实时状态追踪

| # | 任务 | 改动文件 | 依赖 |
|---|------|---------|------|
| 2.1 | 创建 PipelineContext + CancellationToken | `tasks/pipeline_context.py` (新) | 无 |
| 2.2 | 创建 PipelineOrchestrator | `tasks/orchestrator.py` (新) | 2.1 |
| 2.3 | 流水线 print() → structlog 迁移 | `tasks/pipeline.py`, 所有 processors | 无 |
| 2.4 | scheduler_jobs.py 迁移到 Orchestrator | `scheduler_jobs.py` | 2.2 |
| 2.5 | 管理 API 增强 (cancel/status) | `api/sources.py` | 2.2 |

**交付物**: 实时状态可查 + 结构化日志 + 真正的暂停/取消

### Phase 3: 可靠性 (P1)

**目标**: ContentExtractor 增强 + Pipeline 统一

| # | 任务 | 改动文件 | 依赖 |
|---|------|---------|------|
| 3.1 | ContentExtractor 添加重试 + Jina 降级 | `scrapers/content_extractor.py` | 无 |
| 3.2 | BrowserPool 实现 | `scrapers/content_extractor.py` | 3.1 |
| 3.3 | Analyzer 迁移到 AIService | `processors/analyzer.py` | Phase 1 |
| 3.4 | Translator 迁移到 AIService | `processors/translator.py` | Phase 1 |
| 3.5 | PodcastAnalyzer 迁移到 AIService | `processors/podcast_analyzer.py` | Phase 1 |
| 3.6 | SourceHealthChecker 增强 | `services/source_health.py` | 无 |

**交付物**: 全文提取可靠 + 所有 AI 调用统一

### Phase 4: 代码清理 (P2)

**目标**: 删除重复代码，统一模型

| # | 任务 | 改动文件 | 依赖 |
|---|------|---------|------|
| 4.1 | 4 个 Pipeline 迁移到 StepBasedPipeline | `tasks/pipeline.py` → 拆分为独立文件 | Phase 2+3 |
| 4.2 | 删除 pipeline.py 中的重复 Stats 类 | `tasks/pipeline.py` | 4.1 |
| 4.3 | 删除弃用的过滤器 | `processors/filter.py`, `initial_filter.py` | Phase 1 |
| 4.4 | 统一 Source/SourceConfig 模型 | `models/source.py`, `source_config.py` | 无 |
| 4.5 | DataTracker 扩展到所有 Pipeline | `services/data_tracker.py` | 4.1 |
| 4.6 | 添加 dry-run 模式 | `tasks/base_pipeline.py` | 4.1 |

**交付物**: 代码量减少约 30%，单一事实源

---

## 7. 向后兼容性

### 7.1 兼容策略

| 组件 | 策略 | 说明 |
|------|------|------|
| AIService | 并行共存 | 新旧调用方式同时工作，通过构造函数注入切换 |
| TranscriptionService | 配置开关 | `use_new_transcriber: true` 切换 |
| PipelineOrchestrator | 渐进替换 | 先用于手动触发，验证后替换 APScheduler 入口 |
| structlog | 无冲突 | structlog 和 print() 可共存 |
| StepBasedPipeline | 逐个迁移 | 先迁移最简单的 TwitterPipeline，验证后迁移其他 |

### 7.2 不改动的部分

以下模块 **不在本次重构范围内**:
- 前端代码 (frontend/)
- 数据库 Schema (models/ 的表结构不变)
- API 响应格式 (现有端点保持不变)
- Redis 缓存策略
- 飞书集成 (DataTracker/FeishuService)
- Admin API (admin/)
- Deep Research 系统

### 7.3 数据迁移

**无需数据迁移**。所有改动都是行为变更，不涉及表结构修改。

---

## 8. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| AIService 引入新 bug 导致过滤行为异常 | 中 | 高 | 先对 UnifiedFilter 做 A/B 测试，监控通过率变化 |
| TranscriptionService 阿里云 API 变更 | 低 | 高 | 保留旧 Transcriber 作为 fallback |
| BrowserPool 内存泄漏 | 中 | 中 | 设置 pool 最大生命周期，定期重建 |
| Orchestrator 重叠执行防护失败 | 低 | 中 | 使用 DB 级锁作为二级保护 |
| structlog 迁移遗漏导致日志丢失 | 低 | 低 | 分模块迁移，保留 print() 直到确认 structlog 工作正常 |
| Phase 4 代码清理引入回归 | 中 | 高 | Phase 4 开始前对所有 Pipeline 添加集成测试 |

---

## 9. 新增文件清单

| 文件路径 | 职责 | Phase |
|---------|------|-------|
| `backend/app/services/ai_service.py` | 统一 AI 调用层 | 1 |
| `backend/app/processors/transcription_service.py` | 新版转写服务 | 1 |
| `backend/app/tasks/pipeline_context.py` | 流水线运行上下文 | 2 |
| `backend/app/tasks/orchestrator.py` | 流水线编排器 | 2 |

**总计 4 个新文件**，其余均为修改现有文件。
