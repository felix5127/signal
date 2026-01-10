# 视频流水线
# 此文件内容从原 pipeline.py 的 run_video_pipeline 函数迁移

async def run_video_pipeline():
    """视频流水线 - 实现待迁移"""
    from app.tasks.pipeline import run_video_pipeline as _legacy
    return await _legacy()
