# 完整流水线 - 多源聚合 (HN/GitHub/HF/Arxiv/ProductHunt)
# 从原 pipeline.py 文件导入（使用 importlib 避免与同名目录冲突）

import importlib.util
import os

# 加载 pipeline.py 文件（不是 pipeline/ 目录）
_pipeline_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline.py")
_spec = importlib.util.spec_from_file_location("pipeline_module", _pipeline_file)
_pipeline_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pipeline_module)

# 导出 run_full_pipeline
run_full_pipeline = _pipeline_module.run_full_pipeline

__all__ = ["run_full_pipeline"]
