# 完整流水线 - 多源聚合 (HN/GitHub/HF/Arxiv/ProductHunt)
# 此文件内容从原 pipeline.py 的 run_full_pipeline 函数迁移
# 由于篇幅限制，暂时作为占位符，实际实现需要从原文件提取

async def run_full_pipeline(sources=None):
    """完整流水线 - 实现待迁移"""
    from app.tasks.pipeline import run_full_pipeline as _legacy
    return await _legacy(sources)
