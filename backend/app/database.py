# Input: 配置文件中的 database_url
# Output: SQLAlchemy 引擎、Session 依赖注入
# Position: 数据访问层，为所有 ORM 操作提供数据库连接
# 更新提醒：一旦我被更新，务必更新我的开头注释，以及所属的文件夹的 md

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import config

# ============================================
# 根据数据库类型选择不同的配置
# ============================================
is_sqlite = config.database_url.startswith("sqlite:")
is_postgresql = config.database_url.startswith("postgresql:")

if is_sqlite:
    # SQLite 配置
    engine = create_engine(
        config.database_url,
        connect_args={
            "check_same_thread": False,  # SQLite 多线程支持
            "timeout": 30,  # 增加超时时间避免锁等待
        },
        poolclass=StaticPool,  # 使用静态连接池
        echo=False,
    )
    # 启用 WAL 模式（Write-Ahead Logging），支持并发读写
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.commit()
else:
    # PostgreSQL / 其他数据库配置
    engine = create_engine(
        config.database_url,
        pool_pre_ping=True,  # 检查连接有效性
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


def get_db():
    """
    FastAPI 依赖注入函数

    使用示例：
    ```python
    @app.get("/items")
    def get_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_schema_migrations():
    """
    运行 schema 迁移 - 添加 create_all 不会添加的新列

    PostgreSQL 专用：使用 ADD COLUMN IF NOT EXISTS 安全添加缺失列
    """
    if not is_postgresql:
        return

    print("[DB] Running schema migrations...")

    # 需要添加到 resources 表的所有列（完整列表）
    resource_columns = [
        # LLM 过滤
        ("llm_score", "INTEGER"),
        ("llm_reason", "TEXT"),
        ("llm_prompt_version", "INTEGER"),
        # 人工审核
        ("review_status", "VARCHAR(20)"),
        ("review_comment", "TEXT"),
        ("reviewed_at", "TIMESTAMP"),
        ("reviewed_by", "VARCHAR(100)"),
        # 数据源关联
        ("source_id", "INTEGER"),
        # 缩略图
        ("thumbnail_url", "TEXT"),
        # 播客/视频专用
        ("audio_url", "TEXT"),
        ("duration", "INTEGER"),
        ("transcript", "TEXT"),
        ("chapters", "JSONB"),
        ("qa_pairs", "JSONB"),
        # 精选理由
        ("featured_reason", "TEXT"),
        ("featured_reason_zh", "TEXT"),
        # 时间戳
        ("analyzed_at", "TIMESTAMP"),
        # 元数据
        ("extra_metadata", "JSONB"),
    ]

    # 需要添加的索引
    resource_indexes = [
        ("idx_resources_llm_score", "llm_score"),
        ("idx_resources_source_id", "source_id"),
        ("idx_resources_review_status", "review_status"),
    ]

    with engine.connect() as conn:
        # 添加缺失的列
        for col_name, col_type in resource_columns:
            try:
                conn.execute(text(
                    f"ALTER TABLE resources ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                ))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"[DB] Warning: Failed to add column {col_name}: {e}")
                conn.rollback()

        # 加宽过窄的 varchar 列（防止 StringDataRightTruncation）
        column_widenings = [
            ("resources", "source_name", "VARCHAR(255)"),
            ("resources", "domain", "VARCHAR(100)"),
            ("resources", "subdomain", "VARCHAR(100)"),
            ("sources", "name", "VARCHAR(255)"),
        ]
        for table, col_name, col_type in column_widenings:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ALTER COLUMN {col_name} TYPE {col_type}"
                ))
                conn.commit()
            except Exception as e:
                if "does not exist" not in str(e).lower():
                    pass  # 列类型已满足要求，忽略
                conn.rollback()

        # 添加缺失的索引
        for idx_name, col_name in resource_indexes:
            try:
                conn.execute(text(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON resources({col_name})"
                ))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"[DB] Warning: Failed to create index {idx_name}: {e}")
                conn.rollback()

    print("[DB] Schema migrations completed")


def init_db():
    """
    初始化数据库，创建所有表

    在应用启动时调用一次
    """
    # 导入核心模型
    from app.models import signal  # noqa: F401
    from app.models import resource  # noqa: F401
    from app.models import source  # noqa: F401
    from app.models import prompt  # noqa: F401
    from app.models import review  # noqa: F401

    Base.metadata.create_all(bind=engine, checkfirst=True)

    # 运行 schema 迁移（添加 create_all 不会处理的新列）
    _run_schema_migrations()
