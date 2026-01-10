# Twitter 流水线
# 此文件内容从原 pipeline.py 的 run_twitter_pipeline 函数迁移

async def run_twitter_pipeline():
    """Twitter 流水线 - 实现待迁移"""
    from app.tasks.pipeline import run_twitter_pipeline as _legacy
    return await _legacy()
