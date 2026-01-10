# pytest配置文件
# 提供测试夹具（fixtures）

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models.signal import Signal
from app.models.resource import Resource


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    数据库会话夹具

    每个测试函数都会创建新的数据库
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理：删除所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    测试客户端夹具

    使用测试数据库覆盖依赖
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_signal(db: Session) -> Signal:
    """
    示例信号夹具

    创建一个测试用的信号
    """
    signal = Signal(
        source="github",
        title="Test Repository",
        url="https://github.com/test/repo",
        one_liner="A test repository",
        summary="This is a test repository for testing purposes",
        final_score=4,
        heat_score=80,
        quality_score=4,
        category="ai",
        tags="ai,machine-learning",
        status="published",
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    return signal


@pytest.fixture
def sample_signals(db: Session) -> list[Signal]:
    """
    示例信号列表夹具

    创建多个测试用的信号
    """
    signals = [
        Signal(
            source="github",
            title=f"Test Repository {i}",
            url=f"https://github.com/test/repo{i}",
            one_liner=f"A test repository {i}",
            summary=f"This is test repository {i}",
            final_score=i % 5 + 1,
            heat_score=50 + i * 10,
            quality_score=i % 5 + 1,
            category="ai" if i % 2 == 0 else "devtools",
            tags="ai,test" if i % 2 == 0 else "devtools,testing",
            status="published",
        )
        for i in range(1, 11)
    ]

    for signal in signals:
        db.add(signal)

    db.commit()

    return signals
