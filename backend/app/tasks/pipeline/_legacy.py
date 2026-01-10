# Input: 各种 scrapers, processors (已废弃，请使用子模块)
# Output: 数据库中的 Resource 记录 (已废弃，请使用子模块)
# Position: 向后兼容层，重定向到新的模块化流水线
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
⚠️ DEPRECATED - 此文件已废弃，请使用子模块

此文件保留用于向后兼容。所有功能已迁移到 pipeline/ 子目录：

旧导入:
    from app.tasks.pipeline import run_article_pipeline

新导入:
    from app.tasks.pipeline.article_pipeline import run_article_pipeline
    # 或
    from app.tasks.pipeline import run_article_pipeline

模块结构:
    pipeline/
    ├── __init__.py         # 统一导出
    ├── stats.py            # 统计类
    ├── article_pipeline.py # 文章流水线 ✅ 已迁移
    ├── full_pipeline.py    # 完整流水线 (待迁移)
    ├── twitter_pipeline.py # Twitter流水线 (待迁移)
    ├── podcast_pipeline.py # 播客流水线 (待迁移)
    └── video_pipeline.py   # 视频流水线 (待迁移)
"""

# 导入所有公共接口，保持向后兼容
from app.tasks.pipeline.stats import (
    PipelineStats,
    ArticlePipelineStats,
)
from app.tasks.pipeline.article_pipeline import run_article_pipeline

# 其他流水线暂时从原实现导入（待迁移）
from app.tasks.pipeline._legacy import (
    run_full_pipeline,
    TwitterPipelineStats,
    run_twitter_pipeline,
    PodcastPipelineStats,
    run_podcast_pipeline,
    VideoPipelineStats,
    run_video_pipeline,
)

__all__ = [
    "PipelineStats",
    "ArticlePipelineStats",
    "TwitterPipelineStats",
    "PodcastPipelineStats",
    "VideoPipelineStats",
    "run_article_pipeline",
    "run_full_pipeline",
    "run_twitter_pipeline",
    "run_podcast_pipeline",
    "run_video_pipeline",
]
