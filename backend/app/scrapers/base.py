# Input: config.py (配置参数)
# Output: RawSignal 数据模型
# Position: 爬虫基类，定义统一接口和重试逻辑
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential


class RawSignal(BaseModel):
    """
    原始信号数据模型（爬虫输出）

    字段说明：
    - source: 数据来源
    - source_id: 原始平台 ID
    - url: 原文链接
    - title: 标题
    - content: 原始内容（可选）
    - source_created_at: 原始发布时间
    - metadata: 额外元数据（如 HN score, GitHub stars 等）
    """

    source: str  # 'hn' | 'github' | 'huggingface'
    source_id: Optional[str] = None
    url: str
    title: str
    content: Optional[str] = None
    source_created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class BaseScraper(ABC):
    """
    爬虫抽象基类

    所有爬虫都应继承此类并实现 scrape() 方法

    特性：
    - 统一的错误处理和重试逻辑
    - 标准化的数据输出格式（RawSignal）
    - Rate limiting 支持
    """

    def __init__(self, source_name: str):
        """
        初始化爬虫

        Args:
            source_name: 数据源名称 ('hn' | 'github' | 'huggingface')
        """
        self.source_name = source_name

    @retry(
        stop=stop_after_attempt(3),  # 最多重试 3 次
        wait=wait_exponential(multiplier=1, min=1, max=4),  # 指数退避：1s, 2s, 4s
        reraise=True,  # 重试失败后抛出原始异常
    )
    async def fetch_with_retry(self, fetch_func, *args, **kwargs):
        """
        带重试的 HTTP 请求

        Args:
            fetch_func: 请求函数
            *args, **kwargs: 传递给请求函数的参数

        Returns:
            请求结果
        """
        return await fetch_func(*args, **kwargs)

    @abstractmethod
    async def scrape(self) -> List[RawSignal]:
        """
        抓取数据（子类必须实现）

        Returns:
            RawSignal 列表
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}(source={self.source_name})>"
