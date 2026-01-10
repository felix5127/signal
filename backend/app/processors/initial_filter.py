# Input: 文章标题、内容、来源（来自 scrapers 或 RSS）
# Output: InitialFilterResult（是否忽略、价值评分、一句话摘要、语言类型）
# Position: LLM 初评层，快速筛选值得深入分析的内容，支持中英文分流
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import re
from typing import List, Optional
from dataclasses import dataclass, field

from app.utils.llm import llm_client


@dataclass
class InitialFilterResult:
    """
    初评结果数据模型

    字段说明：
    - ignore: 是否应该忽略这篇文章
    - reason: 判断原因（30-50字）
    - value: 价值评分（0-5）
    - summary: 一句话总结
    - language: 语言类型（zh/en）
    """
    ignore: bool
    reason: str
    value: int  # 0-5
    summary: str
    language: str  # zh/en


class InitialFilter:
    """
    初评过滤器

    两阶段过滤：
    1. 规则预筛（关键词匹配、来源白名单、语言检测）
    2. LLM 初评（判断内容是否值得深入分析）

    评分标准（0-5）：
    - 0: 应被忽略的文章（非中英文或完全不相关）
    - 1: 低质量或基本不相关，不推荐阅读
    - 2: 质量较低或相关性较弱，但可能有少量参考价值
    - 3: 一般质量，内容相关且有一定深度，但缺乏独特见解或创新性，值得一读
    - 4: 高质量，提供了有价值的见解或实用信息，推荐阅读
    - 5: 极高质量，提供了深度分析、创新思路或重要解决方案，强烈推荐阅读
    """

    # ================== 规则预筛关键词 ==================

    # 高价值关键词（命中任一个增加通过概率）
    HIGH_VALUE_KEYWORDS = [
        # AI/ML 相关
        "AI", "LLM", "GPT", "Claude", "Gemini", "Llama", "Transformer",
        "机器学习", "深度学习", "人工智能", "大语言模型", "神经网络",
        "Machine Learning", "Deep Learning", "Neural Network",
        # 技术突破
        "开源", "发布", "新版本", "突破", "创新",
        "Open Source", "Release", "Breakthrough", "Innovation",
        # 工程实践
        "架构", "性能优化", "最佳实践", "案例分析",
        "Architecture", "Performance", "Best Practice", "Case Study",
        # 产品设计
        "产品设计", "用户体验", "UX", "UI",
        "Product Design", "User Experience",
        # 创业商业
        "创业", "融资", "商业模式", "增长",
        "Startup", "Funding", "Business Model", "Growth",
    ]

    # 低价值关键词（命中任一个降低通过概率）
    LOW_VALUE_KEYWORDS = [
        # 广告营销
        "广告", "促销", "限时优惠", "点击购买", "立即下单",
        "Advertisement", "Promotion", "Limited Offer", "Buy Now",
        # 招聘信息
        "招聘", "求职", "简历", "职位",
        "Hiring", "Job Opening", "Resume", "Position",
        # 闲聊八卦
        "八卦", "吐槽", "闲聊",
        "Gossip", "Rant",
        # 低质量内容
        "转发", "点赞", "关注", "收藏",
        "Retweet", "Like", "Follow", "Bookmark",
    ]

    # 来源白名单（这些来源的内容默认高质量）
    SOURCE_WHITELIST = [
        # 知名技术博客
        "Paul Graham", "Martin Fowler", "Joel on Software",
        "Netflix Tech Blog", "Google AI Blog", "OpenAI Blog",
        "Anthropic", "Meta AI", "Microsoft Research",
        # 知名中文博客
        "阮一峰", "张鑫旭", "酷壳", "美团技术",
        # 学术来源
        "arXiv", "Papers with Code", "Google Scholar",
        # 顶级媒体
        "Hacker News", "TechCrunch", "The Verge",
    ]

    # ================== LLM Prompts ==================

    # 中文文章初评 System Prompt
    SYSTEM_PROMPT_ZH = """(C) 上下文：你是一个高级内容分析助手，为一个面向技术从业者、创业者和产品经理的网站筛选文章。这个网站主要收集和分享有关软件开发、人工智能、产品管理、营销、设计、商业、科技和个人成长等领域的高质量内容。

(O) 目标：你的任务是快速分析给定的文章，并决定是否应该忽略这篇文章。你需要识别出低价值、不相关或质量较差的内容，同时确保不会错过潜在的高价值文章。

(S) 风格：请以一个经验丰富的内容策展人的风格来分析和评判文章。你应该简洁明了，直击要点，并能够快速识别出文章的核心价值。

(T) 语气：保持专业、客观的语气。你的分析应该基于事实和明确的标准，而不是主观感受。

(A) 受众：你的分析结果将被网站的内容管理团队使用，他们需要快速决策是否将文章纳入网站的内容库。

(R) 响应：请使用中文以JSON格式输出你的分析结果，包括以下字段：
- ignore: 布尔值，表示是否应该忽略这篇文章
- reason: 字符串，简要说明做出该判断的主要原因（限30-50字）
- value: 用0-5的整数评分表示文章的价值（0表示应被忽略，1-5表示价值等级）
- summary: 用一句话总结文章的主要内容
- language: 字符串，表示文章的语言类型（如"zh"、"en"、"ja"等）

请根据以下标准分析文章：

1. 语言：是否为中文或英文。如果不是，直接忽略。
2. 内容类型：是否为实质性内容，而非简单的公告、活动预热、广告、产品推荐或闲聊。
3. 主题相关性：是否与目标领域相关（软件开发、人工智能、产品管理、营销、设计、商业、科技和个人成长等）。
4. 质量和价值：
   - 内容深度：是否提供深入见解、独特观点或有价值信息
   - 技术深度：对于技术文章，评估其专业程度和技术细节
   - 实用性：是否能启发思考或提供实用解决方案

评分标准：
- 0：应被忽略的文章（非中英文或完全不相关）
- 1：低质量或基本不相关，不推荐阅读
- 2：质量较低或相关性较弱，但可能有少量参考价值
- 3：一般质量，内容相关且有一定深度，但缺乏独特见解或创新性，值得一读
- 4：高质量，提供了有价值的见解或实用信息，推荐阅读
- 5：极高质量，提供了深度分析、创新思路或重要解决方案，强烈推荐阅读

请注意，即使对于建议忽略的文章，也要提供 value、summary 和 language 字段。value 应该反映文章对目标受众的潜在价值，即使这个值很低或为0。summary 应该简要概括文章的主要内容，无论是否相关。language 字段应始终指明文章的语言类型。"""

    # 英文文章初评 System Prompt
    SYSTEM_PROMPT_EN = """(C) Context: You are an advanced content analysis assistant, screening articles for a website targeting technology professionals, entrepreneurs, and product managers. This website primarily collects and shares high-quality content related to software development, artificial intelligence, product management, marketing, design, business, technology, and personal growth.

(O) Objective: Your task is to quickly analyze given articles and decide whether they should be ignored. You need to identify low-value, irrelevant, or poor-quality content while ensuring that potentially high-value articles are not overlooked.

(S) Style: Please analyze and evaluate articles in the style of an experienced content curator. Be concise, get straight to the point, and quickly identify the core value of each article.

(T) Tone: Maintain a professional and objective tone. Your analysis should be based on facts and clear criteria, not subjective feelings.

(A) Audience: Your analysis results will be used by the website's content management team, who need to make quick decisions on whether to include articles in the website's content library.

(R) Response: Please output your analysis results in JSON format using Chinese, including the following fields:
- ignore: Boolean value indicating whether this article should be ignored
- reason: String briefly explaining the main reason for this judgment (limit 30-50 characters)
- value: Integer score from 0-5 representing the article's value (0 means it should be ignored, 1-5 indicates value level)
- summary: One sentence summarizing the main content of the article
- language: String indicating the language of the article (e.g., "zh", "en", "ja", etc.)

Please analyze articles based on the following criteria:

1. Language: Is it in Chinese or English? If not, ignore it directly.
2. Content type: Is it substantial content, rather than simple announcements, event teasers, advertisements, product recommendations, or casual chat?
3. Topic relevance: Is it related to the target areas (software development, artificial intelligence, product management, marketing, design, business, technology, and personal growth, etc.)?
4. Quality and value:
   - Content depth: Does it provide in-depth insights, unique perspectives, or valuable information?
   - Technical depth: For technical articles, assess their professionalism and technical details
   - Practicality: Can it inspire thinking or provide practical solutions?

Scoring criteria:
- 0: Articles that should be ignored (non-Chinese/English or completely irrelevant)
- 1: Low quality or barely relevant, not recommended for reading
- 2: Relatively low quality or weak relevance, but may have some reference value
- 3: Average quality, relevant content with some depth, but lacking unique insights or innovation. Worth reading.
- 4: High quality, providing valuable insights or practical information, recommended reading
- 5: Exceptionally high quality, providing in-depth analysis, innovative ideas, or important solutions. Strongly recommended reading.

Please note that even for articles suggested to be ignored, you should still provide the value, summary, and language fields. The value should reflect the potential value of the article to the target audience, even if this value is very low or 0. The summary should briefly outline the main content of the article, regardless of its relevance. The language field should always indicate the language of the article."""

    # User Prompt 模板
    USER_PROMPT_TEMPLATE = """请根据要求基于以下文章进行分析，并输出指定格式的 JSON 字符串。

<article>
  <title>{title}</title>
  <link>{url}</link>
  <source>{source}</source>
  <content>
<![CDATA[
{content}
]]></content>
</article>"""

    def __init__(self, source_whitelist: Optional[List[str]] = None):
        """
        初始化初评过滤器

        Args:
            source_whitelist: 自定义来源白名单（可选，将与默认白名单合并）
        """
        self.source_whitelist = set(self.SOURCE_WHITELIST)
        if source_whitelist:
            self.source_whitelist.update(source_whitelist)

    def _detect_language(self, text: str) -> str:
        """
        检测文本语言（简单规则）

        Args:
            text: 输入文本

        Returns:
            语言代码：zh/en/other
        """
        if not text:
            return "other"

        # 统计中文字符数量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文单词数量
        english_words = len(re.findall(r'[a-zA-Z]+', text))

        total_len = len(text)
        if total_len == 0:
            return "other"

        chinese_ratio = chinese_chars / total_len

        # 中文字符占比超过 20% 认为是中文
        if chinese_ratio > 0.2:
            return "zh"
        # 英文单词较多认为是英文
        elif english_words > 5:
            return "en"
        else:
            return "other"

    def _check_keywords(self, title: str, content: str) -> tuple[int, List[str]]:
        """
        关键词匹配检查

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            (score_adjustment, matched_keywords) - 分数调整值和匹配的关键词
        """
        text = f"{title} {content}".lower()

        high_value_matched = []
        low_value_matched = []

        # 检查高价值关键词
        for keyword in self.HIGH_VALUE_KEYWORDS:
            if keyword.lower() in text:
                high_value_matched.append(keyword)

        # 检查低价值关键词
        for keyword in self.LOW_VALUE_KEYWORDS:
            if keyword.lower() in text:
                low_value_matched.append(keyword)

        # 计算分数调整：高价值 +1（最多+2），低价值 -1（最多-2）
        score_adjustment = min(len(high_value_matched), 2) - min(len(low_value_matched), 2)

        return score_adjustment, high_value_matched + low_value_matched

    def _is_whitelist_source(self, source: str) -> bool:
        """
        检查是否为白名单来源

        Args:
            source: 来源名称

        Returns:
            是否在白名单中
        """
        if not source:
            return False

        source_lower = source.lower()
        for whitelist_source in self.source_whitelist:
            if whitelist_source.lower() in source_lower:
                return True
        return False

    def rule_filter(self, title: str, content: str, source: str = "") -> dict:
        """
        规则预筛

        快速判断文章是否明显不符合要求，避免不必要的 LLM 调用。

        Args:
            title: 文章标题
            content: 文章内容
            source: 文章来源

        Returns:
            {
                "should_skip_llm": bool,  # 是否跳过 LLM 评估
                "preliminary_result": InitialFilterResult or None,  # 如果跳过，返回预判结果
                "language": str,  # 检测到的语言
                "is_whitelist": bool,  # 是否白名单来源
                "keyword_score_adj": int,  # 关键词分数调整
            }
        """
        # 1. 语言检测
        text_for_detection = f"{title} {content[:500]}"  # 使用标题和内容前500字符
        language = self._detect_language(text_for_detection)

        # 非中英文直接拒绝
        if language == "other":
            return {
                "should_skip_llm": True,
                "preliminary_result": InitialFilterResult(
                    ignore=True,
                    reason="文章不是中文或英文",
                    value=0,
                    summary="文章语言不符合要求",
                    language=language,
                ),
                "language": language,
                "is_whitelist": False,
                "keyword_score_adj": 0,
            }

        # 2. 内容长度检查
        content_length = len(content)
        if content_length < 100:  # 内容太短
            return {
                "should_skip_llm": True,
                "preliminary_result": InitialFilterResult(
                    ignore=True,
                    reason="内容过短，缺乏实质性信息",
                    value=0,
                    summary=title if title else "内容过短",
                    language=language,
                ),
                "language": language,
                "is_whitelist": False,
                "keyword_score_adj": 0,
            }

        # 3. 关键词检查
        keyword_score_adj, matched_keywords = self._check_keywords(title, content)

        # 4. 白名单来源检查
        is_whitelist = self._is_whitelist_source(source)

        # 返回规则预筛结果（需要 LLM 进一步评估）
        return {
            "should_skip_llm": False,
            "preliminary_result": None,
            "language": language,
            "is_whitelist": is_whitelist,
            "keyword_score_adj": keyword_score_adj,
        }

    def _build_system_prompt(self, language: str = "zh") -> str:
        """构建系统 Prompt（供 BatchFilterProcessor 使用）"""
        return self.SYSTEM_PROMPT_ZH if language == "zh" else self.SYSTEM_PROMPT_EN

    def _build_user_prompt(
        self,
        title: str,
        content: str,
        url: str = "",
        source: str = "",
    ) -> str:
        """构建用户 Prompt（供 BatchFilterProcessor 使用）"""
        # 截断过长的内容
        max_content_length = 3000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...[内容已截断]..."
        return self.USER_PROMPT_TEMPLATE.format(
            title=title,
            url=url,
            source=source,
            content=content,
        )

    def _parse_filter_result(
        self,
        llm_result: dict,
        title: str,
        content: str,
        url: str = "",
        source: str = "",
    ) -> InitialFilterResult:
        """解析 LLM 结果（供 BatchFilterProcessor 使用）"""
        ignore = llm_result.get("ignore", False)
        reason = llm_result.get("reason", "")
        value = max(0, min(5, int(llm_result.get("value", 0))))
        summary = llm_result.get("summary", title or "无法分析")
        detected_language = llm_result.get("language", "zh")

        # 标准化语言代码
        if detected_language in ["中文", "Chinese", "chinese"]:
            detected_language = "zh"
        elif detected_language in ["英文", "English", "english"]:
            detected_language = "en"

        return InitialFilterResult(
            ignore=ignore,
            reason=reason,
            value=value,
            summary=summary,
            language=detected_language,
        )

    async def llm_filter(
        self,
        title: str,
        content: str,
        url: str = "",
        source: str = "",
        language: str = "zh",
    ) -> InitialFilterResult:
        """
        LLM 初评

        调用 LLM 进行内容价值评估。

        Args:
            title: 文章标题
            content: 文章内容（Markdown 格式）
            url: 文章链接
            source: 文章来源
            language: 预检测的语言（zh/en）

        Returns:
            InitialFilterResult 对象
        """
        # 根据语言选择 Prompt
        system_prompt = self.SYSTEM_PROMPT_ZH if language == "zh" else self.SYSTEM_PROMPT_EN

        # 截断过长的内容（避免 Token 超限）
        max_content_length = 8000  # 约 2000 tokens
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...[内容已截断]..."

        # 构建 User Prompt
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            title=title,
            url=url,
            source=source,
            content=content,
        )

        try:
            # 调用 LLM
            llm_response = await llm_client.call_json(
                system_prompt,
                user_prompt,
                temperature=0.3,  # 使用较低温度保证一致性
            )

            # 解析响应
            ignore = llm_response.get("ignore", False)
            reason = llm_response.get("reason", "")
            value = llm_response.get("value", 0)
            summary = llm_response.get("summary", "")
            detected_language = llm_response.get("language", language)

            # 标准化语言代码
            if detected_language in ["中文", "Chinese", "chinese"]:
                detected_language = "zh"
            elif detected_language in ["英文", "English", "english"]:
                detected_language = "en"

            # 确保 value 在有效范围内
            value = max(0, min(5, int(value)))

            return InitialFilterResult(
                ignore=ignore,
                reason=reason,
                value=value,
                summary=summary,
                language=detected_language,
            )

        except Exception as e:
            # LLM 调用失败，返回保守结果（不忽略，中等评分）
            print(f"[InitialFilter] LLM call failed: {e}")
            return InitialFilterResult(
                ignore=False,
                reason=f"LLM 调用失败，保守处理: {str(e)[:50]}",
                value=3,  # 中等评分，让后续流程决定
                summary=title if title else "无法分析",
                language=language,
            )

    async def filter(
        self,
        title: str,
        content: str,
        url: str = "",
        source: str = "",
    ) -> InitialFilterResult:
        """
        完整的初评流程（规则预筛 + LLM 初评）

        Args:
            title: 文章标题
            content: 文章内容
            url: 文章链接
            source: 文章来源

        Returns:
            InitialFilterResult 对象
        """
        # 1. 规则预筛
        rule_result = self.rule_filter(title, content, source)

        # 如果规则预筛已经给出结论，直接返回
        if rule_result["should_skip_llm"]:
            return rule_result["preliminary_result"]

        # 2. LLM 初评
        result = await self.llm_filter(
            title=title,
            content=content,
            url=url,
            source=source,
            language=rule_result["language"],
        )

        # 3. 应用规则调整
        # 白名单来源加分
        if rule_result["is_whitelist"] and not result.ignore:
            result.value = min(5, result.value + 1)

        # 关键词分数调整
        keyword_adj = rule_result["keyword_score_adj"]
        if keyword_adj != 0:
            result.value = max(0, min(5, result.value + keyword_adj))

        return result

    async def filter_batch(
        self,
        items: List[dict],
    ) -> List[InitialFilterResult]:
        """
        批量初评

        Args:
            items: 文章列表，每个 item 应包含：
                - title: 标题
                - content: 内容
                - url: 链接（可选）
                - source: 来源（可选）

        Returns:
            InitialFilterResult 列表
        """
        results = []
        for item in items:
            result = await self.filter(
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                source=item.get("source", ""),
            )
            results.append(result)
        return results


# 全局单例（可选，根据需要使用）
initial_filter = InitialFilter()
