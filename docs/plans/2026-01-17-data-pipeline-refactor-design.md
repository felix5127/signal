# Signal Hunter 数据采集管线重构 - 技术方案

> 文档版本: v1.0
> 创建日期: 2026-01-17
> 关联需求: 2026-01-17-data-pipeline-refactor-spec.md
> 状态: 已确认

---

## 一、整体架构

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   用户前台   │  │  Admin 后台  │  │  数据源管理  │               │
│  │  (现有保持)  │  │  审核工作台  │  │  统计面板    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        API Layer                              │   │
│  │  /api/admin/review     审核相关                               │   │
│  │  /api/admin/sources    数据源管理                             │   │
│  │  /api/admin/prompts    Prompt 版本管理                        │   │
│  │  /api/admin/stats      统计数据                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                │                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Service Layer                             │   │
│  │  ReviewService    内容审核服务                                │   │
│  │  SourceService    数据源管理服务（已有，扩展）                │   │
│  │  PromptService    Prompt 版本管理服务（新增）                 │   │
│  │  StatsService     统计服务（新增）                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                │                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Pipeline Layer                             │   │
│  │  UnifiedPipeline  统一的内容处理管线（重构）                  │   │
│  │    ├── Scraper    采集器（现有）                              │   │
│  │    ├── Deduper    去重器（增强）                              │   │
│  │    ├── Extractor  全文提取器（现有）                          │   │
│  │    ├── Filter     统一过滤器（重构，合并两套逻辑）            │   │
│  │    ├── Analyzer   摘要生成器（简化）                          │   │
│  │    └── Translator 翻译器（现有）                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │  Resource  │  │   Source   │  │   Prompt   │  │   Review   │    │
│  │  (扩展)    │  │  (扩展)    │  │   (新增)   │  │   (新增)   │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │
│                                                                      │
│                         PostgreSQL                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心变更点

| 模块 | 变更类型 | 说明 |
|------|----------|------|
| `SignalFilter` + `InitialFilter` | 合并重构 | 统一为 `UnifiedFilter`，使用 0-5 评分制 |
| `Resource` 模型 | 扩展 | 新增 `status` 状态字段、`llm_score`、`llm_reason` |
| `Source` 模型 | 扩展 | 新增 `is_whitelist`、统计字段 |
| `Prompt` 模型 | 新增 | 存储 Prompt 版本历史 |
| `Review` 模型 | 新增 | 存储人工审核记录 |
| Admin API | 新增 | 审核、数据源管理、统计接口 |
| Admin 前端 | 新增 | 审核工作台、数据源管理页面 |

---

## 二、数据模型

### 2.1 Resource 模型扩展

```python
# app/models/resource.py 扩展字段

class ResourceStatus(str, Enum):
    """资源状态"""
    PENDING = "pending"        # 刚采集，待 LLM 评分
    APPROVED = "approved"      # LLM 通过，待人工审核
    REJECTED = "rejected"      # LLM 拒绝，待人工确认
    PUBLISHED = "published"    # 已发布，对外可见
    ARCHIVED = "archived"      # 已归档，不再展示

class Resource(Base):
    # ... 现有字段保持不变 ...

    # ========== 新增字段 ==========

    # 状态管理
    status: str = Column(String(20), default="pending", index=True)

    # LLM 评分结果
    llm_score: int = Column(Integer, nullable=True)          # 0-5 分
    llm_reason: str = Column(Text, nullable=True)            # LLM 判断理由
    llm_prompt_version: int = Column(Integer, nullable=True) # 使用的 Prompt 版本

    # 人工审核
    review_status: str = Column(String(20), nullable=True)   # approved/rejected
    review_comment: str = Column(Text, nullable=True)        # 人工批注
    reviewed_at: datetime = Column(DateTime, nullable=True)
    reviewed_by: str = Column(String(100), nullable=True)

    # 来源关联
    source_id: int = Column(Integer, ForeignKey("sources.id"), nullable=True)
```

### 2.2 Source 模型扩展

```python
# app/models/source.py 扩展

class Source(Base):
    """数据源配置"""
    __tablename__ = "sources"

    id: int = Column(Integer, primary_key=True)

    # 基础信息
    name: str = Column(String(200), nullable=False)          # 数据源名称
    type: str = Column(String(50), nullable=False)           # blog/twitter/podcast/video
    url: str = Column(String(500), nullable=False, unique=True)  # RSS URL

    # 配置
    enabled: bool = Column(Boolean, default=True)            # 是否启用
    is_whitelist: bool = Column(Boolean, default=False)      # 是否白名单

    # 统计（定期更新）
    total_collected: int = Column(Integer, default=0)        # 总采集数
    total_approved: int = Column(Integer, default=0)         # LLM 通过数
    total_rejected: int = Column(Integer, default=0)         # LLM 拒绝数
    total_published: int = Column(Integer, default=0)        # 已发布数
    total_review_overturned: int = Column(Integer, default=0)# 人工改判数
    avg_llm_score: float = Column(Float, default=0.0)        # 平均 LLM 评分

    # 状态
    last_collected_at: datetime = Column(DateTime, nullable=True)
    last_error: str = Column(Text, nullable=True)

    # 时间戳
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, onupdate=datetime.utcnow)
```

### 2.3 Prompt 模型（新增）

```python
# app/models/prompt.py 新增

class Prompt(Base):
    """Prompt 版本管理"""
    __tablename__ = "prompts"

    id: int = Column(Integer, primary_key=True)

    # 版本信息
    name: str = Column(String(100), nullable=False)          # Prompt 名称
    version: int = Column(Integer, nullable=False)           # 版本号
    type: str = Column(String(50), nullable=False)           # filter/analyzer/translator

    # 内容
    system_prompt: str = Column(Text, nullable=False)
    user_prompt_template: str = Column(Text, nullable=False)

    # 状态
    status: str = Column(String(20), default="draft")        # draft/active/archived

    # 效果统计（A/B 测试用）
    total_used: int = Column(Integer, default=0)             # 使用次数
    avg_score: float = Column(Float, nullable=True)          # 平均评分
    approval_rate: float = Column(Float, nullable=True)      # 通过率

    # 时间戳
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    activated_at: datetime = Column(DateTime, nullable=True)

    # 唯一约束：同类型同版本只能有一个
    __table_args__ = (
        UniqueConstraint('type', 'version', name='uix_prompt_type_version'),
    )
```

### 2.4 Review 模型（新增）

```python
# app/models/review.py 新增

class Review(Base):
    """人工审核记录"""
    __tablename__ = "reviews"

    id: int = Column(Integer, primary_key=True)

    # 关联
    resource_id: int = Column(Integer, ForeignKey("resources.id"), nullable=False)

    # 审核内容
    action: str = Column(String(20), nullable=False)         # approve/reject/restore
    old_status: str = Column(String(20), nullable=False)     # 原状态
    new_status: str = Column(String(20), nullable=False)     # 新状态
    comment: str = Column(Text, nullable=True)               # 批注说明

    # 审核人
    reviewer: str = Column(String(100), default="admin")

    # 时间戳
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # 关联对象
    resource = relationship("Resource", backref="reviews")
```

### 2.5 数据库迁移

```sql
-- 1. Resource 表新增字段
ALTER TABLE resources ADD COLUMN status VARCHAR(20) DEFAULT 'published';
ALTER TABLE resources ADD COLUMN llm_score INTEGER;
ALTER TABLE resources ADD COLUMN llm_reason TEXT;
ALTER TABLE resources ADD COLUMN llm_prompt_version INTEGER;
ALTER TABLE resources ADD COLUMN review_status VARCHAR(20);
ALTER TABLE resources ADD COLUMN review_comment TEXT;
ALTER TABLE resources ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE resources ADD COLUMN source_id INTEGER REFERENCES sources(id);

-- 2. 创建 sources 表（如果不存在，扩展字段）
ALTER TABLE sources ADD COLUMN is_whitelist BOOLEAN DEFAULT FALSE;
ALTER TABLE sources ADD COLUMN total_collected INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN total_approved INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN total_rejected INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN total_published INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN total_review_overturned INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN avg_llm_score FLOAT DEFAULT 0.0;

-- 3. 创建 prompts 表
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    total_used INTEGER DEFAULT 0,
    avg_score FLOAT,
    approval_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    UNIQUE(type, version)
);

-- 4. 创建 reviews 表
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL REFERENCES resources(id),
    action VARCHAR(20) NOT NULL,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    comment TEXT,
    reviewer VARCHAR(100) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 现有数据迁移：所有现有 Resource 标记为 published
UPDATE resources SET status = 'published' WHERE status IS NULL;

-- 6. 创建索引
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_source_id ON resources(source_id);
CREATE INDEX idx_resources_llm_score ON resources(llm_score);
CREATE INDEX idx_reviews_resource_id ON reviews(resource_id);
CREATE INDEX idx_prompts_type_status ON prompts(type, status);
```

---

## 三、统一过滤器

### 3.1 UnifiedFilter 设计

```python
# app/processors/unified_filter.py

"""
统一内容过滤器

合并原有 SignalFilter 和 InitialFilter，使用统一的 0-5 评分制。

设计原则：
1. 白名单源直接通过，不调用 LLM
2. 其他源使用 LLM 评分，>= 3 分通过
3. 所有内容都保留，只是状态不同
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from app.utils.llm import llm_client
from app.services.prompt_service import PromptService


@dataclass
class FilterResult:
    """过滤结果"""
    score: int              # 0-5 评分
    reason: str             # 判断理由（50字内）
    passed: bool            # 是否通过（score >= 3）
    is_whitelist: bool      # 是否白名单源
    language: str           # 检测到的语言 zh/en
    prompt_version: int     # 使用的 Prompt 版本


class UnifiedFilter:
    """
    统一过滤器

    处理流程：
    1. 检查是否白名单源 → 是则直接通过
    2. 语言检测 → 非中英文直接拒绝
    3. 领域排除检查 → 命中则直接拒绝
    4. LLM 评分 → 返回 0-5 分 + 理由
    """

    # 评分阈值
    PASS_THRESHOLD = 3

    # 领域排除（硬过滤）
    EXCLUDED_DOMAINS = [
        # 生物医学（非 AI 核心）
        "DNA repair", "gene therapy", "anti-aging",
        "格陵兰鲨", "抗衰老", "长寿", "基因修复",
        "protein folding", "蛋白质折叠",

        # 游戏开发
        "Unity", "Unreal", "game engine", "游戏引擎",
        "game development", "游戏开发",

        # 加密货币/Web3
        "blockchain", "区块链", "NFT", "DeFi", "Web3",
        "cryptocurrency", "加密货币", "Solana", "Ethereum",

        # 图形学（非 AI 生成）
        "WebGL", "ray tracing", "光线追踪",
        "fluid simulation", "流体模拟",
    ]

    def __init__(self, prompt_service: Optional[PromptService] = None):
        self.prompt_service = prompt_service

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        import re
        if not text:
            return "other"

        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_len = len(text)

        if total_len == 0:
            return "other"

        chinese_ratio = chinese_chars / total_len

        if chinese_ratio > 0.2:
            return "zh"
        elif len(re.findall(r'[a-zA-Z]+', text)) > 5:
            return "en"
        else:
            return "other"

    def _check_excluded_domain(self, title: str, content: str) -> Optional[str]:
        """检查是否命中排除领域"""
        text = f"{title} {content[:1000]}".lower()

        for keyword in self.EXCLUDED_DOMAINS:
            if keyword.lower() in text:
                return keyword
        return None

    async def filter(
        self,
        title: str,
        content: str,
        url: str,
        source_name: str,
        source_is_whitelist: bool,
    ) -> FilterResult:
        """执行过滤"""

        # 1. 白名单源直接通过
        if source_is_whitelist:
            return FilterResult(
                score=5,
                reason="白名单源，直接通过",
                passed=True,
                is_whitelist=True,
                language=self._detect_language(title + content[:500]),
                prompt_version=0,
            )

        # 2. 语言检测
        language = self._detect_language(title + content[:500])
        if language not in ("zh", "en"):
            return FilterResult(
                score=0,
                reason=f"不支持的语言: {language}",
                passed=False,
                is_whitelist=False,
                language=language,
                prompt_version=0,
            )

        # 3. 领域排除
        excluded = self._check_excluded_domain(title, content)
        if excluded:
            return FilterResult(
                score=0,
                reason=f"非核心领域: {excluded}",
                passed=False,
                is_whitelist=False,
                language=language,
                prompt_version=0,
            )

        # 4. LLM 评分
        return await self._llm_score(title, content, url, source_name, language)

    async def _llm_score(
        self,
        title: str,
        content: str,
        url: str,
        source_name: str,
        language: str,
    ) -> FilterResult:
        """LLM 评分"""

        # 获取当前活跃的 Prompt
        prompt_version = 1  # 默认版本
        system_prompt = FILTER_SYSTEM_PROMPT
        user_prompt_template = FILTER_USER_PROMPT

        if self.prompt_service:
            active_prompt = self.prompt_service.get_active_prompt("filter")
            if active_prompt:
                prompt_version = active_prompt.version
                system_prompt = active_prompt.system_prompt
                user_prompt_template = active_prompt.user_prompt_template

        # 截断内容
        content_truncated = content[:3000] if len(content) > 3000 else content

        # 构建用户 Prompt
        user_prompt = user_prompt_template.format(
            title=title,
            source_name=source_name,
            url=url,
            content=content_truncated,
        )

        try:
            response = await llm_client.call_json(
                system_prompt,
                user_prompt,
                temperature=0.3,
            )

            score = int(response.get("score", 0))
            score = max(0, min(5, score))  # 限制在 0-5
            reason = response.get("reason", "")[:100]  # 限制长度

            return FilterResult(
                score=score,
                reason=reason,
                passed=score >= self.PASS_THRESHOLD,
                is_whitelist=False,
                language=language,
                prompt_version=prompt_version,
            )

        except Exception as e:
            # LLM 调用失败，保守处理（通过，待人工审核）
            return FilterResult(
                score=3,
                reason=f"LLM 调用失败: {str(e)[:50]}",
                passed=True,
                is_whitelist=False,
                language=language,
                prompt_version=prompt_version,
            )


# ============================================================
# Prompt 模板
# ============================================================

FILTER_SYSTEM_PROMPT = """你是一个 AI 技术内容筛选专家，为 AI 技术情报平台筛选内容。

## 评分标准（0-5 分）

**5 分 - 极高价值**
- 头部公司重磅产品发布（OpenAI/Anthropic/Google 新产品）
- 改变开发者工作方式的工具（如 Cursor, Claude Code 级别）
- 深度技术分析 + 完整代码实现
- 权威人士的深度洞察

**4 分 - 高价值**
- 有独特见解的技术分析
- 实用的 AI 开发教程（有代码）
- AI 领域重要动态和趋势分析
- 知名博主的深度文章

**3 分 - 有价值**
- AI 相关的技术讨论，有一定深度
- 普通的 AI 工具/产品介绍
- AI 领域的新闻报道（有实质内容）

**2 分 - 价值较低**
- 内容较浅的 AI 相关文章
- 转载/二手信息
- 过于基础的入门内容

**1 分 - 价值很低**
- 与 AI 关联很弱
- 纯营销/广告内容
- 标题党，内容空洞

**0 分 - 无价值**
- 完全不相关
- 垃圾内容
- 非中英文

## 判断重点

1. **深度优先**：深度分析 > 新闻通稿
2. **头部优先**：OpenAI/Anthropic/Google 等头部公司动态优先
3. **实用优先**：有代码/工具/Demo 的内容优先
4. **原创优先**：原创分析 > 转载搬运

## 输出格式

严格返回 JSON：
{
  "score": 4,
  "reason": "深度分析 Claude Code 架构，有代码实现"
}

reason 限制在 50 字以内，说明评分理由。
"""

FILTER_USER_PROMPT = """请评估以下内容：

标题：{title}
来源：{source_name}
URL：{url}

内容摘要：
{content}

---
请给出 0-5 分评分和理由。
"""
```

### 3.2 过滤流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      UnifiedFilter.filter()                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  是否白名单源？    │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                   是                   否
                    │                   │
                    ▼                   ▼
            ┌─────────────┐    ┌───────────────────┐
            │ score=5     │    │   语言检测        │
            │ passed=True │    └─────────┬─────────┘
            │ 直接返回    │              │
            └─────────────┘    ┌─────────┴─────────┐
                               ▼                   ▼
                           zh/en               其他语言
                               │                   │
                               ▼                   ▼
                    ┌───────────────────┐  ┌─────────────┐
                    │   领域排除检查    │  │ score=0     │
                    └─────────┬─────────┘  │ 直接返回    │
                              │            └─────────────┘
                    ┌─────────┴─────────┐
                    ▼                   ▼
                  命中               未命中
                    │                   │
                    ▼                   ▼
            ┌─────────────┐    ┌───────────────────┐
            │ score=0     │    │   LLM 评分        │
            │ 直接返回    │    │   (调用 API)      │
            └─────────────┘    └─────────┬─────────┘
                                         │
                                         ▼
                               ┌───────────────────┐
                               │  返回 FilterResult │
                               │  score: 0-5       │
                               │  passed: score>=3 │
                               └───────────────────┘
```

### 3.3 与原有 Filter 的对比

| 维度 | SignalFilter (旧) | InitialFilter (旧) | UnifiedFilter (新) |
|------|-------------------|--------------------|--------------------|
| 评分方式 | A/B/C/D/E/F 条件 | 0-5 评分 | 0-5 评分 |
| 通过条件 | 满足任一条件 | >= 3 分 | >= 3 分 |
| 严格程度 | 极严（全拒绝） | 中等 | 中等偏宽 |
| 白名单 | 无 | 有（来源） | 有（来源+动态管理） |
| 可观测性 | 差 | 一般 | 好（保存评分+理由） |

---

## 四、API 设计

### 4.1 审核相关 API

```
# 获取待审核列表
GET /api/admin/review/list
  ?status=approved|rejected|all
  ?source_id=1
  ?date_from=2026-01-01
  ?date_to=2026-01-17
  ?page=1
  ?page_size=50

Response:
{
  "items": [
    {
      "id": 123,
      "title": "...",
      "url": "...",
      "source_name": "...",
      "status": "approved",
      "llm_score": 4,
      "llm_reason": "...",
      "created_at": "..."
    }
  ],
  "total": 200,
  "page": 1,
  "page_size": 50
}

# 批量审核操作
POST /api/admin/review/action
{
  "resource_ids": [123, 124, 125],
  "action": "publish" | "reject" | "restore",
  "comment": "批注说明"
}

# 单个审核操作
POST /api/admin/review/{resource_id}/action
{
  "action": "publish" | "reject" | "restore",
  "comment": "批注说明"
}

# 获取审核统计
GET /api/admin/review/stats
  ?date_from=2026-01-01
  ?date_to=2026-01-17

Response:
{
  "total_pending": 150,
  "total_approved": 80,
  "total_rejected": 70,
  "total_published": 60,
  "total_overturned": 10,
  "by_source": [
    {"source_id": 1, "source_name": "...", "count": 50}
  ]
}
```

### 4.2 数据源管理 API

```
# 获取数据源列表
GET /api/admin/sources
  ?type=blog|twitter|podcast|video
  ?enabled=true|false

Response:
{
  "items": [
    {
      "id": 1,
      "name": "宝玉的分享",
      "type": "blog",
      "url": "https://...",
      "enabled": true,
      "is_whitelist": true,
      "stats": {
        "total_collected": 100,
        "total_approved": 80,
        "total_rejected": 20,
        "approval_rate": 0.8,
        "avg_llm_score": 3.5
      },
      "last_collected_at": "..."
    }
  ]
}

# 添加数据源
POST /api/admin/sources
{
  "name": "新数据源",
  "type": "blog",
  "url": "https://...",
  "is_whitelist": false
}

# 更新数据源
PUT /api/admin/sources/{source_id}
{
  "name": "...",
  "enabled": true,
  "is_whitelist": true
}

# 删除数据源
DELETE /api/admin/sources/{source_id}

# 获取数据源详情统计
GET /api/admin/sources/{source_id}/stats

Response:
{
  "source": {...},
  "score_distribution": {
    "0": 5, "1": 10, "2": 15, "3": 30, "4": 25, "5": 15
  },
  "recent_items": [...],
  "daily_stats": [...]
}
```

### 4.3 Prompt 管理 API

```
# 获取 Prompt 列表
GET /api/admin/prompts
  ?type=filter|analyzer|translator

# 获取当前活跃 Prompt
GET /api/admin/prompts/active/{type}

# 创建新版本
POST /api/admin/prompts
{
  "name": "内容过滤 v2",
  "type": "filter",
  "system_prompt": "...",
  "user_prompt_template": "..."
}

# 激活某版本
POST /api/admin/prompts/{prompt_id}/activate

# 获取版本对比
GET /api/admin/prompts/compare?v1=1&v2=2
```

---

## 五、后台界面设计

### 5.1 审核工作台

```
┌─────────────────────────────────────────────────────────────────────┐
│  审核工作台                                    [今日待审: 156]      │
├─────────────────────────────────────────────────────────────────────┤
│  筛选: [全部▼] [所有来源▼] [2026-01-17 ▼]      [刷新]              │
├───────────────────────────────┬─────────────────────────────────────┤
│   LLM 通过 (78)               │      LLM 拒绝 (78)                  │
├───────────────────────────────┼─────────────────────────────────────┤
│ ┌───────────────────────────┐ │ ┌─────────────────────────────────┐ │
│ │ □ Claude Code 深度解析... │ │ │ □ 每周 AI 资讯汇总...          │ │
│ │   宝玉的分享 · 10:30      │ │ │   某公众号 · 09:15              │ │
│ │   ⭐ 4 分 · 深度分析有代码 │ │ │   ⭐ 2 分 · 内容较浅无新意     │ │
│ │   [删除] [查看]           │ │ │   [恢复] [查看]                 │ │
│ └───────────────────────────┘ │ └─────────────────────────────────┘ │
│ ┌───────────────────────────┐ │ ┌─────────────────────────────────┐ │
│ │ □ OpenAI 发布 GPT-5...    │ │ │ □ Python 入门教程...           │ │
│ │   OpenAI Blog · 08:00     │ │ │   某博客 · 08:30                │ │
│ │   ⭐ 5 分 · 头部公司重磅   │ │ │   ⭐ 1 分 · 与 AI 无关         │ │
│ │   [删除] [查看]           │ │ │   [恢复] [查看]                 │ │
│ └───────────────────────────┘ │ └─────────────────────────────────┘ │
│         ...                   │         ...                         │
├───────────────────────────────┴─────────────────────────────────────┤
│  已选 3 项   [批量发布] [批量删除]              [上一页] 1/4 [下一页]│
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 数据源管理

```
┌─────────────────────────────────────────────────────────────────────┐
│  数据源管理                                         [+ 添加数据源]  │
├─────────────────────────────────────────────────────────────────────┤
│  类型: [全部▼] [博客] [Twitter] [播客] [视频]                       │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 📝 宝玉的分享                                    [白名单] [启用] │ │
│ │    blog · https://baoyu.io/feed                                 │ │
│ │    ┌─────────────────────────────────────────────────────────┐  │ │
│ │    │ 采集: 156  通过: 142 (91%)  发布: 138  改判: 4          │  │ │
│ │    │ 平均分: 4.2  最近采集: 2 小时前                         │  │ │
│ │    └─────────────────────────────────────────────────────────┘  │ │
│ │    [编辑] [查看详情] [禁用]                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 📝 阮一峰的网络日志                                      [启用] │ │
│ │    blog · https://ruanyifeng.com/feed                           │ │
│ │    ┌─────────────────────────────────────────────────────────┐  │ │
│ │    │ 采集: 89   通过: 45 (51%)   发布: 40   改判: 8          │  │ │
│ │    │ 平均分: 3.1  最近采集: 2 小时前                         │  │ │
│ │    └─────────────────────────────────────────────────────────┘  │ │
│ │    [编辑] [查看详情] [设为白名单] [禁用]                        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、统一管线设计

### 6.1 UnifiedPipeline 流程

```python
# app/tasks/unified_pipeline.py

async def run_unified_pipeline(source_type: str = None):
    """
    统一内容处理管线

    流程：
    1. 获取要采集的数据源
    2. RSS 采集
    3. URL 去重（数据库查重 + 标题相似度 + 内容指纹）
    4. 全文提取
    5. 统一过滤（UnifiedFilter）
    6. 摘要生成
    7. 翻译（仅英文）
    8. 存储
    9. 更新数据源统计
    """

    # 1. 获取数据源
    sources = get_enabled_sources(source_type)

    for source in sources:
        # 2. RSS 采集
        raw_items = await scrape_rss(source.url)

        # 3. 去重
        new_items = await dedupe(raw_items)

        for item in new_items:
            # 4. 全文提取
            content = await extract_content(item.url)

            # 5. 统一过滤
            filter_result = await unified_filter.filter(
                title=item.title,
                content=content.markdown,
                url=item.url,
                source_name=source.name,
                source_is_whitelist=source.is_whitelist,
            )

            # 6. 确定状态
            if source.is_whitelist:
                status = "published"
            elif filter_result.passed:
                status = "approved"
            else:
                status = "rejected"

            # 7. 摘要生成（仅通过的内容）
            summary = None
            if filter_result.passed:
                summary = await generate_summary(content.markdown)

            # 8. 翻译（仅英文内容）
            translated = None
            if filter_result.language == "en" and filter_result.passed:
                translated = await translate(item.title, summary)

            # 9. 存储
            resource = Resource(
                title=item.title,
                title_translated=translated.title if translated else None,
                url=item.url,
                content_markdown=content.markdown,
                summary=summary.text if summary else None,
                summary_zh=translated.summary if translated else None,

                status=status,
                llm_score=filter_result.score,
                llm_reason=filter_result.reason,
                llm_prompt_version=filter_result.prompt_version,
                language=filter_result.language,

                source_id=source.id,
                source_name=source.name,
            )
            db.add(resource)

        # 10. 更新数据源统计
        update_source_stats(source.id)

    db.commit()
```

### 6.2 去重增强

```python
# app/processors/deduper.py

class Deduper:
    """
    内容去重器

    三层去重：
    1. URL 精确匹配
    2. 标题相似度（Jaccard > 0.8）
    3. 内容指纹（SimHash 汉明距离 < 3）
    """

    async def dedupe(self, items: List[RawItem]) -> List[RawItem]:
        """批量去重"""
        result = []

        for item in items:
            # 1. URL 去重
            if await self._url_exists(item.url):
                continue

            # 2. 标题相似度
            if await self._similar_title_exists(item.title):
                continue

            # 3. 内容指纹（可选，需要先提取内容）
            # if await self._similar_content_exists(item.content_hash):
            #     continue

            result.append(item)

        return result

    async def _url_exists(self, url: str) -> bool:
        """URL 精确匹配"""
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return db.query(Resource).filter(Resource.url_hash == url_hash).first() is not None

    async def _similar_title_exists(self, title: str, threshold: float = 0.8) -> bool:
        """标题相似度检查（Jaccard）"""
        # 获取最近 7 天的标题
        recent_titles = db.query(Resource.title).filter(
            Resource.created_at > datetime.now() - timedelta(days=7)
        ).all()

        title_tokens = set(title.lower().split())

        for (existing_title,) in recent_titles:
            existing_tokens = set(existing_title.lower().split())

            # Jaccard 相似度
            intersection = len(title_tokens & existing_tokens)
            union = len(title_tokens | existing_tokens)

            if union > 0 and intersection / union > threshold:
                return True

        return False
```

---

## 七、文件变更清单

### 7.1 新增文件

```
backend/app/
├── models/
│   ├── prompt.py              # Prompt 模型
│   └── review.py              # Review 模型
├── processors/
│   └── unified_filter.py      # 统一过滤器
├── services/
│   ├── review_service.py      # 审核服务
│   ├── prompt_service.py      # Prompt 服务
│   └── stats_service.py       # 统计服务
├── api/
│   └── admin/
│       ├── __init__.py
│       ├── review.py          # 审核 API
│       ├── sources.py         # 数据源管理 API
│       ├── prompts.py         # Prompt 管理 API
│       └── stats.py           # 统计 API
└── tasks/
    └── unified_pipeline.py    # 统一管线

frontend/app/
└── admin/
    ├── review/
    │   └── page.tsx           # 审核工作台
    ├── sources/
    │   └── page.tsx           # 数据源管理
    └── prompts/
        └── page.tsx           # Prompt 管理
```

### 7.2 修改文件

```
backend/app/
├── models/
│   ├── resource.py            # 扩展字段
│   └── source.py              # 扩展字段（如果存在）
├── tasks/
│   └── pipeline.py            # 改用 UnifiedPipeline
└── main.py                    # 注册新路由

frontend/app/
└── admin/
    └── layout.tsx             # 添加新菜单项
```

### 7.3 删除文件

```
backend/app/processors/
├── filter.py                  # SignalFilter（合并到 unified_filter）
└── initial_filter.py          # InitialFilter（合并到 unified_filter）
```

---

## 八、实施步骤

### Phase 1: 数据层（Day 1）

1. 创建数据库迁移脚本
2. 新增 Prompt、Review 模型
3. 扩展 Resource、Source 模型
4. 执行迁移，现有数据标记为 published

### Phase 2: 过滤器重构（Day 1-2）

1. 实现 UnifiedFilter
2. 实现 Deduper 增强
3. 删除旧的 SignalFilter、InitialFilter
4. 更新 Pipeline 引用

### Phase 3: 服务层（Day 2）

1. 实现 ReviewService
2. 实现 PromptService
3. 实现 StatsService
4. 扩展 SourceService

### Phase 4: API 层（Day 2-3）

1. 实现审核 API
2. 实现数据源管理 API
3. 实现 Prompt 管理 API
4. 实现统计 API

### Phase 5: 前端（Day 3-4）

1. 实现审核工作台页面
2. 实现数据源管理页面
3. 实现 Prompt 管理页面
4. 更新导航菜单

### Phase 6: 测试与上线（Day 4）

1. 单元测试
2. 集成测试
3. 手动触发采集测试
4. 部署上线

---

## 九、验收标准

- [ ] 后台可查看所有采集内容（通过/拒绝分组）
- [ ] 可对内容进行删除/恢复操作并添加批注
- [ ] 可管理数据源（添加/删除/启用/禁用/白名单）
- [ ] 可查看每个数据源的统计指标
- [ ] 可管理 Prompt 版本（查看/回滚）
- [ ] 采集管线正常运行（6 小时一次）
- [ ] 去重功能正常（URL + 标题 + 内容指纹）
- [ ] 英文内容自动翻译
- [ ] 每天采集 200+ 条内容进入审核池
- [ ] 白名单源内容直接发布
- [ ] 所有采集内容都有保留（包括 rejected）
