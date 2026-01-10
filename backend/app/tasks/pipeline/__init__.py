# Input: RawSignal 数据, 各种 scrapers, processors
# Output: 数据库中的 Resource 记录
# Position: 流水线模块，提供多种数据处理流水线
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
数据处理流水线模块

拆分后的流水线架构：
- article_pipeline: 文章 RSS 采集 → 全文提取 → 分析 → 翻译 → 存储
- full_pipeline: 多源聚合流水线 (HN/GitHub/HF/Arxiv/ProductHunt)
- twitter_pipeline: Twitter 采集流水线
- podcast_pipeline: 播客采集流水线
- video_pipeline: 视频采集流水线
"""

# 向后兼容：导出所有公共接口
from app.tasks.pipeline.stats import (
    PipelineStats,
    ArticlePipelineStats,
    TwitterPipelineStats,
    PodcastPipelineStats,
    VideoPipelineStats,
)
from app.tasks.pipeline.article_pipeline import run_article_pipeline
from app.tasks.pipeline.full_pipeline import run_full_pipeline
from app.tasks.pipeline.twitter_pipeline import run_twitter_pipeline
from app.tasks.pipeline.podcast_pipeline import run_podcast_pipeline
from app.tasks.pipeline.video_pipeline import run_video_pipeline

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
