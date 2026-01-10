# Input: InitialFilter, Analyzer, Translator, queue.py
# Output: 批量并发处理工具（优化版）
# Position: 批量处理器，将串行处理改为并发处理
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.task import TaskStatus
from app.processors.initial_filter import InitialFilter, InitialFilterResult
from app.processors.analyzer import Analyzer, AnalysisResult
from app.processors.translator import Translator
from app.tasks.queue import AsyncTaskQueue, TaskProgress, batch_llm
import logging

logger = logging.getLogger(__name__)


class BatchFilterProcessor:
    """
    批量初评处理器（并发版）

    优化点：
    - 并发执行 LLM 初评
    - 批量数据库查询（去重检查）
    - 自动重试失败任务
    """

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.initial_filter = InitialFilter()

    async def filter_batch(
        self,
        items: List[Dict[str, str]],  # [{"title", "content", "url", "source"}, ...]
        task_id: Optional[str] = None,
    ) -> List[Tuple[bool, Optional[InitialFilterResult]]]:
        """
        批量初评（并发）

        Args:
            items: 待过滤项目列表
            task_id: 任务ID

        Returns:
            List[(success, filter_result)]
        """
        # 构建 LLM 调用列表
        prompts = []
        for item in items:
            system_prompt = self.initial_filter._build_system_prompt()
            user_prompt = self.initial_filter._build_user_prompt(
                title=item.get("title", ""),
                content=item.get("content", "")[:3000],  # 截断到 3000 字符
                url=item.get("url", ""),
                source=item.get("source", ""),
            )
            prompts.append((system_prompt, user_prompt))

        # 批量调用 LLM
        llm_results = await batch_llm.process_batch_with_retry(
            prompts=prompts,
            max_retries=2,
            use_json=True,
        )

        # 解析结果
        results = []
        for (success, llm_result), item in zip(llm_results, items):
            if success:
                try:
                    # 解析 JSON + 规则过滤
                    filter_result = self.initial_filter._parse_filter_result(
                        llm_result,
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        url=item.get("url", ""),
                        source=item.get("source", ""),
                    )
                    results.append((True, filter_result))
                except Exception as e:
                    logger.error(f"[BatchFilter] Parse error: {e}")
                    results.append((False, None))
            else:
                results.append((False, None))

        return results


class BatchAnalyzerProcessor:
    """
    批量分析处理器（并发版）

    优化点：
    - 并发执行三步分析
    - 自动重试失败任务
    - 支持快速/完整分析模式
    """

    def __init__(self, max_concurrent: int = 3):  # 分析更耗时，降低并发
        self.max_concurrent = max_concurrent
        self.analyzer = Analyzer()

    async def analyze_batch(
        self,
        items: List[Dict[str, Any]],  # [{"content", "title", "source", "url", "language"}, ...]
        use_full_analysis: bool = True,
        task_id: Optional[str] = None,
    ) -> List[Tuple[bool, Optional[AnalysisResult]]]:
        """
        批量深度分析（并发）

        Args:
            items: 待分析项目列表
            use_full_analysis: 是否使用完整三步分析
            task_id: 任务ID

        Returns:
            List[(success, analysis_result)]
        """
        # 创建任务队列
        queue = AsyncTaskQueue(max_concurrent=self.max_concurrent)
        db = SessionLocal()

        try:
            # 创建任务
            if task_id is None:
                task_id = await queue.create_task(
                    task_type="batch_analysis",
                    total_items=len(items),
                )

            progress = TaskProgress(task_id, len(items), db)

            # 定义分析函数
            async def analyze_item(item: Dict[str, Any]) -> AnalysisResult:
                if use_full_analysis:
                    return await self.analyzer.full_analyze(
                        content=item["content"],
                        title=item["title"],
                        source=item.get("source", ""),
                        url=item.get("url", ""),
                        language=item.get("language", "en"),
                    )
                else:
                    return await self.analyzer.quick_analyze(
                        content=item["content"],
                        title=item["title"],
                        source=item.get("source", ""),
                        url=item.get("url", ""),
                        language=item.get("language", "en"),
                    )

            # 并发执行
            await queue.start_task(task_id)
            results = await queue.run_parallel(
                task_id=task_id,
                items=items,
                func=analyze_item,
                progress=progress,
                description="Analysis",
            )

            # 标记完成
            success_count = sum(1 for s, _ in results if s)
            await queue.complete_task(
                task_id,
                result={"analyzed": success_count, "total": len(items)},
            )

            return results

        except Exception as e:
            logger.error(f"[BatchAnalyzer] Error: {e}")
            await queue.complete_task(task_id, error=str(e))
            raise
        finally:
            db.close()


class BatchTranslatorProcessor:
    """
    批量翻译处理器（并发版）

    优化点：
    - 并发执行翻译任务
    - 支持标题/分析结果分别翻译
    """

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.translator = Translator()

    async def translate_batch(
        self,
        items: List[Dict[str, Any]],  # [{"title", "analysis_dict"}, ...]
        task_id: Optional[str] = None,
    ) -> List[Tuple[bool, Optional[Dict]]]:
        """
        批量翻译（并发）

        Args:
            items: 待翻译项目列表
            task_id: 任务ID

        Returns:
            List[(success, translated_dict)]
        """
        queue = AsyncTaskQueue(max_concurrent=self.max_concurrent)
        db = SessionLocal()

        try:
            if task_id is None:
                task_id = await queue.create_task(
                    task_type="batch_translation",
                    total_items=len(items),
                )

            progress = TaskProgress(task_id, len(items), db)

            async def translate_item(item: Dict[str, Any]) -> Dict:
                # 翻译分析结果
                translated_analysis = await self.translator.translate_analysis(
                    item["analysis_dict"]
                )

                # 翻译标题
                translated_title = await self.translator.translate_title(
                    item["title"]
                )
                translated_analysis["title_translated"] = translated_title

                return translated_analysis

            await queue.start_task(task_id)
            results = await queue.run_parallel(
                task_id=task_id,
                items=items,
                func=translate_item,
                progress=progress,
                description="Translation",
            )

            success_count = sum(1 for s, _ in results if s)
            await queue.complete_task(
                task_id,
                result={"translated": success_count, "total": len(items)},
            )

            return results

        except Exception as e:
            logger.error(f"[BatchTranslator] Error: {e}")
            await queue.complete_task(task_id, error=str(e))
            raise
        finally:
            db.close()
