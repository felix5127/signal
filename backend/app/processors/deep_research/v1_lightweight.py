# Input: Resource对象, LLM client, Search provider
# Output: ResearchResult (1500字深度报告)
# Position: V1轻量级研究引擎,3步流程实现

from typing import List, Dict, Optional, Callable
from datetime import datetime
from app.models.resource import Resource
from app.utils.llm import LLMClient
from .base import BaseResearchEngine, ResearchResult, BaseSearchProvider, SearchResult


class LightweightResearchEngine(BaseResearchEngine):
    """
    V1: 轻量级研究引擎

    3步流程:
      1. 生成研究问题 (1次LLM调用, ~500 tokens)
      2. 搜索相关内容 (3个问题 × 2次搜索 = 6次API调用)
      3. 生成综合报告 (1次LLM调用, ~8000 tokens)

    成本: ~$0.03/篇
    """

    def __init__(
        self,
        llm_client: LLMClient,
        search_provider: BaseSearchProvider,
        config: Dict,
    ):
        """
        初始化引擎

        Args:
            llm_client: LLM客户端
            search_provider: 搜索提供商
            config: 配置字典,包含max_questions, max_searches_per_question等
        """
        self.llm = llm_client
        self.search = search_provider
        self.config = config
        self.progress_callback: Optional[Callable] = None

        # 配置参数
        self.max_questions = config.get("max_questions", 3)
        self.max_searches_per_question = config.get("max_searches_per_question", 2)
        self.report_max_tokens = config.get("report_max_tokens", 2000)

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self.progress_callback = callback

    async def research(
        self, resource: Resource, max_cost: float = 0.05
    ) -> ResearchResult:
        """执行轻量级研究流程"""

        steps = []
        total_tokens = 0

        # Step 1: 生成研究问题
        if self.progress_callback:
            self.progress_callback(10, "正在生成研究问题...")

        questions = await self._generate_questions(resource)
        step1_tokens = 500  # 估算
        steps.append(
            {"step": "generate_questions", "output": questions, "tokens": step1_tokens}
        )
        total_tokens += step1_tokens

        # Step 2: 搜索每个问题
        if self.progress_callback:
            self.progress_callback(30, "正在搜索相关内容...")

        search_results = []
        for i, q in enumerate(questions[: self.max_questions]):
            if self.progress_callback:
                self.progress_callback(30 + (i * 20) // len(questions), f"正在搜索第 {i+1} 个问题...")

            results = await self.search.search(
                query=f"{resource.title} {q}",
                max_results=self.max_searches_per_question,
            )
            search_results.extend(results)
            steps.append(
                {"step": "search", "question_id": i + 1, "query": q, "results": len(results)}
            )

        # Step 3: 生成报告
        if self.progress_callback:
            self.progress_callback(80, "正在生成综合报告...")

        report = await self._generate_report(
            resource=resource, questions=questions, search_results=search_results
        )
        step3_tokens = len(report.split()) * 2  # 粗略估算中文token
        steps.append({"step": "generate_report", "tokens": step3_tokens})
        total_tokens += step3_tokens

        if self.progress_callback:
            self.progress_callback(100, "研究完成！")

        # 计算成本
        cost = await self.estimate_cost(resource)

        return ResearchResult(
            content=report,
            sources=[r.url for r in search_results],
            tokens_used=total_tokens,
            cost_usd=cost,
            research_steps=steps,
            metadata={"version": "v1-lightweight", "questions": questions},
            generated_at=datetime.now()
        )

    async def _generate_questions(self, resource: Resource) -> List[str]:
        """
        生成3个研究问题

        根据资源的来源和类型,生成针对性的研究问题。
        """

        # 根据来源定制问题提示
        source_hints = {
            "github": "重点关注: 技术实现、代码质量、社区活跃度",
            "huggingface": "重点关注: 模型性能、训练数据、适用场景",
            "hn": "重点关注: 技术创新点、实际应用、社区讨论",
            "twitter": "重点关注: 行业观点、专家看法、市场反应",
            "podcast": "重点关注: 行业洞察、专家观点、发展趋势",
            "article": "重点关注: 技术细节、行业影响、发展趋势",
        }

        hint = source_hints.get(resource.source_name or "", "")

        system_prompt = "你是一个专业的技术研究分析师，擅长生成具体、可搜索的研究问题。"

        user_prompt = f"""基于以下技术资源,生成3个最值得深入研究的问题:

## 资源信息
标题: {resource.title}
摘要: {resource.summary}
来源: {resource.source_name}
类型: {resource.type}

## 要求
1. 问题要具体、可搜索 (适合Google/网络搜索)
2. 覆盖不同维度: 技术细节、竞品对比、实际应用
3. {hint}
4. 每个问题一行,简洁明确

## 输出格式
严格按照以下格式输出,不要有其他内容:
1. [问题1]
2. [问题2]
3. [问题3]
"""

        response = await self.llm.call(
            system_prompt, user_prompt, max_tokens=300, temperature=0.3
        )

        # 解析问题列表
        questions = []
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.')) or line.startswith(('1、', '2、', '3、')):
                # 提取问题内容
                parts = line.split('.', 2)
                if len(parts) >= 3:
                    questions.append(parts[2].strip())
                else:
                    questions.append(parts[1].strip())

        return questions[:3]  # 确保最多3个问题

    async def _generate_report(
        self, resource: Resource, questions: List[str], search_results: List[SearchResult]
    ) -> str:
        """生成综合研究报告"""

        system_prompt = """你是一个资深的技术研究报告撰写专家，擅长将复杂的技术信息转化为清晰、深入的研究报告。

请基于搜索到的信息，针对给定的技术资源撰写一份深度研究报告。

报告要求：
1. 开头：简要介绍该技术/产品/项目的背景和重要性
2. 主体：针对每个研究问题进行详细分析，引用搜索到的信息
3. 结尾：总结技术趋势、潜在影响和未来发展方向

格式要求：
- 使用Markdown格式
- 至少1500字
- 包含技术细节和分析
- 引用具体的信息来源"""

        # 构建搜索结果的上下文
        search_context = "\n\n".join([
            f"## 来源 {i+1}: {r.title}\n{r.content}\nURL: {r.url}"
            for i, r in enumerate(search_results[:10])  # 最多使用10个搜索结果
        ])

        # 构建问题列表 (避免 f-string 内使用反斜杠)
        questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

        user_prompt = f"""## 研究对象
{resource.title}

## 资源摘要
{resource.summary}

## 研究问题
{questions_text}

## 搜索到的信息
{search_context}

请基于以上信息撰写深度研究报告。"""

        response = await self.llm.call(
            system_prompt, user_prompt, max_tokens=self.report_max_tokens, temperature=0.3
        )

        return response

    async def estimate_cost(self, resource: Resource) -> float:
        """
        计算成本（估算）

        基于资源类型和复杂度估算成本

        Args:
            resource: 资源对象

        Returns:
            float: 预估成本（美元）
        """
        # 基于资源类型估算成本
        base_cost = {
            'article': 0.03,
            'podcast': 0.05,
            'tweet': 0.02,
            'video': 0.08
        }.get(resource.type, 0.03)

        # 根据资源分数调整成本（高分资源需要更多分析）
        if resource.score and resource.score > 80:
            base_cost *= 1.2

        return base_cost