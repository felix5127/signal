# backend/app/utils/
> L2 | 父级: backend/app/CLAUDE.md

## 职责
通用工具函数和外部服务封装，提供 LLM 调用、缓存、日志等基础能力。

## 成员清单
llm.py: OpenAI 客户端封装 (异步调用 + 错误重试 + Token 计数)
cache.py: Redis 缓存封装 (异步 + 连接池 + 降级机制 + 装饰器)
jina.py: Jina Reader API 调用 (网页转 Markdown)
logger.py: 结构化日志配置 (structlog)

## Redis 缓存配置

### config.yaml
```yaml
redis:
  enabled: true
  url: "redis://localhost:6379/0"
  max_connections: 10
  ttl_resources_list: 300   # 5min
  ttl_resource_detail: 600  # 10min
  ttl_stats: 60             # 1min
  ttl_tags: 1800            # 30min
  key_prefix: "signal:"
```

### 环境变量覆盖 (.env)
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_MAX_CONNECTIONS=10
```

### API 缓存装饰器
```python
from app.utils.cache import cache_result, make_resources_list_key

@router.get("/resources")
@cache_result(key_func=make_resources_list_key, ttl=300)
async def get_resources(type: str, page: int, db: Session = Depends(get_db)):
    ...
```

### 降级机制
- Redis 不可用时自动降级到直接 DB 查询
- 所有缓存操作失败记录日志但不抛异常
- 健康检查失败时自动禁用缓存

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
