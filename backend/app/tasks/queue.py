# Input: database.py, TaskStatus 模型, LLM 客户端
# Output: 异步任务队列管理器，批量并发处理工具
# Position: 异步任务执行引擎，提供并发控制和进度跟踪
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.database import SessionLocal, get_db
from app.models.task import TaskStatus
from app.utils.llm import llm_client
import logging

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar('T')
R = TypeVar('R')


class TaskProgress:
    """任务进度跟踪器"""

    def __init__(self, task_id: str, total_items: int, db: Session):
        self.task_id = task_id
        self.total_items = total_items
        self.processed_items = 0
        self.failed_items = 0
        self.db = db
        self._lock = asyncio.Lock()

    async def update(self, processed: int = 0, failed: int = 0):
        """更新进度"""
        async with self._lock:
            self.processed_items += processed
            self.failed_items += failed
            progress = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 100

            # 更新数据库
            task = self.db.query(TaskStatus).filter(TaskStatus.task_id == self.task_id).first()
            if task:
                task.processed_items = self.processed_items
                task.failed_items = self.failed_items
                task.progress = min(progress, 100.0)
                task.updated_at = datetime.now()
                self.db.commit()

    async def increment_success(self):
        """增加成功计数"""
        await self.update(processed=1)

    async def increment_failed(self):
        """增加失败计数"""
        await self.update(failed=1)


class AsyncTaskQueue:
    """
    异步任务队列管理器

    特性：
    - 并发控制（信号量限制同时执行的任务数）
    - 进度跟踪（实时更新数据库）
    - 错误处理（记录失败任务，继续处理其他任务）
    - 批量操作（批量数据库插入/更新）
    """

    def __init__(
        self,
        max_concurrent: int = 5,  # 最大并发数（避免 API 限流）
        batch_size: int = 10,  # 批量操作大小
    ):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: Dict[str, asyncio.Task] = {}

    @asynccontextmanager
    async def acquire_slot(self):
        """获取执行槽位"""
        await self.semaphore.acquire()
        try:
            yield
        finally:
            self.semaphore.release()

    async def create_task(
        self,
        task_type: str,
        total_items: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建任务记录

        Args:
            task_type: 任务类型
            total_items: 总任务数
            metadata: 元数据

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())

        db: Session = SessionLocal()
        try:
            task = TaskStatus(
                task_id=task_id,
                task_type=task_type,
                status="pending",
                total_items=total_items,
                progress=0.0,
                meta=metadata or {},
                created_at=datetime.now(),
            )
            db.add(task)
            db.commit()
            logger.info(f"[Queue] Created task {task_id} (type={task_type}, total={total_items})")
            return task_id
        finally:
            db.close()

    async def start_task(self, task_id: str):
        """标记任务开始"""
        db: Session = SessionLocal()
        try:
            task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
            if task:
                task.status = "running"
                task.started_at = datetime.now()
                db.commit()
        finally:
            db.close()

    async def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """标记任务完成"""
        db: Session = SessionLocal()
        try:
            task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
            if task:
                task.status = "completed" if not error else "failed"
                task.progress = 100.0
                task.completed_at = datetime.now()
                task.result = result
                task.error = error
                db.commit()
                logger.info(
                    f"[Queue] Task {task_id} completed: "
                    f"status={task.status}, processed={task.processed_items}, failed={task.failed_items}"
                )
        finally:
            db.close()

    async def run_parallel(
        self,
        task_id: str,
        items: List[T],
        func: Callable[[T], R],
        progress: TaskProgress,
        description: str = "Processing",
    ) -> List[Tuple[bool, Any]]:
        """
        并发执行任务列表

        Args:
            task_id: 任务ID
            items: 待处理项目列表
            func: 异步处理函数 (接收 item，返回 result)
            progress: 进度跟踪器
            description: 任务描述（用于日志）

        Returns:
            List[(success, result)]: 成功/失败标志和结果
        """
        results = []

        async def process_item(item: T, index: int) -> Tuple[bool, Any]:
            """处理单个项目"""
            async with self.acquire_slot():
                try:
                    logger.debug(f"[Queue] [{description}] {index+1}/{len(items)}: Processing...")
                    result = await func(item)
                    await progress.increment_success()
                    return (True, result)
                except Exception as e:
                    logger.error(f"[Queue] [{description}] {index+1}/{len(items)}: Error - {e}")
                    await progress.increment_failed()
                    return (False, str(e))

        # 并发执行所有任务
        tasks_list = [
            process_item(item, i)
            for i, item in enumerate(items)
        ]
        results = await asyncio.gather(*tasks_list)

        return results

    async def batch_save(
        self,
        items: List[Any],
        db: Session,
        batch_size: Optional[int] = None,
    ):
        """
        批量保存到数据库

        Args:
            items: 待保存的项目列表
            db: 数据库会话
            batch_size: 批次大小（默认使用 self.batch_size）
        """
        batch_size = batch_size or self.batch_size
        total = len(items)

        for i in range(0, total, batch_size):
            batch = items[i:i+batch_size]
            for item in batch:
                db.add(item)

            try:
                db.commit()
                logger.debug(f"[Queue] Batch saved: {i+1}-{min(i+batch_size, total)}/{total}")
            except Exception as e:
                db.rollback()
                logger.error(f"[Queue] Batch save error: {e}")
                raise


class BatchLLMProcessor:
    """
    批量 LLM 调用处理器

    特性：
    - 并发调用 LLM API（控制并发数避免超限）
    - 自动重试失败任务
    - 批量处理（提高吞吐量）
    """

    def __init__(self, max_concurrent: int = 5):
        """
        Args:
            max_concurrent: 最大并发数（根据 API 限制调整）
                - OpenAI: 推荐 5-10
                - Kimi: 推荐 3-5
                - 其他: 根据实际限流情况调整
        """
        self.max_concurrent = max_concurrent
        self.queue = AsyncTaskQueue(max_concurrent=max_concurrent)

    async def process_batch(
        self,
        prompts: List[Tuple[str, str]],  # [(system_prompt, user_prompt), ...]
        task_id: Optional[str] = None,
        progress: Optional[TaskProgress] = None,
        use_json: bool = False,
    ) -> List[Tuple[bool, Any]]:
        """
        批量处理 LLM 调用

        Args:
            prompts: 提示词列表 [(system_prompt, user_prompt), ...]
            task_id: 任务ID（可选）
            progress: 进度跟踪器（可选）
            use_json: 是否返回 JSON 格式

        Returns:
            List[(success, result)]: 成功/失败标志和结果
        """
        results = []

        async def call_llm(item: Tuple[str, str]) -> Any:
            system_prompt, user_prompt = item
            if use_json:
                return await llm_client.call_json(system_prompt, user_prompt)
            else:
                return await llm_client.call(system_prompt, user_prompt)

        # 如果没有提供 task_id 和 progress，创建临时的
        if task_id is None:
            task_id = str(uuid.uuid4())

        if progress is None:
            db = SessionLocal()
            try:
                progress = TaskProgress(task_id, len(prompts), db)
            finally:
                db.close()

        results = await self.queue.run_parallel(
            task_id=task_id,
            items=prompts,
            func=call_llm,
            progress=progress,
            description="LLM Call",
        )

        return results

    async def process_batch_with_retry(
        self,
        prompts: List[Tuple[str, str]],
        max_retries: int = 2,
        use_json: bool = False,
    ) -> List[Tuple[bool, Any]]:
        """
        批量处理 LLM 调用（带重试）

        Args:
            prompts: 提示词列表
            max_retries: 最大重试次数
            use_json: 是否返回 JSON 格式

        Returns:
            List[(success, result)]
        """
        # 初次尝试
        results = await self.process_batch(prompts, use_json=use_json)

        # 收集失败的任务
        failed_items = [
            (i, prompts[i])
            for i, (success, _) in enumerate(results)
            if not success
        ]

        # 重试失败的任务
        for retry in range(max_retries):
            if not failed_items:
                break

            logger.info(f"[BatchLLM] Retry {retry+1}/{max_retries} for {len(failed_items)} failed items")

            retry_prompts = [item for _, item in failed_items]
            retry_results = await self.process_batch(retry_prompts, use_json=use_json)

            # 更新结果
            for (idx, _), (success, result) in zip(failed_items, retry_results):
                results[idx] = (success, result)

            # 收集仍然失败的任务
            failed_items = [
                (i, prompts[i])
                for i, (success, _) in enumerate(results)
                if not success
            ]

        return results


class BatchContentExtractor:
    """
    批量内容提取处理器

    用于并发提取网页全文内容
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Args:
            max_concurrent: 最大并发数（内容提取可以更高）
        """
        self.max_concurrent = max_concurrent
        self.queue = AsyncTaskQueue(max_concurrent=max_concurrent)

    async def extract_batch(
        self,
        urls: List[str],
        content_extractor,  # ContentExtractor 实例
        task_id: Optional[str] = None,
        progress: Optional[TaskProgress] = None,
    ) -> List[Tuple[bool, Any]]:
        """
        批量提取网页内容

        Args:
            urls: URL 列表
            content_extractor: ContentExtractor 实例
            task_id: 任务ID
            progress: 进度跟踪器

        Returns:
            List[(success, ExtractedContent)]
        """
        async def extract(url: str) -> Any:
            return await content_extractor.extract(url)

        if task_id is None:
            task_id = str(uuid.uuid4())

        if progress is None:
            db = SessionLocal()
            try:
                progress = TaskProgress(task_id, len(urls), db)
            finally:
                db.close()

        results = await self.queue.run_parallel(
            task_id=task_id,
            items=urls,
            func=extract,
            progress=progress,
            description="Content Extraction",
        )

        return results


# 全局实例
default_queue = AsyncTaskQueue(max_concurrent=5)
batch_llm = BatchLLMProcessor(max_concurrent=5)
batch_extractor = BatchContentExtractor(max_concurrent=10)
