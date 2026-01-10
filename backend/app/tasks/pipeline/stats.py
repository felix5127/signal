# Input: None
# Output: 统计数据类
# Position: 流水线统计类定义
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

"""
流水线统计数据类

定义各种流水线使用的统计类，用于跟踪处理进度和结果。
"""


class PipelineStats:
    """流水线统计数据（通用版）"""

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
        self.scraped_count = 0  # RSS 采集数
        self.extracted_count = 0  # 全文提取成功数
        self.extraction_failed_count = 0  # 全文提取失败数
        self.filter_passed_count = 0  # 初评通过数
        self.filter_rejected_count = 0  # 初评拒绝数
        self.analyzed_count = 0  # 深度分析完成数
        self.translated_count = 0  # 翻译完成数
        self.saved_count = 0  # 保存成功数
        self.failed_count = 0  # 处理失败数
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class TwitterPipelineStats:
    """Twitter 流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0
        self.filtered_count = 0
        self.analyzed_count = 0
        self.translated_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class PodcastPipelineStats:
    """播客流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0
        self.transcribed_count = 0
        self.transcription_failed_count = 0
        self.analyzed_count = 0
        self.translated_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0


class VideoPipelineStats:
    """视频流水线统计数据"""

    def __init__(self):
        self.scraped_count = 0
        self.transcribed_count = 0
        self.transcription_failed_count = 0
        self.analyzed_count = 0
        self.translated_count = 0
        self.saved_count = 0
        self.failed_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
