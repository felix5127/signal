# Input: RawSignal (来自 scrapers) + FilterResult (来自 filter)
# Output: SummaryResult (摘要 + 评分 + 分类)
# Position: LLM 摘要生成层，生成结构化信号摘要，支持并行批处理
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
from typing import List, Optional

from pydantic import BaseModel

from app.scrapers.base import RawSignal
from app.utils.llm import llm_client


class SummaryResult(BaseModel):
    """
    摘要生成结果数据模型

    字段说明：
    - one_liner: 一句话总结（20字以内）
    - summary: 详细摘要（200字左右，3-5个要点）
    - heat_score: 热度评分（1-5）
    - quality_score: 质量评分（1-5）
    - category: 分类标签
    - tags: 关键词标签
    """

    one_liner: str
    summary: str
    heat_score: int
    quality_score: int
    category: str
    tags: List[str] = []


class SummaryGenerator:
    """
    摘要生成器

    使用 LLM 生成结构化摘要，包含：
    - 一句话总结
    - 详细摘要（3-5 个要点）
    - 热度评分（基于影响力、关注度）
    - 质量评分（基于技术深度、实用性）
    - 分类标签
    """

    # LLM 摘要生成 Prompt
    SUMMARY_SYSTEM_PROMPT = """你是一个技术信号分析专家,擅长提炼技术创新的核心价值。

你的任务是为技术内容生成结构化摘要,帮助独立开发者、技术投资人、技术创作者快速理解信号价值。

**输出要求**：

1. **one_liner（一句话总结 - 20字以内）**
   - 格式: [主体] + [动作] + [核心亮点]
   - 专有名词保留英文
   - ✅ 好例子: "Z80-μLM: 40KB大小的对话AI"
   - ✅ 好例子: "OpenAI发布GPT-5,性能提升3倍"
   - ❌ 坏例子: "一个有趣的AI项目"(不够具体)

2. **summary（详细摘要 - 150-250字）**
   - 用简洁的段落文字描述,不要使用列表格式
   - 必须包含以下要素:
     - 这是什么(What): 产品/技术/论文的定义
     - 核心亮点(Highlight): 最重要的1-2个特性
     - 技术细节(Detail): 关键参数、数据、方法
     - 实用价值(Value): 能解决什么问题,适合谁用
   - 专有名词保留英文(如 GitHub, Benchmark, API)
   - 数字用阿拉伯数字(如 40KB, 95%, 3倍)
   - ✅ 好例子: "Z80-μLM是一个轻量级的对话AI系统,能够适应在40KB大小的存储空间内运行。它基于Z80微处理器架构设计,展示了在资源受限的环境中实现AI对话的能力。项目在GitHub上开源,由作者quesomaster9000发布,引起了Hacker News社区的关注和讨论。"
   - ❌ 坏例子: "- 新模型\n- 性能好\n- 开源了"(格式错误,太简略)

3. **heat_score（热度评分 1-5）**
   基于**影响范围**和**关注度**评分:
   - 5分: 行业颠覆性进展(如GPT-4首发,影响百万开发者)
   - 4分: 重要技术突破(如Llama 3发布,影响数十万人)
   - 3分: 值得关注的新工具/论文(GitHub 100+ stars,HN 50+评论)
   - 2分: 小众工具/实验性项目(GitHub 10-100 stars)
   - 1分: 边缘创新/个人项目(GitHub <10 stars)

   **判断依据**:
   - HN评论数: >100(5分), 50-100(4分), 20-50(3分), 5-20(2分), <5(1分)
   - GitHub stars: >10k(5分), 1k-10k(4分), 100-1k(3分), 10-100(2分), <10(1分)
   - 行业影响: 顶级公司发布(+1分), 学术会议论文(+1分)

4. **quality_score（质量评分 1-5）**
   基于**技术深度**和**实用价值**评分:
   - 5分: 顶级研究成果(NeurIPS Best Paper,被广泛引用的论文)
   - 4分: 高质量实用工具(完整文档,活跃维护,真实用户)
   - 3分: 有价值的内容(功能完整,可用但文档不全)
   - 2分: 初步尝试/实验性(功能单一,文档缺失)
   - 1分: 质量存疑(代码不全,无文档,概念性)

   **判断依据**:
   - 代码质量: 有测试(+1), 有文档(+1), 活跃维护(+1)
   - 技术深度: 算法创新(+1), 工程优化(+1), 系统设计(+1)
   - 实用性: 可直接使用(+1), 有案例(+1), 解决真实问题(+1)

5. **category（分类 - 单选）**
   - **技术突破**: 重大算法/架构创新(如新Transformer变体,新训练方法)
   - **开源工具**: 新的开源项目/库/框架(如新CLI工具,新Web框架)
   - **商业产品**: 公司发布的产品/服务(如OpenAI API,Anthropic Claude)
   - **论文研究**: 学术论文发表(如arXiv新论文,会议论文)
   - **行业动态**: 行业新闻/趋势分析(如公司战略,技术趋势)

6. **tags（关键词标签 - 3-5个）**
   - 优先级: 技术栈 > 应用领域 > 公司/组织
   - 英文,首字母大写
   - 避免过于宽泛的词(如AI, Tech)
   - ✅ 好例子: ["LLM", "Z80", "Microprocessor", "Open Source"]
   - ❌ 坏例子: ["AI", "Tech", "New", "Interesting"]

**返回格式**：
严格返回 JSON 格式,不要包含任何额外文字:
{
  "one_liner": "Z80-μLM: 40KB大小的对话AI",
  "summary": "Z80-μLM是一个轻量级的对话AI系统,能够适应在40KB大小的存储空间内运行。它基于Z80微处理器架构设计,展示了在资源受限的环境中实现AI对话的能力。项目在GitHub上开源,由作者quesomaster9000发布,引起了Hacker News社区的关注和讨论。",
  "heat_score": 3,
  "quality_score": 4,
  "category": "开源工具",
  "tags": ["Conversational AI", "Z80", "Microprocessor", "Open Source"]
}
"""

    SUMMARY_USER_PROMPT_TEMPLATE = """标题：{title}

URL：{url}

来源：{source}

元数据：{metadata}

匹配条件：{matched_conditions}

{source_specific_info}

请生成结构化摘要。"""

    async def generate(
        self, signal: RawSignal, matched_conditions: List[str]
    ) -> SummaryResult:
        """
        生成单个信号的摘要

        Args:
            signal: 原始信号
            matched_conditions: 匹配的过滤条件（A/B/C）

        Returns:
            SummaryResult 对象
        """
        # 为不同来源生成特定提示信息
        source_specific_info = ""
        if signal.source == "github":
            metadata = signal.metadata
            source_specific_info = f"""[GitHub 项目特定要求]
- 请在摘要中包含：项目语言({metadata.get('language', 'N/A')})、Star数({metadata.get('stars', 'N/A')})
- 请在 one_liner 中体现项目的主要功能
- heat_score 参考：Stars > 10k(5分), 1k-10k(4分), 100-1k(3分), <100(2分)
- quality_score 参考：有详细README(+1), 有文档(+1), 活跃维护(+1)
- tags 应包含：编程语言、技术栈、应用领域"""
        elif signal.source == "hn":
            metadata = signal.metadata
            source_specific_info = f"""[Hacker News 特定要求]
- HN评分: {metadata.get('score', 'N/A')}
- 评论数: {metadata.get('comments', 'N/A')}
- heat_score 参考：评论数 >100(5分), 50-100(4分), 20-50(3分), <20(2分)"""
        elif signal.source == "huggingface":
            metadata = signal.metadata
            item_type = metadata.get('type', 'unknown')

            if item_type == "model":
                source_specific_info = f"""[Hugging Face 模型特定要求]
- 请在摘要中包含：任务类型({metadata.get('pipeline_tag', 'N/A')})、Likes({metadata.get('likes', 'N/A')})、框架({metadata.get('library_name', 'N/A')})
- 请在 one_liner 中体现模型的主要功能和应用场景
- heat_score 参考：Likes > 5k(5分), 1k-5k(4分), 100-1k(3分), <100(2分)
- quality_score 参考：Downloads > 100k(+1), 有Model Card(+1), 多框架支持(+1)
- tags 应包含：任务类型、框架、应用领域、模型架构
- category 优先选择："技术突破"(新模型/SOTA)、"开源工具"(可直接使用的模型)"""
            else:  # dataset
                source_specific_info = f"""[Hugging Face 数据集特定要求]
- 请在摘要中包含：数据集规模、Likes({metadata.get('likes', 'N/A')})、应用领域
- 请在 one_liner 中体现数据集的主要用途
- heat_score 参考：Likes > 1k(5分), 500-1k(4分), 100-500(3分), <100(2分)
- quality_score 参考：Downloads > 10k(+1), 有详细说明(+1), 数据质量高(+1)
- tags 应包含：数据类型、应用领域、语言
- category 优先选择："开源工具"(公开数据集)、"论文研究"(论文配套数据集)"""

        user_prompt = self.SUMMARY_USER_PROMPT_TEMPLATE.format(
            title=signal.title,
            url=signal.url,
            source=signal.source,
            metadata=signal.metadata,
            matched_conditions=", ".join(matched_conditions) if matched_conditions else "无",
            source_specific_info=source_specific_info,
        )

        try:
            llm_response = await llm_client.call_json(
                self.SUMMARY_SYSTEM_PROMPT, user_prompt
            )

            # 计算 final_score (热度 + 质量的加权平均)
            # final_score = (heat_score * 0.6 + quality_score * 0.4)
            # 但为了简化，这里在 pipeline 中计算

            return SummaryResult(
                one_liner=llm_response.get("one_liner", ""),
                summary=llm_response.get("summary", ""),
                heat_score=max(1, min(5, llm_response.get("heat_score", 3))),
                quality_score=max(1, min(5, llm_response.get("quality_score", 3))),
                category=llm_response.get("category", "未分类"),
                tags=llm_response.get("tags", []),
            )

        except Exception as e:
            # LLM 调用失败，返回默认值
            print(f"[Generator] LLM call failed for {signal.url}: {e}")
            return SummaryResult(
                one_liner=signal.title[:50],  # 截取标题前 50 字符
                summary=f"来源：{signal.source}\n标题：{signal.title}",
                heat_score=3,
                quality_score=3,
                category="未分类",
                tags=[],
            )

    async def generate_batch(
        self, signals: List[RawSignal], matched_conditions_list: List[List[str]]
    ) -> List[SummaryResult]:
        """
        批量生成摘要（并行批处理优化）

        Args:
            signals: 原始信号列表
            matched_conditions_list: 每个信号匹配的条件列表

        Returns:
            SummaryResult 列表
        """
        if len(signals) != len(matched_conditions_list):
            raise ValueError(
                f"signals 和 matched_conditions_list 长度不一致: "
                f"{len(signals)} vs {len(matched_conditions_list)}"
            )

        # 并行批处理，每批10个避免API压力
        BATCH_SIZE = 10
        results = []

        for i in range(0, len(signals), BATCH_SIZE):
            batch_signals = signals[i:i+BATCH_SIZE]
            batch_conditions = matched_conditions_list[i:i+BATCH_SIZE]

            print(f"[Generator] Processing batch {i//BATCH_SIZE + 1}/{(len(signals)-1)//BATCH_SIZE + 1} ({len(batch_signals)} signals)...")

            # 并行处理当前批次
            tasks = [
                self.generate(signal, conditions)
                for signal, conditions in zip(batch_signals, batch_conditions)
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果，将异常转为默认值
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    signal = batch_signals[j]
                    print(f"[Generator] Failed to generate for {signal.url}: {result}")
                    results.append(SummaryResult(
                        one_liner=signal.title[:50],
                        summary=f"来源：{signal.source}\n标题：{signal.title}",
                        heat_score=3,
                        quality_score=3,
                        category="未分类",
                        tags=[],
                    ))
                else:
                    results.append(result)

        return results
