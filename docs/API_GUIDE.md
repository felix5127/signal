# Signal Hunter API 使用指南

## 📚 目录

1. [快速开始](#快速开始)
2. [认证](#认证)
3. [API端点](#api端点)
4. [错误处理](#错误处理)
5. [代码示例](#代码示例)
6. [Postman集合](#postman集合)

---

## 快速开始

### 基础URL

```
开发环境: http://localhost:8000
生产环境: https://signal.felixwithai.com
```

### 测试API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取信号列表
curl http://localhost:8000/api/signals

# 获取统计信息
curl http://localhost:8000/api/stats
```

---

## 认证

### 当前状态

**目前API认证是可选的**，主要用于未来的扩展。

### JWT认证（准备就绪）

```python
import requests

# 1. 创建JWT token（需要实现登录端点）
token = "your_jwt_token_here"

# 2. 使用token访问API
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/signals",
    headers=headers
)
```

### API密钥认证（用于服务间调用）

```python
import requests

# 使用API密钥
headers = {"X-API-Key": "your_api_key_here"}
response = requests.get(
    "http://localhost:8000/api/signals",
    headers=headers
)
```

---

## API端点

### 1. 信号端点

#### 获取信号列表

```http
GET /api/signals
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|--------|------|
| limit | integer | 否 | 20 | 每页数量（1-100） |
| offset | integer | 否 | 0 | 偏移量 |
| min_score | integer | 否 | - | 最低评分（1-5） |
| source | string | 否 | - | 数据源（单个） |
| sources | string | 否 | - | 数据源（多个，逗号分隔） |
| category | string | 否 | - | 分类 |
| search | string | 否 | - | 搜索关键词 |
| sort_by | string | 否 | created_at | 排序（created_at/final_score） |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "source": "github",
        "title": "Repo Title",
        "url": "https://github.com/user/repo",
        "one_liner": "Short description",
        "summary": "Detailed summary",
        "final_score": 4,
        "heat_score": 80,
        "quality_score": 4,
        "category": "ai",
        "tags": ["ai", "ml"],
        "source_metadata": {},
        "created_at": "2024-01-09T10:00:00"
      }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

**使用示例**:

```bash
# 基础查询
curl "http://localhost:8000/api/signals"

# 筛选高质量信号
curl "http://localhost:8000/api/signals?min_score=4"

# 搜索
curl "http://localhost:8000/api/signals?search=ai"

# 多数据源筛选
curl "http://localhost:8000/api/signals?sources=github,huggingface"

# 按评分排序
curl "http://localhost:8000/api/signals?sort_by=final_score"
```

#### 获取单个信号

```http
GET /api/signals/{signal_id}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "source": "github",
    "title": "Repo Title",
    "url": "https://github.com/user/repo",
    "one_liner": "Short description",
    "summary": "Detailed summary",
    "final_score": 4,
    "heat_score": 80,
    "quality_score": 4,
    "category": "ai",
    "tags": ["ai", "ml"],
    "matched_conditions": ["trending", "high_quality"],
    "source_metadata": {},
    "created_at": "2024-01-09T10:00:00",
    "source_created_at": "2024-01-08T15:30:00"
  }
}
```

#### 生成深度研究报告

```http
POST /api/signals/{signal_id}/deep-research
```

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|--------|------|
| strategy | string | 否 | lightweight | 研究策略（lightweight/full_agent/auto） |
| force | boolean | 否 | false | 强制重新生成 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "status": "processing",
    "message": "Deep research report generation started in background",
    "signal_id": 1,
    "strategy": "lightweight",
    "estimated_time_seconds": "60-120"
  }
}
```

---

### 2. 统计端点

#### 获取统计数据

```http
GET /api/stats
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "total_signals": 1000,
    "by_source": {
      "github": 400,
      "huggingface": 300,
      "arxiv": 200,
      "hackernews": 100
    },
    "by_category": {
      "ai": 500,
      "devtools": 300,
      "opensource": 200
    },
    "by_score": {
      "5": 100,
      "4": 300,
      "3": 400,
      "2": 150,
      "1": 50
    },
    "average_scores": {
      "heat": 75.5,
      "quality": 3.2,
      "final": 3.4
    },
    "latest_update": "2024-01-09T10:00:00",
    "scheduler": {
      "last_run": "2024-01-09T09:00:00",
      "next_run": "2024-01-09T21:00:00"
    }
  }
}
```

---

### 3. 资源端点

#### 获取资源列表

```http
GET /api/resources
```

#### 获取单个资源

```http
GET /api/resources/{resource_id}
```

---

### 4. 健康检查

#### 健康检查端点

```http
GET /health
```

**响应示例**:

```json
{
  "status": "ok",
  "service": "signal-hunter-backend",
  "database": "ok",
  "redis": "ok",
  "scheduler": "running",
  "last_run": "2024-01-09T09:00:00",
  "next_run": "2024-01-09T21:00:00"
}
```

---

## 错误处理

### 错误响应格式

所有错误都遵循统一的格式：

```json
{
  "success": false,
  "error": {
    "message": "错误描述",
    "code": 404,
    "path": "/api/signals/999",
    "details": {}
  }
}
```

### 常见错误码

| 状态码 | 描述 |
|-------|------|
| 400 | 错误请求 |
| 401 | 未认证 |
| 403 | 禁止访问 |
| 404 | 资源未找到 |
| 422 | 验证失败 |
| 500 | 服务器错误 |

### 错误处理示例

```python
import requests

try:
    response = requests.get("http://localhost:8000/api/signals/99999")
    data = response.json()

    if not data.get("success"):
        error = data.get("error", {})
        print(f"错误 {error.get('code')}: {error.get('message')}")
    else:
        print("成功:", data["data"])

except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
```

---

## 代码示例

### Python示例

```python
import requests
from typing import Dict, List, Optional

class SignalHunterClient:
    """Signal Hunter API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()

        if token:
            self.session.headers.update({
                "Authorization": f"Bearer {token}"
            })

    def get_signals(
        self,
        limit: int = 20,
        offset: int = 0,
        min_score: Optional[int] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at"
    ) -> List[Dict]:
        """获取信号列表"""
        params = {
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by
        }

        if min_score:
            params["min_score"] = min_score
        if source:
            params["source"] = source
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        response = self.session.get(f"{self.base_url}/api/signals", params=params)
        response.raise_for_status()

        data = response.json()
        return data["data"]["items"]

    def get_signal(self, signal_id: int) -> Dict:
        """获取单个信号"""
        response = self.session.get(f"{self.base_url}/api/signals/{signal_id}")
        response.raise_for_status()

        data = response.json()
        return data["data"]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        response = self.session.get(f"{self.base_url}/api/stats")
        response.raise_for_status()

        data = response.json()
        return data["data"]

    def health_check(self) -> Dict:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = SignalHunterClient()

    # 获取高质量信号
    signals = client.get_signals(min_score=4, limit=10)
    print(f"找到 {len(signals)} 个高质量信号")

    # 获取统计信息
    stats = client.get_stats()
    print(f"总信号数: {stats['total_signals']}")

    # 健康检查
    health = client.health_check()
    print(f"服务状态: {health['status']}")
```

### JavaScript/TypeScript示例

```typescript
// Signal Hunter API客户端
class SignalHunterClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string = 'http://localhost:8000', token?: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async getSignals(params: {
    limit?: number;
    offset?: number;
    min_score?: number;
    source?: string;
    category?: string;
    search?: string;
    sort_by?: string;
  } = {}): Promise<any> {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    const queryString = queryParams.toString();
    const endpoint = `/api/signals${queryString ? `?${queryString}` : ''}`;

    const response = await this.request<{ success: boolean; data: any }>(endpoint);

    if (!response.success) {
      throw new Error('API request failed');
    }

    return response.data;
  }

  async getSignal(signalId: number): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>(
      `/api/signals/${signalId}`
    );

    if (!response.success) {
      throw new Error('API request failed');
    }

    return response.data;
  }

  async getStats(): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>(
      '/api/stats'
    );

    if (!response.success) {
      throw new Error('API request failed');
    }

    return response.data;
  }
}

// 使用示例
async function main() {
  const client = new SignalHunterClient();

  // 获取信号列表
  const signals = await client.getSignals({ min_score: 4, limit: 10 });
  console.log(`找到 ${signals.items.length} 个高质量信号`);

  // 获取统计信息
  const stats = await client.getStats();
  console.log(`总信号数: ${stats.total_signals}`);
}
```

---

## Postman集合

### 导入集合

创建一个名为 `SignalHunter.postman_collection.json` 的文件：

```json
{
  "info": {
    "name": "Signal Hunter API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Get Signals",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/signals?limit=20&offset=0",
          "host": ["{{base_url}}"],
          "path": ["api", "signals"],
          "query": [
            {
              "key": "limit",
              "value": "20"
            },
            {
              "key": "offset",
              "value": "0"
            }
          ]
        }
      }
    },
    {
      "name": "Get Signal by ID",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/signals/1",
          "host": ["{{base_url}}"],
          "path": ["api", "signals", "1"]
        }
      }
    },
    {
      "name": "Get Stats",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/stats",
          "host": ["{{base_url}}"],
          "path": ["api", "stats"]
        }
      }
    }
  ]
}
```

---

## 最佳实践

### 1. 错误处理

```python
# 好的做法
try:
    data = client.get_signals(min_score=4)
    if not response.get("success"):
        # 处理API错误
        pass
except requests.exceptions.RequestException:
    # 处理网络错误
    pass

# 不好的做法
data = client.get_signals(min_score=4)  # 没有错误处理
```

### 2. 分页处理

```python
def fetch_all_signals(client: SignalHunterClient, batch_size=100):
    """获取所有信号（自动分页）"""
    offset = 0
    all_signals = []

    while True:
        signals, total = client.get_signals(limit=batch_size, offset=offset)

        if not signals:
            break

        all_signals.extend(signals)

        if len(all_signals) >= total:
            break

        offset += batch_size

    return all_signals
```

### 3. 缓存使用

```python
import time
from functools import lru_cache

class CachedSignalHunterClient(SignalHunterClient):
    """带缓存的客户端"""

    @lru_cache(maxsize=100)
    def get_signal(self, signal_id: int) -> Dict:
        """获取信号（带缓存）"""
        return super().get_signal(signal_id)
```

---

## 更多资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [OpenAPI规范](https://swagger.io/specification/)
- 项目代码审查报告: `CODE_REVIEW_REPORT.md`
- 修复总结: `REFACTORING_SUMMARY.md`
