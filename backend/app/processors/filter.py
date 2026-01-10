# Input: RawSignal (来自 scrapers)
# Output: FilterResult (通过/拒绝 + 匹配条件 + 理由)
# Position: LLM 过滤层，判断信号是否满足 A/B/C 条件
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import hashlib
from typing import List, Optional

from pydantic import BaseModel

from app.scrapers.base import RawSignal
from app.utils.llm import llm_client


class FilterResult(BaseModel):
    """
    过滤结果数据模型

    字段说明：
    - passed: 是否通过过滤
    - matched_conditions: 匹配的条件列表 ['A', 'B', 'C']
    - reason: 判断理由
    - url_hash: URL 哈希（用于去重）
    - title_hash: 标题哈希（用于去重）
    """

    passed: bool
    matched_conditions: List[str] = []
    reason: str = ""
    url_hash: str = ""
    title_hash: str = ""


class SignalFilter:
    """
    信号过滤器

    两阶段过滤：
    1. 去重过滤（URL hash + 标题 SimHash）
    2. LLM 过滤（判断是否满足 A/B/C 条件）

    A/B/C 条件：
    A. 发布了新代码/新模型/新论文
    B. 披露了可复现实验结果
    C. 提供了可用工具/API/Demo
    """

    # LLM 过滤 Prompt
    FILTER_SYSTEM_PROMPT = """你是一个技术信号筛选专家,专注于识别真正有价值的技术创新。

你的任务是判断给定的技术内容是否满足以下至少一项条件：

**【A】 发布了新代码/新模型/新论文**
   - ✅ 开源项目发布新版本(GitHub/GitLab/Hugging Face)
   - ✅ 新的 AI 模型发布(GPT-5, Llama-3, Claude-3等)
   - ✅ 新论文发表(arXiv, NeurIPS, ICML, CVPR等)
   - ✅ 新的 API/SDK 发布
   - ❌ 旧项目的讨论、教程、评测

**【B】 披露了可复现实验结果**
   - ✅ 提供了详细的 Benchmark 数据和对比
   - ✅ 包含实验方法、参数、指标
   - ✅ 有明确的性能提升数据(准确率、速度、成本等)
   - ✅ 提供了复现代码或详细步骤
   - ❌ 只有文字描述没有具体数据

**【C】 提供了可用工具/API/Demo**
   - ✅ 可直接使用的工具、库、框架
   - ✅ 公开的 API 接口(免费或付费)
   - ✅ 在线 Demo 或 Playground
   - ✅ 可下载的软件/模型
   - ❌ 概念性介绍,没有实际产物

**【严格拒绝以下内容】**：
- ❌ 纯观点/评论/讨论类文章(如"AI的未来","某某的思考")
- ❌ 新闻报道,无技术细节(如"某公司融资1亿美元")
- ❌ 招聘/广告/营销内容
- ❌ 入门教程/科普文章(除非包含新工具/新方法)
- ❌ "Show HN" 中的纯分享,无实质内容
- ❌ 问题/求助帖(如"Ask HN: ...")

**判断标准**:
1. 必须有**实质性产出**(代码/模型/论文/工具/数据)
2. 必须是**新发布**的内容(非旧内容的二次传播)
3. 必须有**技术价值**(非纯商业/营销)

**返回格式**：
严格返回 JSON 格式,不要包含任何额外文字:
{
  "passed": true/false,
  "matched_conditions": ["A", "B"],  # 可以多选
  "reason": "简短说明（20字以内）"
}

**示例**:
- "Show HN: Z80-μLM, a 'Conversational AI' That Fits in 40KB" → {"passed": true, "matched_conditions": ["A", "C"], "reason": "新开源项目+可用代码"}
- "OpenAI releases GPT-5 with 95% accuracy on MMLU" → {"passed": true, "matched_conditions": ["A", "B"], "reason": "新模型+Benchmark数据"}
- "Why I think AI will change the world" → {"passed": false, "matched_conditions": [], "reason": "纯观点文章"}
"""

    FILTER_USER_PROMPT_TEMPLATE = """标题：{title}

URL：{url}

来源：{source}

元数据：{metadata}

{source_specific_info}

请判断这条信息是否满足条件 A/B/C 的至少一项。"""

    def __init__(self, dedup_enabled: bool = True):
        """
        初始化过滤器

        Args:
            dedup_enabled: 是否启用去重
        """
        self.dedup_enabled = dedup_enabled
        self.seen_url_hashes = set()
        self.seen_title_hashes = set()

    @staticmethod
    def _compute_hash(text: str) -> str:
        """
        计算文本的 SHA-256 哈希

        Args:
            text: 输入文本

        Returns:
            64 字符哈希字符串
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_simhash(text: str, hash_bits: int = 64) -> str:
        """
        计算文本的 SimHash（简化版）

        用于标题去重：相似标题会产生相近的哈希值

        Args:
            text: 输入文本
            hash_bits: 哈希位数

        Returns:
            SimHash 字符串
        """
        # 简化版 SimHash：将文本分词后计算哈希
        # 实际生产环境可以用 simhash 库
        tokens = text.lower().split()
        if not tokens:
            return "0" * hash_bits

        # 计算每个 token 的哈希
        v = [0] * hash_bits
        for token in tokens:
            h = hash(token)
            for i in range(hash_bits):
                if h & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1

        # 生成 SimHash
        fingerprint = 0
        for i in range(hash_bits):
            if v[i] > 0:
                fingerprint |= 1 << i

        return format(fingerprint, f"0{hash_bits//4}x")

    def _check_duplicate(self, signal: RawSignal) -> Optional[str]:
        """
        检查是否重复

        Args:
            signal: 原始信号

        Returns:
            如果重复，返回原因；否则返回 None
        """
        if not self.dedup_enabled:
            return None

        # 1. URL 去重
        url_hash = self._compute_hash(signal.url)
        if url_hash in self.seen_url_hashes:
            return f"重复 URL: {signal.url}"

        # 2. 标题 SimHash 去重（检测标题相似度）
        title_hash = self._compute_simhash(signal.title)
        if title_hash in self.seen_title_hashes:
            return f"重复标题: {signal.title}"

        # 记录哈希
        self.seen_url_hashes.add(url_hash)
        self.seen_title_hashes.add(title_hash)

        return None

    async def filter(self, signal: RawSignal) -> FilterResult:
        """
        过滤单个信号

        Args:
            signal: 原始信号

        Returns:
            FilterResult 对象
        """
        # 计算哈希（无论是否去重都需要存储）
        url_hash = self._compute_hash(signal.url)
        title_hash = self._compute_simhash(signal.title)

        # 1. 去重检查
        dup_reason = self._check_duplicate(signal)
        if dup_reason:
            return FilterResult(
                passed=False,
                matched_conditions=[],
                reason=dup_reason,
                url_hash=url_hash,
                title_hash=title_hash,
            )

        # 2. LLM 过滤
        # 为不同数据源生成特定信息
        source_specific_info = ""
        if signal.source == "github":
            metadata = signal.metadata
            source_specific_info = f"""[GitHub 项目特定信息]
- Stars: {metadata.get('stars', 'N/A')}
- Forks: {metadata.get('forks', 'N/A')}
- 编程语言: {metadata.get('language', 'N/A')}
- 项目所有者: {metadata.get('owner', 'N/A')}
- Topics/标签: {', '.join(metadata.get('topics', [])[:5]) if metadata.get('topics') else 'N/A'}

注意：这是一个 GitHub 开源项目。请重点关注：
1. 是否是新发布的项目（条件A）
2. 是否提供了可用的代码/工具（条件C）
3. Star 数表明项目热度，但不是唯一判断标准"""
        elif signal.source == "hn":
            metadata = signal.metadata
            source_specific_info = f"""[Hacker News 特定信息]
- HN 评分: {metadata.get('score', 'N/A')}
- 评论数: {metadata.get('comments', 'N/A')}
- 作者: {metadata.get('author', 'N/A')}"""
        elif signal.source == "huggingface":
            metadata = signal.metadata
            item_type = metadata.get('type', 'unknown')
            source_specific_info = f"""[Hugging Face 特定信息]
- 类型: {item_type} ({'模型' if item_type == 'model' else '数据集' if item_type == 'dataset' else '未知'})
- Likes: {metadata.get('likes', 'N/A')}
- Downloads: {metadata.get('downloads', 'N/A')}
- 作者: {metadata.get('author', 'N/A')}"""

            if item_type == "model":
                source_specific_info += f"""
- 任务类型: {metadata.get('pipeline_tag', 'N/A')}
- 框架: {metadata.get('library_name', 'N/A')}
- 标签: {', '.join(metadata.get('tags', [])[:5]) if metadata.get('tags') else 'N/A'}

注意：这是一个 Hugging Face 模型。请重点关注：
1. 是否是新发布的模型（条件A）
2. 是否提供了可复现的结果或 Demo（条件B）
3. 是否可直接使用（条件C）
4. Likes 和 Downloads 表明模型热度"""
            else:
                source_specific_info += f"""
- 标签: {', '.join(metadata.get('tags', [])[:5]) if metadata.get('tags') else 'N/A'}

注意：这是一个 Hugging Face 数据集。请重点关注：
1. 是否是新发布的数据集（条件A）
2. 数据集质量和规模
3. 是否可直接使用（条件C）"""

        user_prompt = self.FILTER_USER_PROMPT_TEMPLATE.format(
            title=signal.title,
            url=signal.url,
            source=signal.source,
            metadata=signal.metadata,
            source_specific_info=source_specific_info,
        )

        try:
            llm_response = await llm_client.call_json(
                self.FILTER_SYSTEM_PROMPT, user_prompt
            )

            return FilterResult(
                passed=llm_response.get("passed", False),
                matched_conditions=llm_response.get("matched_conditions", []),
                reason=llm_response.get("reason", ""),
                url_hash=url_hash,
                title_hash=title_hash,
            )

        except Exception as e:
            # LLM 调用失败，默认拒绝
            print(f"[Filter] LLM call failed for {signal.url}: {e}")
            return FilterResult(
                passed=False,
                matched_conditions=[],
                reason=f"LLM 调用失败: {str(e)}",
                url_hash=url_hash,
                title_hash=title_hash,
            )

    async def filter_batch(self, signals: List[RawSignal]) -> List[FilterResult]:
        """
        批量过滤信号

        Args:
            signals: 原始信号列表

        Returns:
            FilterResult 列表
        """
        results = []
        for signal in signals:
            result = await self.filter(signal)
            results.append(result)
        return results

    def reset_dedup_cache(self):
        """重置去重缓存"""
        self.seen_url_hashes.clear()
        self.seen_title_hashes.clear()
