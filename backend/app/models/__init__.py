# Input: 各子模块的 ORM 模型
# Output: 统一导出所有数据模型
# Position: models 包入口，聚合所有 ORM 模型供外部导入
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from app.models.signal import Signal
from app.models.digest import DailyDigest, WeeklyDigest
from app.models.resource import Resource
from app.models.newsletter import Newsletter
from app.models.task import TaskStatus

__all__ = [
    # v1.0 旧模型（保留兼容）
    "Signal",
    "DailyDigest",
    "WeeklyDigest",
    # v2.0 新模型
    "Resource",
    "Newsletter",
    # 任务状态模型
    "TaskStatus",
]
