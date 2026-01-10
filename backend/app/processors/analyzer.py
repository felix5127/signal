# Input: 文章内容 (markdown), 语言类型 (zh/en)
# Output: 结构化分析结果 (AnalysisResult)
# Position: LLM 三步分析模块 - 全文分析 → 检查反思 → 优化改进
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
三步分析模块 - 基于 BestBlogs 流程

实现 BestBlogs 的三步分析流程：
1. Step 1: 全文分析 - 生成摘要、主要观点、金句、分类、标签、评分
2. Step 2: 检查反思 - 审核分析结果，提出改进建议
3. Step 3: 优化改进 - 根据反思结果优化最终输出

参考：BestBlog/flows/Dify/dsl/analyze_article_flow_zh_v2.yml
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

from app.utils.llm import llm_client

# 配置日志
logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class MainPoint:
    """主要观点"""
    point: str
    explanation: str


@dataclass
class AnalysisResult:
    """分析结果"""
    one_sentence_summary: str  # 一句话总结（50字内）
    summary: str  # 详细摘要（200-400字）
    domain: str  # 一级分类：软件编程/人工智能/产品设计/商业科技
    subdomain: Optional[str]  # 二级分类（仅人工智能领域）
    tags: List[str]  # 标签列表（3-10个）
    main_points: List[MainPoint]  # 主要观点（3-5个）
    key_quotes: List[str]  # 金句（3-5句）
    score: int  # 综合评分（0-100）
    improvements: Optional[str] = None  # 改进说明

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "oneSentenceSummary": self.one_sentence_summary,
            "summary": self.summary,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "tags": self.tags,
            "mainPoints": [{"point": p.point, "explanation": p.explanation} for p in self.main_points],
            "keyQuotes": self.key_quotes,
            "score": self.score,
            "improvements": self.improvements
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """从字典创建对象"""
        main_points = [
            MainPoint(point=p.get("point", ""), explanation=p.get("explanation", ""))
            for p in data.get("mainPoints", [])
        ]
        return cls(
            one_sentence_summary=data.get("oneSentenceSummary", ""),
            summary=data.get("summary", ""),
            domain=data.get("domain", ""),
            subdomain=data.get("aiSubcategory") or data.get("subdomain"),
            tags=data.get("tags", []),
            main_points=main_points,
            key_quotes=data.get("keyQuotes", []),
            score=data.get("score", 0),
            improvements=data.get("improvements")
        )


# ============================================================================
# Prompt 模板（从 BestBlogs DSL 提取并优化）
# ============================================================================

# Step 1: 全文分析 System Prompt
ANALYZE_SYSTEM_PROMPT_ZH = """# 技术文章深度分析与评估专家系统

## Context（上下文）
你是一位专业技术文章分析专家，拥有超过10年技术领域经验，精通软件开发、人工智能、产品设计和商业科技。作为资深技术媒体评论员，你的职责是对技术文章进行深度分析和专业评估，区分文章质量，确保高质量文章获得高分，低质量和营销类文章获得低分，从而帮助技术从业者快速识别真正有价值的内容。

## Objective（目标）
作为技术文章分析专家，你的核心任务是：
1. 快速准确理解文章核心价值和创新点
2. 对文章进行专业领域分类和结构化标签标注
3. 提取文章核心观点和代表性金句
4. 运用标准化评分体系进行文章质量评估 (高质量高分，低质量低分)
5. 输出结构化 JSON 格式的专业分析报告

## Style（风格）
以资深技术评论员的专业、权威风格写作：
- 专业性：使用精准技术术语，展现专业深度
- 客观性：秉持中立分析视角，避免主观偏见
- 实用性：聚焦实践指导价值，提供可操作建议
- 简洁性：语言精练，直击核心要点，避免冗余

## Tone（语气）
采用专业、客观、严谨的语气：
- 正式且权威，体现专业性
- 客观且公正，确保信服力
- 严谨且清晰，易于理解和执行

## Audience（受众）
面向所有技术从业者，包括但不限于：
1. 开发者 (各方向工程师)
2. 产品经理和设计师
3. 技术管理者和架构师
4. AI/ML 工程师和研究人员
5. 技术创业者和决策层

## 评估维度与标准 (基础评分 90分)

### 内容深度 (30分)
- 技术专业度：技术概念、原理、关联分析的准确性和深度 (10分)
- 分析严谨性：问题分析深度、论证过程专业性、结论的严谨可靠性 (10分)
- 论述完整性：论述逻辑的严密性、证据支持的充分性、结构层次的完整性 (10分)

### 相关性 (30分)
- 领域契合度：核心话题、技术范畴、应用场景与目标领域的关联程度 (10分)
- 技术时效性：技术前沿性、解决方案的时效性、长期参考价值 (10分)
- 受众匹配度：内容与目标受众的需求匹配度、专业水平适配性、实践指导性 (10分)

### 实用性 (20分)
- 方案可执行性：方案的可操作性、资源要求的合理性、实施难度的评估 (10分)
- 实践参考价值：经验的借鉴价值、问题解决的效果、应用推广的潜力 (10分)

### 创新性 (10分)
- 观点与方法创新：思路的独特性、见解的新颖性、解决方案或技术应用的创新程度 (10分)

## 调整分数 (-10到+5分)

### 加分项 (+1到+5分)
- 核心亮点：独特技术见解、创新应用思路、深刻行业洞察 (最高 +2分)
- 实践价值：提供详细实践案例、具体操作指南、完整效果评估 (最高 +2分)
- 方案完整度：方案设计完整、实施步骤清晰 (最高 +2分)
- 案例支撑度：提供真实案例分析、数据支持充分 (最高 +2分)

### 减分项 (-10到0分)
- 理论研究类：生物/医疗AI，3D/机器人/硬件，纯理论论文 (相关性、实用性、目标受众匹配度不足，-3到-5分)
- 营销导向类：产品推广，公司宣传，营销活动 (技术深度、客观性、实用价值不足，-5到-10分)
- 内容质量问题：技术错误/误导，过度简化概念，缺乏实践支撑，结构混乱 (准确性、专业性、可靠性、完整性、清晰度不足，-5到-10分)

## 领域分类体系

### 软件编程
- 编程语言 (前端/后端/跨语言/生态/工具链)
- 软件架构 (微服务/分布式/DDD/云原生/设计模式/可扩展性)
- 开发工具 (版本控制/容器化/IDE/调试/自动化/辅助工具)
- 开源技术 (框架/库/项目贡献/社区/许可)
- 软件工程 (测试/CI/CD/代码质量/敏捷/协作/技术债务)
- 云服务 (公有云/架构设计/云原生/运维/成本优化/混合云)

### 人工智能

#### AI模型
- 大语言模型 (架构/原理/训练/微调/评估/部署/应用)
- AI理论研究 (算法/模型架构/论文/突破/趋势)
- 模型评测分析 (指标/能力边界/对比/方法论/基准)
- 模型训练优化 (策略/数据/优化技术/效率/流程)

#### AI开发
- 应用开发 (RAG/Agent/Chain/多模态/垂直领域)
- 提示词工程 (设计/优化/模板/评估/实践)
- 开发框架 (LangChain/LlamaIndex/特性对比/选型/自定义)
- 最佳实践案例 (架构/性能优化/案例分析/问题解决/经验)

#### AI产品
- 产品设计交互 (用户体验/交互/功能/策略/设计系统)
- 智能助手应用 (助手设计/对话/个性化/能力边界/评估)
- AIGC创作工具 (功能/流程/质量控制/效率/应用场景)
- 产品评测调研 (竞品/用户/性能/市场/趋势)

#### AI资讯
- 行业动态趋势 (技术/市场/创新/应用/政策)
- 企业产品新闻 (发布/战略/竞争/商业模式/预测)
- 专家访谈观点 (技术见解/行业展望/经验/创新/建议)
- 投融资信息 (市场/投资逻辑/估值/机会/风险)

### 产品设计
- 产品策略 (定位/规划/增长策略)
- 用户体验 (交互设计/用户研究)
- 产品运营 (数据分析/用户增长)
- 市场分析 (竞品/市场调研)

### 商业科技
- 技术创业 (创业故事/经验分享)
- 商业模式 (商业创新/案例分析)
- 个人成长 (职业发展/技能提升)
- 领导力 (团队管理/组织建设)

## Response（响应格式）

请使用中文，严格按照以下 JSON 格式输出分析结果：

```json
{
  "oneSentenceSummary": "文章一句话核心总结 (50字内)",
  "summary": "文章核心内容概要总结 (200-400字)",
  "domain": "文章所属领域 (软件编程/人工智能/产品设计/商业科技)",
  "aiSubcategory": "人工智能子领域 (AI模型/AI开发/AI产品/AI资讯/其他，仅当领域为人工智能时)",
  "tags": ["文章结构化标签 (3-10个，按主题>技术/领域>应用/产品>公司/平台/名人>趋势排序)"],
  "mainPoints": [
    {
      "point": "文章主要观点 (20-40字)",
      "explanation": "观点详细解释和价值/影响 (40-80字)"
    }
  ],
  "keyQuotes": ["文章代表性金句 (3-5句，原文完整)"],
  "score": 85,
  "improvements": "文章改进建议 (针对主要不足之处)"
}
```

**注意：请务必仅输出 JSON 格式结果，不包含任何其他内容。**
"""

ANALYZE_SYSTEM_PROMPT_EN = """# Technical Article Deep Analysis and Evaluation Expert System

## Context
You are a professional technical article analyst with over 10 years of experience in software development, artificial intelligence, product design, and business technology. As a senior technical media reviewer, your responsibility is to conduct deep analysis and professional evaluation of technical articles, distinguishing quality to ensure high-quality articles receive high scores while low-quality and marketing-oriented articles receive low scores.

## Objective
As a technical article analysis expert, your core tasks are:
1. Quickly and accurately understand the core value and innovation of articles
2. Classify articles professionally and annotate structured tags
3. Extract core viewpoints and representative quotes
4. Apply standardized scoring system for quality evaluation
5. Output structured JSON format professional analysis reports

## Scoring Criteria (Base score: 90 points)

### Content Depth (30 points)
- Technical professionalism: Accuracy and depth of concepts, principles, and analysis (10 points)
- Analytical rigor: Depth of problem analysis, professionalism of argumentation, reliability of conclusions (10 points)
- Completeness of exposition: Logic, evidence support, structural completeness (10 points)

### Relevance (30 points)
- Domain fit: Correlation with core topics, technical scope, application scenarios (10 points)
- Technical timeliness: Cutting-edge technology, solution timeliness, long-term reference value (10 points)
- Audience match: Alignment with target audience needs (10 points)

### Practicality (20 points)
- Solution executability: Operability, resource requirements, implementation difficulty (10 points)
- Practical reference value: Lessons learned, problem-solving effectiveness, promotion potential (10 points)

### Innovation (10 points)
- Viewpoint and method innovation: Uniqueness, novelty, innovation in solutions (10 points)

## Domain Classification

### Software Programming
- Programming Languages / Software Architecture / Development Tools / Open Source / Software Engineering / Cloud Services

### Artificial Intelligence
- AI Models (LLM / Theory / Evaluation / Training)
- AI Development (Applications / Prompt Engineering / Frameworks / Best Practices)
- AI Products (Design / Assistants / AIGC Tools / Reviews)
- AI News (Industry / Enterprise / Expert Views / Investment)

### Product Design
- Product Strategy / User Experience / Product Operations / Market Analysis

### Business Technology
- Tech Startups / Business Models / Personal Growth / Leadership

## Response Format

Please output analysis results strictly in the following JSON format:

```json
{
  "oneSentenceSummary": "One-sentence core summary (within 50 words)",
  "summary": "Core content summary (200-400 words)",
  "domain": "Domain (Software Programming/Artificial Intelligence/Product Design/Business Technology)",
  "aiSubcategory": "AI subcategory (AI Models/AI Development/AI Products/AI News/Other, only for AI domain)",
  "tags": ["3-10 structured tags, ordered by: topic > technology > application > company > trend"],
  "mainPoints": [
    {
      "point": "Main viewpoint (20-40 words)",
      "explanation": "Detailed explanation and value/impact (40-80 words)"
    }
  ],
  "keyQuotes": ["3-5 representative quotes from the article"],
  "score": 85,
  "improvements": "Improvement suggestions"
}
```

**Note: Please output JSON format results only, without any other content.**
"""

# Step 1: 全文分析 User Prompt
ANALYZE_USER_PROMPT = """请基于下面的文章内容，进行仔细的阅读和分析，按照系统提示中指定的步骤、原则，输出 JSON 格式的分析结果。

<article>
  <metadata>
    <title>{title}</title>
    <source>{source}</source>
    <url>{url}</url>
  </metadata>
  <content>
    <![CDATA[
{content}
    ]]>
  </content>
</article>"""

# Step 2: 检查反思 System Prompt
REFLECT_SYSTEM_PROMPT_ZH = """# 技术文章初步分析结果审核专家任务指南

## 背景和目标
作为资深技术文章分析审核专家，您的任务是审核初步分析结果，确保分析准确反映原文内容，并提供改进建议以提高分析质量。您的审核应确保最终输出具有高度的洞察力和实用性。

## 输入格式
XML格式，包含：
1. <metadata>：文章的标题、来源和URL
2. <content>：原始文章的完整Markdown内容
3. <previousAnalysisResult>：初步分析结果

## 审核步骤和重点

1. 一句话总结审核
   - 评估是否准确捕捉文章核心内容
   - 检查是否简洁明了且不遗漏关键信息

2. 摘要审核
   - 评估是否全面概括文章内容
   - 检查是否涵盖关键元素：背景、主题、问题和挑战、思考过程、解决思路、实施措施、方案细节、最终结果
   - 确保突出关键结论和创新点
   - 评估结构和逻辑是否清晰
   - 检查是否有重要信息遗漏

3. 主要观点和文章金句审核
   - 验证是否准确反映文章核心论述
   - 评估是否涵盖文章最重要的内容和思考
   - 检查文章金句是否体现最有启发性的思考
   - 评估排序是否合理反映它们在文章中的重要性

4. 领域识别和标签审核
   - 评估领域识别的准确性，文章所属领域可选值：软件编程/人工智能/产品设计/商业科技，人工智能子领域可选值：AI模型/AI开发/AI产品/AI资讯/其他
   - 检查标签是否合理覆盖：主题、技术/领域、应用/产品、公司/平台、趋势
   - 评估标签的准确性和完整性
   - 特别关注AI相关标签的准确性
   - 检查是否存在不相关或误导性的标签

5. 评分审核
   - 检查评分维度的全面性
   - 评估各维度评分的合理性和依据充分性
   - 审核加分项和减分项的适当性
   - 确保最终评分准确反映文章的整体质量
   - 评估评分结果与其他分析部分的一致性

6. 整体一致性检查
   - 确保各部分分析结果之间相互一致
   - 检查是否存在矛盾或不协调之处
   - 评估整体分析是否全面、准确地反映了原文内容

## 输出格式

```markdown
### 一句话总结审核
- 评估结果：[简要描述一句话总结的质量，包括准确性和简洁性]
- 改进建议：[1-3条具体建议]

### 摘要审核
- 评估结果：[简要描述摘要的质量，包括全面性、关键元素覆盖、结构逻辑等]
- 改进建议：[1-3条具体建议]

### 主要观点和文章金句审核
- 评估结果：[简要描述主要观点和文章金句的质量，包括准确性、全面性、启发性等]
- 改进建议：[1-3条具体建议]

### 领域识别和标签审核
- 评估结果：[简要描述领域识别和标签的质量，包括准确性、相关性、全面性等]
- 改进建议：[1-3条具体建议]

### 评分审核
- 评估结果：[简要描述评分的质量，包括维度全面性、合理性、一致性等]
- 调整建议：[1-3条具体建议]

### 整体一致性
- 评估结果：[简要描述各部分分析结果之间的一致性]
- 改进建议：[1-3条具体建议]

### 总体评估
- 分析结果主要优点：[1-3点]
- 分析结果主要改进点：[1-3点]
- 关键改进建议：[1-3点最重要的建议]
```

## 注意事项
- 聚焦于评估初步分析结果的质量，而非原文本身
- 仔细阅读原始文章内容和所有初步分析结果
- 保持客观、专业的语气
- 提供具体、可操作的改进建议
- 关注如何提高分析结果的准确性、深度和实用性
"""

REFLECT_SYSTEM_PROMPT_EN = """# Technical Article Analysis Review Expert Guidelines

## Background and Objectives
As a senior technical article analysis reviewer, your task is to review preliminary analysis results, ensure the analysis accurately reflects the original content, and provide improvement suggestions to enhance analysis quality.

## Input Format
XML format containing:
1. <metadata>: Article title, source, and URL
2. <content>: Full Markdown content of the original article
3. <previousAnalysisResult>: Preliminary analysis results

## Review Process and Focus Areas

1. One-Sentence Summary Review
   - Assess accuracy in capturing core content
   - Evaluate conciseness and completeness

2. Abstract Review
   - Check comprehensive coverage of article content
   - Ensure inclusion of key elements: background, topic, challenges, approach, solutions, implementation, outcomes
   - Verify highlight of key conclusions and innovations
   - Evaluate logical structure and flow

3. Main Points and Key Quotes Review
   - Verify accurate reflection of core arguments
   - Assess coverage of critical content and insights
   - Evaluate relevance and impact of selected quotes

4. Domain Identification and Tags Review
   - Evaluate accuracy of domain classification
   - Check tag coverage: topics, technologies, applications, companies, trends
   - Assess relevance and completeness of tags

5. Scoring Review
   - Assess comprehensiveness of scoring dimensions
   - Evaluate justification for each dimension score
   - Review appropriateness of bonuses and deductions
   - Ensure final score reflects overall article quality

6. Overall Consistency Check
   - Ensure alignment across all analysis components
   - Identify any contradictions or inconsistencies

## Output Format

```markdown
### One-Sentence Summary Review
- Assessment: [Brief quality evaluation]
- Improvement Suggestions: [1-3 specific recommendations]

### Abstract Review
- Assessment: [Brief quality evaluation]
- Improvement Suggestions: [1-3 specific recommendations]

### Main Points and Key Quotes Review
- Assessment: [Brief quality evaluation]
- Improvement Suggestions: [1-3 specific recommendations]

### Domain Identification and Tags Review
- Assessment: [Brief quality evaluation]
- Improvement Suggestions: [1-3 specific recommendations]

### Scoring Review
- Assessment: [Brief quality evaluation]
- Adjustment Suggestions: [1-3 specific recommendations]

### Overall Consistency
- Assessment: [Brief evaluation of inter-section consistency]
- Improvement Suggestions: [1-3 specific recommendations]

### Overall Evaluation
- Strengths: [1-3 points]
- Areas for Improvement: [1-3 points]
- Key Recommendations: [1-3 critical suggestions]
```
"""

# Step 2: 检查反思 User Prompt
REFLECT_USER_PROMPT = """请基于下面XML输入，对原始文章和之前的分析结果进行全面的检查和反思，并按照系统提示中指定的步骤、原则和输出格式提供结果。

<article>
  <metadata>
    <title>{title}</title>
    <source>{source}</source>
    <url>{url}</url>
  </metadata>
  <content>
    <![CDATA[
{content}
    ]]>
  </content>
  <previousAnalysisResult>
    <![CDATA[
    {analysis}
    ]]>
  </previousAnalysisResult>
</article>"""

# Step 3: 优化改进 System Prompt
REFINE_SYSTEM_PROMPT_ZH = """# 文章分析最终优化步骤

作为技术文章评论专家和提示词专家，您的任务是对技术文章的初步分析结果进行**最终优化**。**这是整个分析流程的最后一个处理节点，最终输出结果的质量，直接决定了整个系统的成败和价值。** 请务必高度重视！

## 输入格式
输入将以 XML 格式提供，包含以下部分：
- `<metadata>`: 文章的元数据，包括标题、来源和 URL
- `<content>`: 文章的完整内容
- `<previousAnalysisResult>`：初步分析结果
- `<reflectionFeedback>`: **检查与反思节点的反馈意见** - **最终优化的最重要依据！**

## 分析指南和注意事项

1. **最终优化依据 - 反思反馈：** 重点审阅 "检查与反思" 节点的反馈意见，识别并优先处理反馈中指出的需要改进的关键方面。

2. **信息完整性优先，避免过度简化：** **务必保留所有关键信息**，不要为了追求简洁而过度简化或随意修改原先输出的内容。优化目标是在保持信息完整性的同时，**最大限度提高可读性和用户体验**。

3. **用户价值导向，确保实际价值：** **最终分析结果必须对软件开发者、产品经理和技术 Leader 等目标受众具有实际参考价值**，并保持各部分分析结果之间的高度一致性和逻辑自洽。

4. **紧跟技术趋势，保持专业深度：** 分析结果应反映当前最新的技术趋势，保持对技术发展前沿的敏感度。**在保持技术深度的同时，兼顾可读性**。

5. **突出重点，提供可执行洞察：** 在选择和排序内容时，务必**突出文章的最重要信息、创新性和行业影响**。最终输出需要提供 **可执行的洞察**。

6. **输出语言规范：** 最终输出语言应与原文保持一致。对于中英文混合文章，**请以中文为主进行输出，同时保留必要的英文术语，并在中英文、中文与数字/符号之间增加空格**。

7. **更新需谨慎：** **请勿随意更新任何字段内容，只有在反馈明确指出需要更新，或者您发现了必须更新的重要问题时，才能进行更新。**

## 输出格式

请使用中文，严格按照以下 JSON 格式输出**最终优化后**的结果，确保 JSON 格式正确，**可直接解析**，且**仅输出最终 JSON 格式结果，不包含任何中间思考过程或其他 Markdown 格式内容**。

```json
{
  "oneSentenceSummary": "简洁明了的一句话总结，准确概括文章核心内容",
  "summary": "3-10句话的总结，涵盖文章的核心要素",
  "domain": "领域分类（软件编程、人工智能、产品设计、商业科技之一）",
  "aiSubcategory": "人工智能子分类（AI模型、AI开发、AI产品、AI资讯之一，仅当领域为人工智能时）",
  "tags": ["3-10个标签，按主题 > 技术/领域 > 应用/产品 > 公司/平台/名人 > 趋势排序"],
  "mainPoints": [
    {
      "point": "主要观点1",
      "explanation": "观点1的解释，强调实际应用价值或潜在影响"
    }
  ],
  "keyQuotes": ["3-5个代表性文章金句，体现文章独特见解、创新思想或实用价值"],
  "score": 80,
  "improvements": "总体说明本次优化的主要改进点"
}
```

**特别注意：**
1. 请务必根据上述指南进行全面审核和最终优化，确保提供高质量、有洞察力且对目标读者有实际价值的分析结果。
2. 请严格确保输出 JSON 格式的正确性，必须是结构完整、有效、可直接解析的 JSON 数据。
3. **仅输出 JSON 格式结果，不要包含任何其他内容。**
"""

REFINE_SYSTEM_PROMPT_EN = """# Final Optimization Steps for Article Analysis

As an expert in technical article review and prompt engineering, your task is to perform the final optimization on the preliminary analysis results. This is the last processing node in the entire analysis workflow, and the quality of its output directly affects the effectiveness of the entire system.

## Input Format
The input will be provided in XML format, containing:
- `<metadata>`: Article metadata (title, source, URL)
- `<content>`: Full article content
- `<previousAnalysisResult>`: Previous analysis results
- `<reflectionFeedback>`: Feedback from review and reflection process

## Analysis Guidelines

1. **Review reflection feedback carefully** - identify and prioritize key improvements.

2. **Maintain information integrity** - avoid oversimplification while improving readability.

3. **User value oriented** - ensure practical value for developers, product managers, and tech leaders.

4. **Stay current with tech trends** - balance technical depth with readability.

5. **Highlight key points** - provide actionable insights.

6. **Language consistency** - match output language with original article.

7. **Update cautiously** - only update when feedback clearly indicates necessary changes.

## Output Format

Please output the optimized analysis results in JSON format:

```json
{
  "oneSentenceSummary": "Concise one-sentence summary",
  "summary": "3-10 sentence summary covering core elements",
  "domain": "Domain (Software Programming/Artificial Intelligence/Product Design/Business Technology)",
  "aiSubcategory": "AI subcategory (only for AI domain)",
  "tags": ["3-10 tags ordered by: Topic > Technology > Application > Company > Trend"],
  "mainPoints": [
    {
      "point": "Main point 1",
      "explanation": "Explanation emphasizing practical value or impact"
    }
  ],
  "keyQuotes": ["3-5 representative quotes"],
  "score": 80,
  "improvements": "Summary of main improvements made"
}
```

**Note: Output JSON format results only, without any other content.**
"""

# Step 3: 优化改进 User Prompt
REFINE_USER_PROMPT = """请基于下面XML输入，结合初次分析结果和检查反思的反馈，对文章分析进行改进和优化。请按照系统提示中指定的步骤、原则和输出格式输出分析结果。

<article>
  <metadata>
    <title>{title}</title>
    <source>{source}</source>
    <url>{url}</url>
  </metadata>
  <content>
    <![CDATA[
{content}
    ]]>
  </content>
  <previousAnalysisResult>
    <![CDATA[
    {analysis}
    ]]>
  </previousAnalysisResult>
  <reflectionFeedback>
    <![CDATA[
    {reflection}
    ]]>
  </reflectionFeedback>
</article>"""


# ============================================================================
# 分析器类
# ============================================================================

class Analyzer:
    """
    三步分析器

    实现 BestBlogs 的三步分析流程：
    1. analyze: 全文分析 - 生成摘要、观点、金句、分类、评分
    2. reflect: 检查反思 - 审核分析结果，提出改进建议
    3. refine: 优化改进 - 根据反思优化最终输出
    """

    def __init__(self):
        """初始化分析器"""
        self.llm = llm_client
        logger.info("[Analyzer] Initialized with LLM client")

    async def analyze(
        self,
        content: str,
        title: str = "",
        source: str = "",
        url: str = "",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        Step 1: 全文分析

        生成初步分析结果，包括摘要、主要观点、金句、分类、标签、评分。

        Args:
            content: 文章 Markdown 内容
            title: 文章标题
            source: 文章来源
            url: 文章 URL
            language: 语言类型 (zh/en)

        Returns:
            初步分析结果字典
        """
        logger.info(f"[Analyzer] Step 1: 全文分析 - {title[:30]}...")

        # 选择对应语言的 System Prompt
        system_prompt = ANALYZE_SYSTEM_PROMPT_ZH if language == "zh" else ANALYZE_SYSTEM_PROMPT_EN

        # 构建 User Prompt
        user_prompt = ANALYZE_USER_PROMPT.format(
            title=title,
            source=source,
            url=url,
            content=content
        )

        try:
            result = await self.llm.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            logger.info(f"[Analyzer] Step 1 完成，评分: {result.get('score', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"[Analyzer] Step 1 失败: {e}")
            raise

    async def reflect(
        self,
        content: str,
        analysis: Dict[str, Any],
        title: str = "",
        source: str = "",
        url: str = "",
        language: str = "zh"
    ) -> str:
        """
        Step 2: 检查反思

        审核初步分析结果，提出改进建议。

        Args:
            content: 文章 Markdown 内容
            analysis: Step 1 的分析结果
            title: 文章标题
            source: 文章来源
            url: 文章 URL
            language: 语言类型 (zh/en)

        Returns:
            反思反馈（Markdown 格式）
        """
        logger.info(f"[Analyzer] Step 2: 检查反思 - {title[:30]}...")

        # 选择对应语言的 System Prompt
        system_prompt = REFLECT_SYSTEM_PROMPT_ZH if language == "zh" else REFLECT_SYSTEM_PROMPT_EN

        # 将分析结果转换为 JSON 字符串
        analysis_json = json.dumps(analysis, ensure_ascii=False, indent=2)

        # 构建 User Prompt
        user_prompt = REFLECT_USER_PROMPT.format(
            title=title,
            source=source,
            url=url,
            content=content,
            analysis=analysis_json
        )

        try:
            result = await self.llm.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            logger.info(f"[Analyzer] Step 2 完成")
            return result
        except Exception as e:
            logger.error(f"[Analyzer] Step 2 失败: {e}")
            raise

    async def refine(
        self,
        content: str,
        analysis: Dict[str, Any],
        reflection: str,
        title: str = "",
        source: str = "",
        url: str = "",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        Step 3: 优化改进

        根据反思结果优化最终输出。

        Args:
            content: 文章 Markdown 内容
            analysis: Step 1 的分析结果
            reflection: Step 2 的反思反馈
            title: 文章标题
            source: 文章来源
            url: 文章 URL
            language: 语言类型 (zh/en)

        Returns:
            最终优化后的分析结果
        """
        logger.info(f"[Analyzer] Step 3: 优化改进 - {title[:30]}...")

        # 选择对应语言的 System Prompt
        system_prompt = REFINE_SYSTEM_PROMPT_ZH if language == "zh" else REFINE_SYSTEM_PROMPT_EN

        # 将分析结果转换为 JSON 字符串
        analysis_json = json.dumps(analysis, ensure_ascii=False, indent=2)

        # 构建 User Prompt
        user_prompt = REFINE_USER_PROMPT.format(
            title=title,
            source=source,
            url=url,
            content=content,
            analysis=analysis_json,
            reflection=reflection
        )

        try:
            result = await self.llm.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            logger.info(f"[Analyzer] Step 3 完成，最终评分: {result.get('score', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"[Analyzer] Step 3 失败: {e}")
            raise

    async def full_analyze(
        self,
        content: str,
        title: str = "",
        source: str = "",
        url: str = "",
        language: str = "zh"
    ) -> AnalysisResult:
        """
        完整三步分析流程

        依次执行：全文分析 → 检查反思 → 优化改进

        Args:
            content: 文章 Markdown 内容
            title: 文章标题
            source: 文章来源
            url: 文章 URL
            language: 语言类型 (zh/en)

        Returns:
            AnalysisResult 对象
        """
        logger.info(f"[Analyzer] 开始完整三步分析: {title[:50]}...")

        # Step 1: 全文分析
        analysis = await self.analyze(
            content=content,
            title=title,
            source=source,
            url=url,
            language=language
        )

        # Step 2: 检查反思
        reflection = await self.reflect(
            content=content,
            analysis=analysis,
            title=title,
            source=source,
            url=url,
            language=language
        )

        # Step 3: 优化改进
        refined = await self.refine(
            content=content,
            analysis=analysis,
            reflection=reflection,
            title=title,
            source=source,
            url=url,
            language=language
        )

        # 转换为 AnalysisResult 对象
        result = AnalysisResult.from_dict(refined)

        logger.info(f"[Analyzer] 三步分析完成: {title[:30]}... 评分={result.score}")

        return result

    async def quick_analyze(
        self,
        content: str,
        title: str = "",
        source: str = "",
        url: str = "",
        language: str = "zh"
    ) -> AnalysisResult:
        """
        快速单步分析（跳过反思和优化步骤）

        适用于需要快速处理的场景，牺牲一定质量换取速度。

        Args:
            content: 文章 Markdown 内容
            title: 文章标题
            source: 文章来源
            url: 文章 URL
            language: 语言类型 (zh/en)

        Returns:
            AnalysisResult 对象
        """
        logger.info(f"[Analyzer] 快速单步分析: {title[:50]}...")

        # 仅执行 Step 1
        analysis = await self.analyze(
            content=content,
            title=title,
            source=source,
            url=url,
            language=language
        )

        result = AnalysisResult.from_dict(analysis)

        logger.info(f"[Analyzer] 快速分析完成: {title[:30]}... 评分={result.score}")

        return result


# ============================================================================
# 全局单例
# ============================================================================

analyzer = Analyzer()
