"""
[INPUT]: 依赖 utils/llm.py (llm_client), services/ai_service.py (AIService), services/prompt_service.py (PromptService)
[OUTPUT]: 对外提供 UnifiedFilter 类, FilterResult 数据类
[POS]: 内容处理层，统一过滤器，合并 SignalFilter + InitialFilter
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import structlog

from app.utils.llm import llm_client

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = structlog.get_logger("unified_filter")


@dataclass
class FilterResult:
    """过滤结果"""
    score: int              # 0-5 评分
    reason: str             # 判断理由（50字内）
    passed: bool            # 是否通过（score >= 3）
    is_whitelist: bool      # 是否白名单源
    language: str           # 检测到的语言 zh/en/other
    prompt_version: int     # 使用的 Prompt 版本


class UnifiedFilter:
    """
    统一过滤器

    合并原有 SignalFilter 和 InitialFilter，使用统一的 0-5 评分制。

    处理流程：
    1. 检查是否白名单源 → 是则直接通过 (score=5)
    2. 语言检测 → 非中英文直接拒绝 (score=0)
    3. 领域排除检查 → 命中则直接拒绝 (score=0)
    4. LLM 评分 → 返回 0-5 分 + 理由

    评分阈值：>= 3 分通过
    """

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

    def __init__(self, prompt_service=None, ai_service: Optional["AIService"] = None):
        """
        初始化过滤器

        Args:
            prompt_service: PromptService 实例（可选）
            ai_service: AIService 实例（可选，提供统一失败策略）
        """
        self.prompt_service = prompt_service
        self._ai_service = ai_service

    def _detect_language(self, text: str) -> str:
        """检测语言"""
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
        """检查是否命中排除领域，返回匹配的关键词"""
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
        """
        执行过滤

        Args:
            title: 内容标题
            content: 内容正文
            url: 内容 URL
            source_name: 来源名称
            source_is_whitelist: 是否白名单源

        Returns:
            FilterResult 对象
        """
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
        prompt_version = 1
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

        # ── 新路径: 使用 AIService (统一失败策略) ──
        if self._ai_service is not None:
            return await self._llm_score_via_ai_service(
                system_prompt, user_prompt, language, prompt_version,
            )

        # ── 旧路径: 直接调用 llm_client (向后兼容) ──
        try:
            response = await llm_client.call_json(
                system_prompt,
                user_prompt,
                temperature=0.3,
            )

            score = int(response.get("score", 0))
            score = max(0, min(5, score))
            reason = response.get("reason", "")[:100]

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

    async def _llm_score_via_ai_service(
        self,
        system_prompt: str,
        user_prompt: str,
        language: str,
        prompt_version: int,
    ) -> FilterResult:
        """
        通过 AIService 调用 LLM 评分

        失败策略: REJECT — 失败时返回 score=0, passed=False
        """
        from app.services.ai_service import FailurePolicy

        result = await self._ai_service.call_json(
            system_prompt,
            user_prompt,
            failure_policy=FailurePolicy.REJECT,
            temperature=0.3,
        )

        if not result.success:
            logger.warning(
                "filter.llm_score.rejected",
                error=result.error,
                language=language,
            )
            return FilterResult(
                score=0,
                reason=f"LLM 不可用: {(result.error or '')[:50]}",
                passed=False,
                is_whitelist=False,
                language=language,
                prompt_version=prompt_version,
            )

        # 解析 AIService 返回的 JSON
        data = result.data or {}
        score = int(data.get("score", 0))
        score = max(0, min(5, score))
        reason = data.get("reason", "")[:100]

        return FilterResult(
            score=score,
            reason=reason,
            passed=score >= self.PASS_THRESHOLD,
            is_whitelist=False,
            language=language,
            prompt_version=prompt_version,
        )


# ============================================================
# 默认 Prompt 模板（数据库中有 active 版本时会覆盖）
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

reason 限制在 50 字以内，说明评分理由。"""

FILTER_USER_PROMPT = """请评估以下内容：

标题：{title}
来源：{source_name}
URL：{url}

内容摘要：
{content}

---
请给出 0-5 分评分和理由。"""


# 全局单例
unified_filter = UnifiedFilter()
