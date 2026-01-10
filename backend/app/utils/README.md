# Utils - 工具函数层

提供通用工具函数和外部服务封装。

## 文件清单

- `llm.py` - OpenAI 客户端封装（异步调用 + 错误重试 + Token 计数）
- `cache.py` - Redis 缓存封装（异步 + 连接池 + 降级机制 + 装饰器）
- `jina.py` - Jina Reader API 调用（网页转 Markdown）
- `logger.py` - 结构化日志配置（structlog）

---

## Redis 缓存使用说明

### 1. 配置（config.yaml）

```yaml
redis:
  enabled: true  # 是否启用缓存
  url: "redis://localhost:6379/0"
  max_connections: 10
  # 缓存过期时间（秒）
  ttl_resources_list: 300   # 5分钟
  ttl_resource_detail: 600  # 10分钟
  ttl_stats: 60             # 1分钟
  ttl_tags: 1800            # 30分钟
  key_prefix: "signal:"     # 键前缀
```

### 2. 环境变量（.env）

```bash
# Redis 配置（可选，覆盖 config.yaml）
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_MAX_CONNECTIONS=10
```

### 3. 在 API 中使用缓存

```python
from app.utils.cache import cache_result, make_resources_list_key

@router.get("/resources")
@cache_result(
    key_func=make_resources_list_key,
    ttl=300,  # 5分钟
)
async def get_resources(type: str, page: int, db: Session = Depends(get_db)):
    # 业务逻辑（缓存失效时执行）
    ...
```

### 4. 手动操作缓存

```python
from app.utils.cache import redis_cache

# 获取缓存
data = await redis_cache.get("key")

# 设置缓存
await redis_cache.set("key", value, ttl=300)

# 删除缓存
await redis_cache.delete("key")

# 批量删除（模式匹配）
await redis_cache.delete_pattern("resources:*")

# 健康检查
is_healthy = await redis_cache.health_check()
```

### 5. 降级机制

- Redis 挂了时，缓存自动降级到数据库查询（不影响业务）
- 所有缓存操作失败都会记录日志，但不抛出异常
- 健康检查失败时自动禁用缓存

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
