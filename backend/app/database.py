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


def init_db():
    """
    初始化数据库，创建所有表

    在应用启动时调用一次
    """
    # 导入所有模型，确保它们被注册到 Base.metadata
    from app.models import signal  # noqa: F401
    from app.models import resource  # noqa: F401
    from app.models import source  # noqa: F401
    from app.models import prompt  # noqa: F401
    from app.models import review  # noqa: F401
    from app.models import research  # noqa: F401

    # 创建所有表 (checkfirst=True 避免重复创建错误)
    Base.metadata.create_all(bind=engine, checkfirst=True)
