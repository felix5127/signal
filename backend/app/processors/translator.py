# Input: 英文文本 / 分析结果 dict / 英文标题
# Output: TranslationResult (原文 + 译文 + 问题列表) / 翻译后的分析结果 / 翻译后的标题
# Position: LLM 翻译层，实现三步翻译流程（初译 → 检查反思 → 意译优化）+ 标题专用翻译
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from app.utils.llm import llm_client


@dataclass
class TranslationResult:
    """
    翻译结果数据模型

    字段说明：
    - original: 原文
    - translated: 翻译后的文本
    - issues: 翻译中识别的问题列表（可选）
    """
    original: str
    translated: str
    issues: Optional[List[str]] = field(default_factory=list)


class Translator:
    """
    三步翻译器

    基于 BestBlogs 的翻译流程，实现高质量英译中：
    1. Step 1: 初次翻译 - 直接翻译，识别专业术语
    2. Step 2: 检查反思 - 审核翻译质量，识别问题
    3. Step 3: 意译优化 - 根据问题优化翻译，更符合中文表达

    翻译原则：
    - 保留专业术语英文（如 LLM, Transformer, API, GPU）
    - 技术名词翻译准确一致
    - 中文表达自然流畅
    - 保持原文风格和语气
    """

    # ===== Step 1: 初次翻译 Prompt =====
    TRANSLATE_SYSTEM_PROMPT = """# AI 翻译专家

## 任务
识别并翻译给定文本中的专业术语和内容。将英文翻译成中文。

## 翻译规则与注意事项
1. 准确翻译专业术语：
   - 按照通用使用习惯处理全称和缩写
   - 保留常用缩写，如 AI、UX、LLM、API、GPU、CPU、Transformer、Benchmark、GitHub 等
   - 技术产品名保留英文，如 Claude、GPT、React、Docker 等

2. 保持原文术语：如果术语已经是目标语言，保持不变

3. 未识别术语：对未在专业术语列表中的术语，尝试合理翻译

4. 保持风格：维持原文的语气和表达方式

5. 考虑上下文：翻译时注意整体语境，确保语义连贯

6. 格式要求：
   - 中英文之间添加空格
   - 数字与中文之间添加空格
   - 保持原文的段落结构

## 输出格式
请直接输出翻译后的中文文本，不需要额外的解释或标注。"""

    TRANSLATE_USER_PROMPT = """请将以下英文内容翻译为中文：

{text}"""

    # ===== Step 2: 检查反思 Prompt =====
    CHECK_SYSTEM_PROMPT = """# AI 翻译检查专家

## 简介
分析英译中翻译结果，识别问题，为后续优化提供指南。

## 背景
- 内容：涵盖人工智能、编程、产品、设计、商业和科技等领域的技术文章
- 翻译方向：英文翻译为中文
- 目的：将技术内容翻译为易于中文读者理解的表达
- 要求：准确传达原意，符合中文表达习惯

## 任务目标
全面检查翻译结果，识别问题，为后续意译优化提供改进方向。

## 分析要点
1. 术语与技术概念
   - 检查专业术语翻译是否准确、一致
   - 识别应保留英文但被错误翻译的术语
   - 检查技术概念的解释是否清晰

2. 语言表达与结构
   - 识别不自然或不流畅的表达
   - 检查是否存在直译导致的生硬表达
   - 评估句子结构是否符合中文习惯

3. 格式一致性
   - 检查中英文混排的空格使用
   - 检查数字与中文之间的空格
   - 验证标点符号使用是否正确

## 输出格式
以 JSON 格式输出分析结果：
{
  "issues": [
    {
      "location": "问题位置描述",
      "description": "问题描述",
      "suggestion": "改进建议"
    }
  ],
  "summary": "总体评价和主要改进方向"
}

如果翻译质量良好，没有明显问题，则 issues 为空数组。"""

    CHECK_USER_PROMPT = """请检查以下翻译结果，识别存在的问题：

## 原文（英文）：
{original}

## 翻译结果（中文）：
{translated}"""

    # ===== Step 3: 意译优化 Prompt =====
    REFINE_SYSTEM_PROMPT = """# AI 翻译优化专家

## 简介
对初次翻译的技术内容进行优化和意译，确保翻译既忠实原意又符合中文表达习惯。

## 背景
- 内容：涵盖人工智能、编程技术、产品、设计、商业、科技类的技术文章
- 初次翻译：已完成，但可能存在问题
- 翻译方向：英文翻译为中文
- 目标：提高翻译质量，使其更易于中文读者理解

## 任务目标
基于初次翻译和识别出的问题，进行重新翻译和意译，提高准确性、可读性和自然度。

## 优化要点
1. 术语与技术概念
   - 确保专业术语翻译准确且一致
   - 保留应保留的英文术语（如 LLM、API、GPU、Transformer 等）
   - 对难懂概念适当添加简短解释

2. 语言表达与结构
   - 调整句式以符合中文习惯
   - 提高表达的流畅性和自然度
   - 避免直译导致的生硬表达

3. 格式要求
   - 中英文之间添加空格
   - 数字与中文之间添加空格
   - 保持原文的段落结构

## 输出要求
1. 直接输出优化后的中文翻译
2. 准确传达原文核心意思，不遗漏关键信息
3. 保持专业性，符合技术人员阅读需求
4. 确保翻译后的内容逻辑连贯，易于理解"""

    REFINE_USER_PROMPT = """请根据以下信息，对翻译进行优化和意译：

## 原文（英文）：
{original}

## 初次翻译（中文）：
{translated}

## 翻译问题分析：
{issues}

请输出优化后的中文翻译："""

    # ===== JSON 翻译 Prompt =====
    TRANSLATE_JSON_SYSTEM_PROMPT = """# AI 翻译专家

## 任务
识别并翻译给定 JSON 文本中的专业术语和内容。将英文翻译成中文。

## 翻译规则与注意事项
1. 准确翻译专业术语：
   - 按照通用使用习惯处理全称和缩写
   - 保留常用缩写，如 AI、UX、LLM、API、GPU、CPU、Transformer、Benchmark、GitHub 等
   - 技术产品名保留英文，如 Claude、GPT、React、Docker 等

2. 保持原文术语：如果术语已经是目标语言，保持不变

3. 保持格式：维持原 JSON 结构，包括保留原有的 key 名称

4. 保持风格：维持原文的语气和表达方式

5. 格式要求：
   - 中英文之间添加空格
   - 数字与中文之间添加空格

## 输出格式
### 1. 专业术语列表
{原文术语1} -> {翻译后术语1}
{原文术语2} -> {翻译后术语2}

### 2. 翻译后的 JSON（保持原有结构和 key 名称）
[完整的翻译后 JSON]"""

    TRANSLATE_JSON_USER_PROMPT = """请根据要求识别专业术语，并对 JSON 内容进行翻译，按要求输出翻译后的中文 JSON，包括保留原有的 key 名称。

待翻译的 JSON：
```json
{json_content}
```"""

    CHECK_JSON_SYSTEM_PROMPT = """# AI 翻译检查专家

## 简介
分析 JSON 格式技术内容的英译中翻译结果，识别问题，为后续优化提供指南。

## 背景
- 内容：涵盖人工智能、编程、产品、设计、商业和科技等领域的技术文章分析结果
- 翻译方向：英文翻译为中文
- JSON 结构可能包含：title（标题）、summary（摘要）、mainPoints（主要观点）、keyQuotes（金句）等

## 任务目标
全面检查翻译结果，识别问题，为后续意译优化提供改进方向。

## 分析要点
1. 术语与技术概念
   - 检查专业术语翻译是否准确、一致
   - 识别应保留英文但被错误翻译的术语

2. 语言表达与结构
   - 识别不自然或不流畅的表达
   - 检查是否存在直译导致的生硬表达

3. 格式一致性
   - 检查中英文混排的空格使用
   - 验证 JSON 结构是否保持完整

## 输出格式
以 Markdown 格式输出问题分析，包含：
1. 问题列表（位置、描述、建议）
2. 主要问题类型总结
3. 改进方向"""

    CHECK_JSON_USER_PROMPT = """请检查以下 JSON 翻译结果，识别存在的问题：

## 原文（英文 JSON）：
```json
{original}
```

## 翻译结果（中文）：
{translated}"""

    REFINE_JSON_SYSTEM_PROMPT = """# AI 翻译优化专家

## 简介
对 JSON 格式技术内容的初次翻译进行优化和意译，确保翻译既忠实原意又符合中文表达习惯。

## 背景
- 内容：涵盖人工智能、编程技术、产品、设计、商业、科技类的技术文章分析结果
- 初次翻译：已完成，但可能存在问题
- 翻译方向：英文翻译为中文
- 目标：提高翻译质量，使其更易于中文读者理解

## 任务目标
基于初次翻译和识别出的问题，进行重新翻译和意译，提高准确性、可读性和自然度。

## 优化要点
1. 术语与技术概念
   - 确保专业术语翻译准确且一致
   - 保留应保留的英文术语（如 LLM、API、GPU、Transformer 等）

2. 语言表达与结构
   - 调整句式以符合中文习惯
   - 提高表达的流畅性和自然度
   - 避免直译导致的生硬表达

3. 格式要求
   - 中英文之间添加空格
   - 数字与中文之间添加空格
   - 保持原 JSON 结构和 key 名称不变

## 输出要求
仅输出优化后的 JSON 字符串，保持结构和原始 JSON 一致，仅将其中的值翻译为中文。
不要包含任何额外的解释文字，直接输出 JSON。"""

    REFINE_JSON_USER_PROMPT = """请根据以下信息，对 JSON 翻译进行优化和意译：

## 原文（英文 JSON）：
```json
{original}
```

## 初次翻译结果：
{translated}

## 翻译问题分析：
{issues}

请直接输出优化后的 JSON："""

    async def translate(self, text: str) -> str:
        """
        Step 1: 初次翻译

        将英文文本直接翻译为中文，识别并处理专业术语。

        Args:
            text: 待翻译的英文文本

        Returns:
            初次翻译的中文文本
        """
        if not text or not text.strip():
            return ""

        user_prompt = self.TRANSLATE_USER_PROMPT.format(text=text)

        try:
            result = await llm_client.call(
                self.TRANSLATE_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.3  # 翻译任务使用较低温度保证准确性
            )
            return result.strip()
        except Exception as e:
            print(f"[Translator] Step 1 (translate) failed: {e}")
            raise

    async def check(self, original: str, translated: str) -> Dict[str, Any]:
        """
        Step 2: 检查反思

        检查翻译质量，识别术语、表达、格式等方面的问题。

        Args:
            original: 原文（英文）
            translated: 翻译结果（中文）

        Returns:
            包含 issues 和 summary 的字典
        """
        if not original or not translated:
            return {"issues": [], "summary": "输入为空"}

        user_prompt = self.CHECK_USER_PROMPT.format(
            original=original,
            translated=translated
        )

        try:
            result = await llm_client.call_json(
                self.CHECK_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.7  # 检查任务使用较高温度以发现更多问题
            )
            return result
        except Exception as e:
            print(f"[Translator] Step 2 (check) failed: {e}")
            # 返回默认结果，继续流程
            return {"issues": [], "summary": "检查失败，将使用初次翻译结果"}

    async def refine(self, original: str, translated: str, issues: Dict[str, Any]) -> str:
        """
        Step 3: 意译优化

        根据检查结果优化翻译，使其更符合中文表达习惯。

        Args:
            original: 原文（英文）
            translated: 初次翻译结果（中文）
            issues: 检查发现的问题

        Returns:
            优化后的翻译文本
        """
        if not original or not translated:
            return translated or ""

        # 如果没有发现问题，直接返回初次翻译
        if not issues.get("issues"):
            return translated

        # 格式化问题描述
        issues_text = json.dumps(issues, ensure_ascii=False, indent=2)

        user_prompt = self.REFINE_USER_PROMPT.format(
            original=original,
            translated=translated,
            issues=issues_text
        )

        try:
            result = await llm_client.call(
                self.REFINE_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.3  # 意译使用较低温度保证质量
            )
            return result.strip()
        except Exception as e:
            print(f"[Translator] Step 3 (refine) failed: {e}")
            # 返回初次翻译结果
            return translated

    async def full_translate(self, text: str) -> TranslationResult:
        """
        完整三步翻译流程

        执行完整的三步翻译：初译 → 检查反思 → 意译优化

        Args:
            text: 待翻译的英文文本

        Returns:
            TranslationResult 对象，包含原文、译文和问题列表
        """
        if not text or not text.strip():
            return TranslationResult(original=text, translated="", issues=[])

        print(f"[Translator] Starting 3-step translation for text ({len(text)} chars)...")

        # Step 1: 初次翻译
        print("[Translator] Step 1: Initial translation...")
        translated = await self.translate(text)

        # Step 2: 检查反思
        print("[Translator] Step 2: Checking translation quality...")
        check_result = await self.check(text, translated)

        # 提取问题列表
        issues = []
        if check_result.get("issues"):
            issues = [
                f"{issue.get('location', '')}: {issue.get('description', '')}"
                for issue in check_result["issues"]
            ]

        # Step 3: 意译优化
        print("[Translator] Step 3: Refining translation...")
        final_translated = await self.refine(text, translated, check_result)

        print(f"[Translator] Translation completed. Issues found: {len(issues)}")

        return TranslationResult(
            original=text,
            translated=final_translated,
            issues=issues if issues else None
        )

    async def translate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        翻译分析结果

        专门用于翻译 LLM 分析结果（摘要、观点、金句等）。
        使用 JSON 格式的三步翻译流程。

        Args:
            analysis: 分析结果字典，可能包含：
                - oneSentenceSummary: 一句话总结
                - summary: 详细摘要
                - mainPoints: 主要观点列表
                - keyQuotes: 金句列表
                - tags: 标签列表

        Returns:
            翻译后的分析结果字典（保持相同结构）
        """
        if not analysis:
            return {}

        print(f"[Translator] Starting 3-step JSON translation...")

        # 将分析结果转为 JSON 字符串
        json_content = json.dumps(analysis, ensure_ascii=False, indent=2)

        # Step 1: 初次翻译
        print("[Translator] Step 1: Initial JSON translation...")
        user_prompt = self.TRANSLATE_JSON_USER_PROMPT.format(json_content=json_content)

        try:
            translated_raw = await llm_client.call(
                self.TRANSLATE_JSON_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.3
            )
        except Exception as e:
            print(f"[Translator] Step 1 (JSON translate) failed: {e}")
            return analysis  # 返回原文

        # Step 2: 检查反思
        print("[Translator] Step 2: Checking JSON translation quality...")
        user_prompt = self.CHECK_JSON_USER_PROMPT.format(
            original=json_content,
            translated=translated_raw
        )

        try:
            check_result = await llm_client.call(
                self.CHECK_JSON_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.7
            )
        except Exception as e:
            print(f"[Translator] Step 2 (JSON check) failed: {e}")
            check_result = "检查失败"

        # Step 3: 意译优化
        print("[Translator] Step 3: Refining JSON translation...")
        user_prompt = self.REFINE_JSON_USER_PROMPT.format(
            original=json_content,
            translated=translated_raw,
            issues=check_result
        )

        try:
            final_result = await llm_client.call_json(
                self.REFINE_JSON_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.3
            )
            print("[Translator] JSON translation completed successfully.")
            return final_result
        except Exception as e:
            print(f"[Translator] Step 3 (JSON refine) failed: {e}")
            # 尝试从初次翻译中提取 JSON
            try:
                return self._extract_json_from_text(translated_raw)
            except Exception:
                print("[Translator] Failed to extract JSON, returning original.")
                return analysis

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON

        处理 LLM 返回的可能包含 markdown 代码块的文本。

        Args:
            text: 可能包含 JSON 的文本

        Returns:
            解析后的 JSON 字典
        """
        # 尝试从 markdown 代码块中提取
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        else:
            # 尝试找到 JSON 对象
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
            else:
                json_str = text.strip()

        return json.loads(json_str)

    # ===== 标题翻译 Prompt =====
    TRANSLATE_TITLE_SYSTEM_PROMPT = """# AI 标题翻译专家

## 任务
将英文标题翻译为简洁自然的中文标题。

## 翻译规则
1. 保留专业术语英文：
   - AI、LLM、GPT、API、GPU、CPU、Transformer、Benchmark、GitHub、Docker、React、Vue、Python、JavaScript、TypeScript 等
   - 技术产品名保留英文：Claude、ChatGPT、OpenAI、Google、Microsoft、Apple 等
   - 技术缩写保留：RAG、CoT、RLHF、MoE、SOTA、SaaS、PaaS 等

2. 翻译要求：
   - 简洁：标题应简短有力，避免冗余
   - 自然：符合中文标题习惯，不是直译
   - 准确：保留原意，不添加不存在的信息

3. 格式要求：
   - 中英文之间添加空格
   - 数字与中文之间添加空格

## 输出格式
直接输出翻译后的中文标题，不需要任何解释或标注。"""

    TRANSLATE_TITLE_USER_PROMPT = """请将以下英文标题翻译为中文：

{title}"""

    async def translate_title(self, title: str) -> str:
        """
        翻译标题

        针对标题的专门翻译，使用简化的 Prompt 保证简洁自然。
        保留专业术语不翻译（如 LLM, API, GPT, Transformer 等）。

        Args:
            title: 英文标题

        Returns:
            中文标题（简洁自然）
        """
        if not title or not title.strip():
            return ""

        user_prompt = self.TRANSLATE_TITLE_USER_PROMPT.format(title=title)

        try:
            result = await llm_client.call(
                self.TRANSLATE_TITLE_SYSTEM_PROMPT,
                user_prompt,
                temperature=0.3  # 使用较低温度保证翻译质量
            )
            translated = result.strip()
            print(f"[Translator] Title translated: '{title[:50]}...' -> '{translated[:50]}...'")
            return translated
        except Exception as e:
            print(f"[Translator] Title translation failed: {e}")
            return title  # 返回原标题


# 模块级单例
translator = Translator()
