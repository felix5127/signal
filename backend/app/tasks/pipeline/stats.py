"""
[INPUT]: 无外部依赖
[OUTPUT]: 对外提供各流水线的统计数据类
[POS]: 统一的流水线统计类定义，被 pipeline.py 和 pipeline/ 子模块共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""


class PipelineStats:
    """流水线统计数据（通用版，用于 FullPipeline）"""

    def __init__(self):
        self.scraped_count = 0
        self.filtered_count = 0
        self.generated_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class ArticlePipelineStats:
    """文章流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0          # RSS 采集数
        self.extracted_count = 0        # 全文提取成功数
        self.extraction_failed_count = 0  # 全文提取失败数
        self.filter_passed_count = 0    # 过滤通过数
        self.filter_rejected_count = 0  # 过滤拒绝数
        self.analyzed_count = 0         # 深度分析完成数
        self.translated_count = 0       # 翻译完成数
        self.saved_count = 0            # 保存成功数
        self.failed_count = 0           # 处理失败数
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class TwitterPipelineStats:
    """Twitter 流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0          # XGoing 采集数
        self.filter_passed_count = 0    # 过滤通过数
        self.filter_rejected_count = 0  # 过滤拒绝数
        self.analyzed_count = 0         # 分析完成数
        self.translated_count = 0       # 翻译完成数
        self.saved_count = 0            # 保存成功数
        self.failed_count = 0           # 处理失败数
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class PodcastPipelineStats:
    """播客流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0          # RSS 采集数
        self.transcribed_count = 0      # 转写成功数
        self.saved_count = 0            # 保存成功数
        self.failed_count = 0           # 处理失败数


class VideoPipelineStats:
    """视频流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0          # RSS 采集数
        self.transcribed_count = 0      # 转写成功数
        self.saved_count = 0            # 保存成功数
        self.failed_count = 0           # 处理失败数
