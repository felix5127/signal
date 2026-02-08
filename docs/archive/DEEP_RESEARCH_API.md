# Deep Research API 测试文档

## API 端点

### 1. 生成深度研究报告

**请求**:
```bash
POST /api/signals/{signal_id}/deep-research?strategy=lightweight&force=false
```

**参数**:
- `signal_id` (路径参数): 信号 ID
- `strategy` (查询参数): 研究策略，可选值:
  - `lightweight` (默认): V1 轻量级引擎
  - `full_agent`: V2 完整 Multi-Agent (暂未实现)
  - `auto`: 自动选择策略
- `force` (查询参数): 是否强制重新生成，默认 `false`

**响应示例**:
```json
{
  "status": "processing",
  "message": "Deep research report generation started in background",
  "signal_id": 1,
  "strategy": "lightweight",
  "estimated_time_seconds": "60-120"
}
```

或者（如果已有缓存）:
```json
{
  "status": "cached",
  "message": "Report already exists and is still fresh",
  "signal_id": 1,
  "generated_at": "2025-12-30T10:30:00",
  "cache_age_hours": 2.5
}
```

---

### 2. 获取深度研究报告

**请求**:
```bash
GET /api/signals/{signal_id}/deep-research
```

**参数**:
- `signal_id` (路径参数): 信号 ID

**响应示例**:
```json
{
  "signal_id": 1,
  "title": "Show HN: Z80-μLM, a 'Conversational AI' That Fits in 40KB",
  "content": "## 1️⃣ 执行摘要\n\n...",
  "generated_at": "2025-12-30T10:30:00",
  "tokens_used": 2500,
  "cost_usd": 0.0285,
  "strategy": "lightweight",
  "sources": [
    "https://example.com/article1",
    "https://example.com/article2"
  ],
  "metadata": {
    "version": "v1-lightweight",
    "questions": [
      "Z80-μLM 的核心技术原理是什么?",
      "Z80-μLM 有哪些竞品或替代方案?",
      "Z80-μLM 的实际应用场景和案例?"
    ]
  }
}
```

**错误响应**:
- `404 Signal not found`: 信号不存在
- `404 Deep research report not generated yet`: 报告尚未生成

---

## 测试示例

### 1. 触发生成报告
```bash
curl -X POST "http://localhost:8000/api/signals/1/deep-research?strategy=lightweight"
```

### 2. 查询报告状态
等待 60-120 秒后:
```bash
curl "http://localhost:8000/api/signals/1/deep-research"
```

### 3. 强制重新生成
```bash
curl -X POST "http://localhost:8000/api/signals/1/deep-research?strategy=lightweight&force=true"
```

---

## 工作流程

1. **用户触发生成**: 前端调用 `POST /api/signals/{id}/deep-research`
2. **后台异步执行**: FastAPI BackgroundTasks 在后台运行生成任务
3. **前端轮询**: 每 5-10 秒调用 `GET /api/signals/{id}/deep-research` 检查是否完成
4. **展示结果**: 一旦返回 200，展示 Markdown 格式的报告

---

## 已知限制

1. **Kimi API 超时**: 生成长报告时可能超时（详见 [KNOWN_ISSUES.md](../KNOWN_ISSUES.md)）
2. **无进度反馈**: 后台任务无法返回实时进度
3. **失败重试**: 如果生成失败，需要手动重新触发

---

## 后续优化

- [ ] 实现 WebSocket 推送进度
- [ ] 添加任务队列 (Celery/RQ)
- [ ] 支持批量生成
- [ ] 错误自动重试机制
