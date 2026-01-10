# Models - 数据模型层

ORM 模型定义，使用 SQLAlchemy 2.0 映射数据库表结构。

## 文件清单

### v1.0 旧模型（保留兼容）
- `signal.py` - Signal 表模型，存储技术信号数据
- `digest.py` - DailyDigest/WeeklyDigest 表模型，存储日报/周报
- `run_log.py` - RunLog 表模型，记录定时任务运行日志

### v2.0 新模型
- `resource.py` - Resource 表模型，存储文章/播客/推文/视频资源（核心数据模型）
- `newsletter.py` - Newsletter 表模型，存储自动生成的周刊

### v3.0 任务管理模型（新增）
- `task.py` - **TaskStatus 表模型**，跟踪异步任务执行状态和进度
  - `task_id` - 唯一任务ID
  - `task_type` - 任务类型 (article_pipeline/twitter_pipeline/batch_llm_call)
  - `status` - 任务状态 (pending/running/completed/failed/cancelled)
  - `progress` - 进度百分比 (0-100)
  - `total_items` - 总任务数
  - `processed_items` - 已处理数
  - `failed_items` - 失败数
  - `result` - 任务结果 (JSON 格式)
  - `error` - 错误信息
  - `started_at` - 开始时间
  - `completed_at` - 完成时间
  - `metadata` - 扩展元数据 (JSON)

### 入口文件
- `__init__.py` - 统一导出所有 ORM 模型

---

**更新提醒**: 一旦本文件夹有所变化，请更新本 README.md
