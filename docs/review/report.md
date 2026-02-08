# Phase 1 代码审查报告

> Reviewer: Opus (Reviewer Agent)
> Date: 2026-02-08
> Scope: Phase 1 基础设施 — AIService + TranscriptionService + 迁移集成

---

## 审查摘要

**有条件通过** — 发现 1 个 CRITICAL 问题，2 个 HIGH 问题，5 个 MEDIUM 问题。

CRITICAL 问题涉及 `TranscriptionService` 的凭证映射语义错误，可能导致转写 API 认证失败。修复此项后可上线。

### 关键发现

| 级别 | 数量 | 分布 |
|------|------|------|
| CRITICAL | 1 | transcription_service.py |
| HIGH | 2 | transcription_service.py, ai_service.py |
| MEDIUM | 5 | ai_service.py (2), unified_filter.py (1), pipeline.py (1), startup.py (1) |

---

## 文件审查

### 1. ai_service.py

#### CRITICAL 问题

无。

#### HIGH 问题

**H1.1 — Token 估算过于粗略，可能严重偏离实际成本**

- 位置: `call_json()` 第 201-206 行, `call_text()` 第 271-275 行
- 问题: 使用 `len(prompt) // 4` 粗略估算 Token 数。对于中文内容（Signal 的主要内容语言），1 个汉字通常消耗 2-3 个 Token，而非 0.25 个。这会导致中文 prompt 的成本被低估 8-12 倍。
- 影响: CostTracker 的每日成本汇总与实际偏差巨大，失去参考价值。
- 建议: 从 LLMClient 的响应中获取实际 `usage.prompt_tokens` 和 `usage.completion_tokens`（OpenAI 兼容 API 均返回此字段）。如果 LLMClient 不暴露此数据，短期可用 `tiktoken` 或保留粗略估算但在日志中标记 `estimated=True`。

#### MEDIUM 问题

**M1.1 — `_parse_json()` 策略 3 和策略 4 顺序不符合注释**

- 位置: 第 317-378 行
- 问题: 注释声明优先级是 "代码块 -> 正则 -> 大括号匹配"，但实际实现是 "代码块 -> 大括号匹配 -> 正则(无嵌套) -> 直接 json.loads"。策略 3 (大括号匹配) 和策略 4 (正则) 的编号/注释与 `call_json()` docstring 中的 "正则 -> 大括号匹配" 描述相反。
- 影响: 低。实际的优先级顺序是合理的（大括号匹配优于简单正则），但注释不准确会误导后续维护者。
- 建议: 更新注释和 docstring 使其与实际实现一致。

**M1.2 — `PENDING_REVIEW` 策略返回 `success=False` 但 `data` 非空**

- 位置: `_apply_failure_policy()` 第 396-400 行
- 问题: `PENDING_REVIEW` 返回 `AICallResult(success=False, data={"status": "pending_review"})`。调用方如果只检查 `result.success`，会忽略 `data` 中的信息；如果检查 `result.data`，可能误以为调用成功。这种 `success=False` + `data` 非空的组合语义模糊。
- 影响: 当前未有模块使用 `PENDING_REVIEW` 策略，所以暂无实际影响。但后续使用时可能引起混淆。
- 建议: 考虑为 `AICallResult` 增加 `status` 字段 (如 `"success" | "failed" | "pending_review"`)，或在 `PENDING_REVIEW` 时不设 `data`，改为在 `error` 字段中标记。

#### 优点

- `AICallResult` 使用 `frozen=True` dataclass，符合不可变模式要求
- `FailurePolicy` 枚举值与 design.md 完全一致 (REJECT/PENDING_REVIEW/RETRY_THEN_SKIP/FALLBACK)
- 多策略 JSON 解析比现有各模块散落的单一解析策略健壮得多
- structlog 结构化日志命名规范 (`ai.call_json.success`, `ai.call_json.failed`) 符合设计规范
- `CostTracker` 的每日重置逻辑正确，避免跨日累积
- 延迟导入 `llm_client` 避免循环依赖，设计周到
- `duration_ms` 字段使用 `time.monotonic()` 而非 `time.time()`，不受系统时钟调整影响
- `JSONParseError` 继承 `Exception` 而非 `BaseException`，错误处理粒度正确

---

### 2. transcription_service.py

#### CRITICAL 问题

**C2.1 — AccessKeyCredential 参数语义错误：`api_key` 不等于 `access_key_id`**

- 位置: `_get_client()` 第 145-149 行
- 问题:
  ```python
  credentials = AccessKeyCredential(
      self._config.api_key,    # TingwuConfig.api_key = TINGWU_API_KEY
      self._config.app_key,    # TingwuConfig.app_key = TINGWU_APP_KEY
  )
  ```
  旧版 `Transcriber` (transcriber.py) 使用 `TINGWU_ACCESS_KEY_ID` + `TINGWU_ACCESS_KEY_SECRET` 创建 `AccessKeyCredential`，并且单独读取 `TINGWU_APP_KEY` 作为业务参数传入请求体。

  新版将 `TingwuConfig.api_key` (别名 `TINGWU_API_KEY`) 当作 `AccessKeyCredential` 的第一个参数，`TingwuConfig.app_key` (别名 `TINGWU_APP_KEY`) 当作第二个参数。

  但 `AccessKeyCredential(access_key_id, access_key_secret)` 需要的是阿里云 AccessKey 对 (AK/SK)，而 `TINGWU_APP_KEY` 是通义听悟的业务 AppKey，不是 AccessKey Secret。这会导致 API 认证直接失败。

- 根因: `TingwuConfig` 只定义了 `api_key` 和 `app_key` 两个字段，但阿里云 SDK 需要三个凭证: `access_key_id`, `access_key_secret`, `app_key`。Config 定义缺少 `access_key_secret` 字段。
- 影响: **转写功能完全不可用**。所有对通义听悟 API 的调用都将因 403 认证失败而中止。
- 修复方案:
  1. `TingwuConfig` 增加 `access_key_secret` 字段 (别名 `TINGWU_ACCESS_KEY_SECRET`)
  2. 将 `api_key` 别名改回 `TINGWU_ACCESS_KEY_ID`（或添加新字段 `access_key_id`）
  3. `_get_client()` 使用 `AccessKeyCredential(config.access_key_id, config.access_key_secret)`
  4. `_submit_task_sync()` 中的 `AppKey` 使用 `config.app_key`（这部分是正确的）

#### HIGH 问题

**H2.1 — `_daily_count` 在转写失败时仍未计入，可能导致限额被绕过**

- 位置: `transcribe()` 第 220 行
- 问题: `self._daily_count += 1` 仅在转写成功后才执行。如果 `_submit_task_async()` 成功但 `_poll_task_async()` 超时/失败，该次调用不会被计入每日限额。但实际上 API 调用已经发生并消耗了资源。
- 影响: 在 API 持续超时的场景下，可能反复提交任务而不受限额控制，浪费通义听悟 API 额度。
- 建议: 在 `_submit_task_async()` 成功后立即 `self._daily_count += 1`，而非在最终结果返回后。

#### MEDIUM 问题

无。

#### 优点

- `CancellationToken` 基于 `threading.Event`，与 design.md 规格完全一致
- `asyncio.to_thread()` 包装同步 SDK 调用，正确解决了事件循环阻塞问题
- AcsClient 单例复用 (`_get_client()`)，避免了旧版每次轮询重建客户端的问题
- `_poll_task_async()` 使用 `asyncio.sleep()` 而非 `time.sleep()`，不阻塞事件循环
- 轮询日志 `attempts % 12 == 0` (每分钟一次) 控制了日志量
- `TranscriptionResult` 使用 `frozen=True`，符合不可变模式
- `_download_result()` 使用 `httpx.AsyncClient` 异步下载，与整体异步架构一致
- 结构化错误返回 (`TranscriptionError`) 替代了旧版的 `return None`

---

### 3. unified_filter.py (修改)

#### CRITICAL 问题

无。

#### HIGH 问题

无。

#### MEDIUM 问题

**M3.1 — 全局单例 `unified_filter` 未注入 `ai_service`，新路径永远不会被激活**

- 位置: 第 358-359 行
- 问题:
  ```python
  # 全局单例
  unified_filter = UnifiedFilter()
  ```
  全局单例创建时 `ai_service=None`，而 `pipeline.py` 第 207 行直接创建新实例:
  ```python
  unified_filter = UnifiedFilter(prompt_service=prompt_service)
  ```
  也未传入 `ai_service`。这意味着在当前集成中，新的 `_llm_score_via_ai_service()` 路径永远不会被执行，所有调用仍走旧路径 (失败放行 `score=3`)。

- 影响: Phase 1 的核心目标之一 —— "UnifiedFilter 失败策略从放行改为 REJECT" —— 实际上未生效。系统行为与重构前完全相同。
- 建议: `pipeline.py` 中创建 `UnifiedFilter` 时需要传入 `AIService` 实例:
  ```python
  ai_service = AIService()
  unified_filter = UnifiedFilter(prompt_service=prompt_service, ai_service=ai_service)
  ```

#### 优点

- 新旧路径并存的兼容策略设计正确 —— 有 `ai_service` 走新路径，无则走旧路径
- `_llm_score_via_ai_service()` 正确使用 `FailurePolicy.REJECT`，失败时返回 `score=0, passed=False`
- `FilterResult` 保持原有字段不变，向后兼容
- TYPE_CHECKING 条件导入避免循环依赖

---

### 4. pipeline.py (修改)

#### CRITICAL 问题

无。

#### HIGH 问题

无。

#### MEDIUM 问题

**M4.1 — PodcastPipeline 新旧转写器的 fallback 逻辑有条件竞争**

- 位置: 第 1002-1037 行
- 问题: `use_new_transcriber` 和 `new_transcription_service` 是两个独立变量。在 `if use_new_transcriber and new_transcription_service is not None:` (第 1065 行) 的判断中，理论上存在 `use_new_transcriber=True` 但 `new_transcription_service=None` 的不可能路径（因为赋值是原子的），但这种双重检查表明对状态同步不够自信。
- 影响: 低。当前逻辑正确，但可以简化。
- 建议: 只使用一个变量 `transcription_service: Optional[TranscriptionService]`，通过 `is not None` 判断是否使用新版。

#### 优点

- 新旧转写器的 fallback 策略实现正确：先尝试新版，不可用则降级到旧版
- 新版 `TranscriptionService.is_available()` 校验在使用前调用，避免运行时才发现配置问题
- 新旧转写器的调用接口保持一致 (都传入 `media_url`, `media_type`)
- `ImportError` 异常被捕获，缺少模块时优雅降级

---

### 5. startup.py (修改)

#### CRITICAL 问题

无。

#### HIGH 问题

无。

#### MEDIUM 问题

**M5.1 — 配置校验不阻止启动，但 OPENAI_API_KEY 缺失应该是 CRITICAL**

- 位置: 第 34-97 行, 注释 "不会阻止启动，仅输出警告/错误日志"
- 问题: design.md 中 `validate_config_on_startup()` 的规格是：有 `errors` 时 `raise ConfigurationError`。但实际实现仅记录日志，不抛出异常。这意味着即使 `OPENAI_API_KEY` 未配置，系统也会正常启动，然后所有 LLM 调用在运行时才失败。
- 影响: 中。design.md 明确要求 "errors 时阻止启动"，当前实现偏离了设计规格。但不阻止启动的行为在某些部署场景下 (如只跑前端) 可能是合理的。
- 建议: 与 Architect 确认意图。如果确实不应阻止启动，更新 design.md 说明理由。如果应阻止启动，添加 `raise` 逻辑。

#### 优点

- 使用 structlog 结构化日志，符合设计规范
- 校验项覆盖 LLM、转写、OPML、数据库四个维度
- OPML 校验循环简洁，使用 `getattr` 安全访问属性
- `validate_config_on_startup()` 在 `startup_event()` 中调用位置正确（数据库初始化之前）

---

## 与设计方案一致性

| 设计规格 | 实际实现 | 一致性 | 备注 |
|---------|---------|--------|------|
| AIService 接口 (call_json/call_text/get_daily_cost) | 完全实现 | OK | 额外增加了 `get_cost_summary()` |
| FailurePolicy 枚举 (REJECT/PENDING_REVIEW/RETRY_THEN_SKIP/FALLBACK) | 完全匹配 | OK | |
| AICallResult 字段 (success/data/raw_response/error/tokens_used/cost_usd/retries) | 基本匹配 | OK | 额外增加了 `duration_ms`，`tokens_used` 始终为 0（未从 API 获取） |
| CostTracker.estimate() 签名 | 不匹配 | **偏差** | design.md 是 `estimate(response, task_id)`，实际是 `estimate(input_tokens, output_tokens, model, task_id)` |
| TranscriptionService.transcribe() 签名 | 基本匹配 | OK | 额外增加了 `max_daily` 参数 |
| asyncio.to_thread() 包装 | 已实现 | OK | `_submit_task_async()` 和 `_poll_task_async()` 都使用 |
| CancellationToken 基于 threading.Event | 已实现 | OK | |
| UnifiedFilter REJECT 策略 | 代码存在但未激活 | **偏差** | pipeline.py 未传入 ai_service，见 M3.1 |
| 启动时 ConfigurationError | 未实现 | **偏差** | 仅日志，不抛异常，见 M5.1 |
| AcsClient 单例复用 | 已实现 | OK | `_get_client()` 延迟初始化 + 缓存 |
| AccessKeyCredential 凭证 | **语义错误** | **CRITICAL** | 见 C2.1 |

---

## 综合建议 (按优先级排序)

### 必须修复 (上线阻塞)

1. **[C2.1] 修复 TranscriptionService 的凭证映射**
   - `TingwuConfig` 增加 `access_key_secret` 字段
   - `_get_client()` 使用正确的 AK/SK 组合
   - 验证与旧版 `Transcriber` 的环境变量兼容性

### 强烈建议修复

2. **[M3.1] 在 pipeline.py 中注入 AIService 到 UnifiedFilter**
   - 否则 Phase 1 核心目标 "失败策略改为 REJECT" 形同虚设

3. **[H2.1] 将 `_daily_count` 递增移到任务提交成功后**
   - 防止超时场景下绕过限额控制

4. **[H1.1] 改进 Token 估算**
   - 短期: 从 LLMClient 暴露实际 Token 使用量
   - 长期: 集成 `tiktoken` 或在 `AICallResult` 中携带实际 usage

### 建议修复

5. **[M5.1] 确认启动校验的阻塞行为**
   - 与 Architect 对齐，更新 design.md 或代码

6. **[M1.1] 修正 `_parse_json()` 注释与实际顺序**

7. **[M1.2] 明确 `PENDING_REVIEW` 的返回语义**

8. **[M4.1] 简化 PodcastPipeline 的转写器选择逻辑**
