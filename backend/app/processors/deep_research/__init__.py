# Input: Signal对象
# Output: 深度研究报告 (ResearchResult)
# Position: Deep Research核心模块,支持V1轻量级和V2完整Multi-Agent

from .base import BaseResearchEngine, ResearchResult, BaseSearchProvider
from .v1_lightweight import LightweightResearchEngine

__all__ = [
    "BaseResearchEngine",
    "ResearchResult",
    "BaseSearchProvider",
    "LightweightResearchEngine",
]
