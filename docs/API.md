# Signal API 参考

> 版本: 1.0 | 更新: 2026-01-30 | Base URL: `http://localhost:8000/api`

本文档定义 Signal 所有 REST API 端点的请求/响应格式。

---

## 目录

1. [概述](#1-概述)
2. [Resources API](#2-resources-api)
3. [Research API](#3-research-api)
4. [Podcast API](#4-podcast-api)
5. [Admin API](#5-admin-api)
6. [其他 API](#6-其他-api)

---

## 1. 概述

### 1.1 认证

大部分 API 无需认证。管理后台 API 需要 JWT Token:

```http
Authorization: Bearer <token>
```

### 1.2 通用响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "错误描述",
  "detail": "详细信息"
}
```

### 1.3 分页参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页数量 |

### 1.4 缓存策略

| API 类型 | TTL | 描述 |
|----------|-----|------|
| 列表 | 5min | 资源列表 |
| 详情 | 10min | 单条资源 |
| 统计 | 1min | 统计数据 |

---

## 2. Resources API

### 2.1 获取资源列表

```http
GET /api/resources
```

**查询参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `page` | int | 页码 |
| `page_size` | int | 每页数量 |
| `type` | string | 内容类型 (article/podcast/tweet/video) |
| `domain` | string | 领域筛选 |
| `source` | string | 来源筛选 |
| `language` | string | 语言 (zh/en) |
| `min_score` | int | 最低 LLM 评分 |
| `days` | int | 最近 N 天 |
| `featured` | bool | 只看精选 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "GPT-5 发布预览",
        "title_translated": "GPT-5 发布预览",
        "url": "https://openai.com/gpt-5",
        "type": "article",
        "source_name": "OpenAI Blog",
        "source_icon_url": "https://...",
        "one_sentence_summary": "OpenAI 发布 GPT-5...",
        "summary_zh": "摘要内容...",
        "main_points_zh": ["观点1", "观点2"],
        "llm_score": 5,
        "score": 92,
        "is_featured": true,
        "featured_reason_zh": "推荐理由",
        "published_at": "2026-01-30T10:00:00Z",
        "created_at": "2026-01-30T10:30:00Z"
      }
    ],
    "total": 1234,
    "page": 1,
    "page_size": 20,
    "total_pages": 62
  }
}
```

---

### 2.2 获取资源详情

```http
GET /api/resources/{id}
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "title": "GPT-5 发布预览",
    "url": "https://openai.com/gpt-5",
    "type": "article",
    "source_name": "OpenAI Blog",
    "summary": "详细摘要...",
    "summary_zh": "中文摘要...",
    "main_points": ["Point 1", "Point 2"],
    "main_points_zh": ["观点1", "观点2"],
    "key_quotes": [
      {"quote": "...", "quote_zh": "..."}
    ],
    "tags": ["AI", "LLM"],
    "deep_research": "深度研究报告...",
    "published_at": "2026-01-30T10:00:00Z"
  }
}
```

---

### 2.3 搜索资源

```http
GET /api/resources/search
```

**查询参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `q` | string | 搜索关键词 (必需) |
| `page` | int | 页码 |
| `page_size` | int | 每页数量 |

**响应**: 同资源列表

---

### 2.4 生成深度研究

```http
POST /api/resources/{id}/deep-research
```

**请求体**:
```json
{
  "strategy": "LIGHTWEIGHT",
  "force": false
}
```

**参数说明**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `strategy` | string | 研究策略 (LIGHTWEIGHT/AUTO) |
| `force` | bool | 强制重新生成 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "research": "# 深度研究报告\n\n## 摘要\n...",
    "tokens_used": 4500,
    "cost_usd": 0.12,
    "cached": false
  }
}
```

---

## 3. Research API

研究工作台 API，支持 SSE 流式响应。

### 3.1 项目管理

#### 获取项目列表

```http
GET /api/research/projects
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "AI Agent 研究",
        "description": "研究 AI Agent 架构",
        "status": "active",
        "source_count": 5,
        "output_count": 2,
        "created_at": "2026-01-20T10:00:00Z",
        "updated_at": "2026-01-30T15:00:00Z"
      }
    ]
  }
}
```

#### 创建项目

```http
POST /api/research/projects
```

**请求体**:
```json
{
  "name": "项目名称",
  "description": "项目描述"
}
```

#### 获取项目详情

```http
GET /api/research/projects/{project_id}
```

#### 归档项目

```http
POST /api/research/projects/{project_id}/archive
```

#### 删除项目

```http
DELETE /api/research/projects/{project_id}
```

---

### 3.2 源材料管理

#### 获取材料列表

```http
GET /api/research/projects/{project_id}/sources
```

#### 添加 URL 源材料

```http
POST /api/research/projects/{project_id}/sources/url
```

**请求体**:
```json
{
  "url": "https://example.com/article",
  "title": "可选标题"
}
```

#### 上传文件

```http
POST /api/research/projects/{project_id}/sources/upload
Content-Type: multipart/form-data
```

**表单字段**:
- `file`: 文件 (PDF/音频/视频)
- `title`: 标题 (可选)

#### 导入系统资源

```http
POST /api/research/projects/{project_id}/sources/import
```

**请求体**:
```json
{
  "resource_id": "uuid"
}
```

#### 删除材料

```http
DELETE /api/research/sources/{source_id}
```

---

### 3.3 研究任务

#### 执行研究 (SSE 流式)

```http
POST /api/research/projects/{project_id}/research
Accept: text/event-stream
```

**请求体**:
```json
{
  "query": "分析 AI Agent 的核心架构模式",
  "use_web_search": true,
  "use_vector_search": true
}
```

**SSE 事件格式**:
```
event: progress
data: {"step": "searching", "message": "搜索相关材料..."}

event: tool_call
data: {"tool": "tavily_search", "query": "AI Agent architecture"}

event: content
data: {"text": "根据分析..."}

event: done
data: {"tokens_used": 3500, "cost_usd": 0.08}
```

#### 获取任务状态

```http
GET /api/research/tasks/{task_id}
```

---

### 3.4 对话会话

#### 创建会话

```http
POST /api/research/projects/{project_id}/chat/sessions
```

**请求体**:
```json
{
  "title": "会话标题",
  "source_ids": ["uuid1", "uuid2"]
}
```

#### 发送消息 (SSE 流式)

```http
POST /api/research/chat/sessions/{session_id}/messages
Accept: text/event-stream
```

**请求体**:
```json
{
  "content": "这篇文章的核心观点是什么?"
}
```

#### 获取会话历史

```http
GET /api/research/chat/sessions/{session_id}
```

---

### 3.5 研究输出

#### 获取输出列表

```http
GET /api/research/projects/{project_id}/outputs
```

#### 生成摘要报告

```http
POST /api/research/projects/{project_id}/outputs/summary
```

#### 生成播客

```http
POST /api/research/projects/{project_id}/outputs/podcast
```

---

## 4. Podcast API

播客生成 API，支持 SSE 流式响应。

### 4.1 文本转播客 (SSE)

```http
POST /api/podcast/generate
Accept: text/event-stream
```

**请求体**:
```json
{
  "text": "要转换的文本内容...",
  "title": "播客标题",
  "host_voice": "zhiyan",
  "guest_voice": "zhimi",
  "style": "conversational"
}
```

**SSE 事件**:
```
event: outline
data: {"title": "...", "sections": [...]}

event: dialogue
data: {"segments": [...]}

event: audio_progress
data: {"progress": 50, "current_segment": 5, "total_segments": 10}

event: done
data: {"audio_url": "https://...", "duration": 300}
```

---

### 4.2 项目转播客 (SSE)

```http
POST /api/podcast/project/{project_id}/generate
Accept: text/event-stream
```

基于研究项目的所有材料生成播客。

---

### 4.3 获取音色列表

```http
GET /api/podcast/voices
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "voices": [
      {"id": "zhiyan", "name": "知言", "language": "zh", "gender": "female"},
      {"id": "zhimi", "name": "知米", "language": "zh", "gender": "male"},
      {"id": "emily", "name": "Emily", "language": "en", "gender": "female"}
    ]
  }
}
```

---

## 5. Admin API

管理后台 API，需要认证。

### 5.1 审核 API

#### 获取待审核列表

```http
GET /api/admin/review/list
```

**查询参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `status` | string | 状态筛选 (pending/approved/rejected) |
| `source` | string | 来源筛选 |
| `date_from` | date | 开始日期 |
| `date_to` | date | 结束日期 |
| `page` | int | 页码 |
| `page_size` | int | 每页数量 |

#### 执行审核

```http
POST /api/admin/review/{resource_id}/action
```

**请求体**:
```json
{
  "action": "approve",
  "comment": "审核备注"
}
```

**action 取值**:
- `approve`: 通过
- `reject`: 拒绝
- `restore`: 恢复

#### 批量审核

```http
POST /api/admin/review/batch
```

**请求体**:
```json
{
  "resource_ids": ["uuid1", "uuid2"],
  "action": "approve"
}
```

#### 获取审核统计

```http
GET /api/admin/review/stats
```

---

### 5.2 数据源管理 API

#### 获取数据源列表

```http
GET /api/admin/sources
```

**查询参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `type` | string | 类型筛选 |
| `enabled` | bool | 启用状态 |
| `is_whitelist` | bool | 白名单筛选 |

#### 创建数据源

```http
POST /api/admin/sources
```

**请求体**:
```json
{
  "name": "数据源名称",
  "type": "blog",
  "url": "https://example.com/feed",
  "enabled": true,
  "is_whitelist": false
}
```

#### 更新数据源

```http
PUT /api/admin/sources/{id}
```

#### 删除数据源

```http
DELETE /api/admin/sources/{id}
```

#### 切换启用状态

```http
POST /api/admin/sources/{id}/toggle
```

#### 设置白名单

```http
PUT /api/admin/sources/{id}/whitelist
```

**请求体**:
```json
{
  "is_whitelist": true
}
```

#### 获取数据源统计

```http
GET /api/admin/sources/{id}/stats
```

---

### 5.3 统计 API

#### 获取总览统计

```http
GET /api/admin/stats/overview
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "total_resources": 12345,
    "status_distribution": {
      "pending": 100,
      "approved": 10000,
      "rejected": 2245
    },
    "today_stats": {
      "collected": 150,
      "approved": 80,
      "rejected": 70
    },
    "avg_llm_score": 3.8,
    "source_stats": {
      "rss": 5000,
      "twitter": 2000,
      "podcast": 500
    }
  }
}
```

#### 获取每日统计

```http
GET /api/admin/stats/daily?days=30
```

#### 获取数据源统计

```http
GET /api/admin/stats/sources
```

#### 获取评分分布

```http
GET /api/admin/stats/score-distribution
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "distribution": {
      "0": 500,
      "1": 800,
      "2": 1500,
      "3": 3000,
      "4": 4000,
      "5": 2545
    }
  }
}
```

---

### 5.4 Prompt 管理 API

#### 获取 Prompt 列表

```http
GET /api/admin/prompts
```

**查询参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `type` | string | 类型 (filter/analyzer/translator) |

#### 获取活跃 Prompt

```http
GET /api/admin/prompts/active?type=filter
```

#### 创建 Prompt

```http
POST /api/admin/prompts
```

**请求体**:
```json
{
  "name": "Filter V2",
  "type": "filter",
  "system_prompt": "你是一个内容质量评估专家...",
  "user_prompt_template": "请评估以下内容:\n\n标题: {title}\n内容: {content}"
}
```

#### 激活 Prompt

```http
POST /api/admin/prompts/{id}/activate
```

---

## 6. 其他 API

### 6.1 日周精选

#### 获取今日精选

```http
GET /api/digest/today
```

#### 获取本周精选

```http
GET /api/digest/week
```

#### 获取历史周刊列表

```http
GET /api/digest/weeks
```

---

### 6.2 Newsletter

#### 获取周刊列表

```http
GET /api/newsletters
```

#### 获取周刊详情

```http
GET /api/newsletters/{id}
```

---

### 6.3 RSS 订阅

```http
GET /api/feeds/{type}
```

**type 取值**:
- `all`: 全部
- `featured`: 精选
- `article`: 文章
- `podcast`: 播客

**响应**: RSS 2.0 / Atom 1.0 XML

---

### 6.4 健康检查

```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-30T10:00:00Z"
}
```

---

### 6.5 任务管理

#### 获取任务状态

```http
GET /api/tasks/{task_id}
```

#### 触发流水线

```http
POST /api/tasks/pipeline/trigger
```

**请求体**:
```json
{
  "pipeline": "article",
  "source_type": "rss"
}
```

---

## 附录: 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

---

*API 变更时请同步更新此文档*
