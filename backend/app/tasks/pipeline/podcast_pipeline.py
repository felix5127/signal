# 播客流水线
# 此文件内容从原 pipeline.py 的 run_podcast_pipeline 函数迁移

async def run_podcast_pipeline():
    """播客流水线 - 实现待迁移"""
    from app.tasks.pipeline import run_twitter_pipeline as _legacy
    return await _legacy()
