"""
[INPUT]: 依赖 models/resource 的 Resource, models/task 的 TaskStatus, services/deep_research_service 的 DeepResearchService
[OUTPUT]: 对外提供 run_resource_deep_research, run_signal_deep_research
[POS]: 后台任务处理器，供 FastAPI BackgroundTasks 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import asyncio
from datetime import datetime


def run_resource_deep_research(resource_id: int, task_id: str, strategy: str = "lightweight"):
    """
    Resources Deep Research 后台任务处理器

    供 FastAPI BackgroundTasks 调用，在后台异步生成资源深度研究报告
    支持任务状态跟踪和进度更新

    Args:
        resource_id: 资源ID
        task_id: 任务ID（用于更新 TaskStatus）
        strategy: 研究策略 (lightweight/auto)
    """
    from app.database import SessionLocal
    from app.models.resource import Resource
    from app.models.task import TaskStatus
    from app.services.deep_research_service import DeepResearchService, ResearchStrategy

    db = SessionLocal()
    try:
        # 获取任务记录
        task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
        if not task:
            print(f"[DeepResearch] Task {task_id} not found")
            return

        # 获取资源对象
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            print(f"[DeepResearch] Resource {resource_id} not found")
            task.status = "failed"
            task.error = f"Resource {resource_id} not found"
            db.commit()
            return

        # 更新任务状态为运行中
        task.status = "running"
        task.started_at = datetime.now()
        task.progress = 0
        task.logs = [{"step": "正在初始化研究引擎...", "time": datetime.now().isoformat()}]
        db.commit()

        # 进度回调函数
        def update_progress(progress: float, step: str):
            task.progress = progress
            task.logs = task.logs or []
            task.logs.append({"step": step, "time": datetime.now().isoformat()})
            db.commit()

        # 解析策略
        try:
            research_strategy = ResearchStrategy(strategy)
        except ValueError:
            print(f"[DeepResearch] Unknown strategy '{strategy}', using 'lightweight'")
            research_strategy = ResearchStrategy.LIGHTWEIGHT

        # 创建新事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            service = DeepResearchService()
            service.engines[research_strategy].set_progress_callback(update_progress)

            result = loop.run_until_complete(
                service.generate_research(resource, strategy=research_strategy)
            )

            # 更新任务为成功状态
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            task.result = {
                "content": result.content,
                "sources": result.sources,
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
            }
            task.logs = (task.logs or []) + [{"step": "研究完成！", "time": datetime.now().isoformat()}]
            db.commit()

            print(
                f"[DeepResearch] Completed for resource {resource_id} "
                f"(tokens: {result.tokens_used}, cost: ${result.cost_usd:.4f})"
            )
        finally:
            loop.close()

    except Exception as e:
        print(f"[DeepResearch] Error for resource {resource_id}: {e}")
        # 更新任务为失败状态
        if task:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            db.commit()
    finally:
        db.close()


def run_signal_deep_research(signal_id: int, strategy: str = "lightweight"):
    """
    Signal Deep Research 后台任务处理器 (Legacy)

    供 FastAPI BackgroundTasks 调用，在后台异步生成深度研究报告

    Args:
        signal_id: 信号ID
        strategy: 研究策略 (lightweight/auto)
    """
    from app.database import SessionLocal
    from app.models.signal import Signal
    from app.services.deep_research_service import DeepResearchService, ResearchStrategy

    db = SessionLocal()
    try:
        # 获取信号对象
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            print(f"[DeepResearch] Signal {signal_id} not found")
            return

        # 解析策略
        try:
            research_strategy = ResearchStrategy(strategy)
        except ValueError:
            print(f"[DeepResearch] Unknown strategy '{strategy}', using 'lightweight'")
            research_strategy = ResearchStrategy.LIGHTWEIGHT

        # 创建新事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            service = DeepResearchService()
            result = loop.run_until_complete(
                service.generate_research(signal, strategy=research_strategy)
            )

            print(
                f"[DeepResearch] Completed for signal {signal_id} "
                f"(tokens: {result.tokens_used}, cost: ${result.cost_usd:.4f})"
            )
        finally:
            loop.close()

    except Exception as e:
        print(f"[DeepResearch] Error for signal {signal_id}: {e}")
    finally:
        db.close()
