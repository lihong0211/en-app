import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from db import Base, get_db
from main import app

# 用内存 SQLite 跑测试，不碰真实 MySQL
# StaticPool：FastAPI 的同步依赖（如 get_db）会被丢进线程池执行，
# 默认的 SingletonThreadPool 会按线程分配连接，导致每个线程看到的是
# 互不相通的独立 :memory: 数据库（建表在主线程，查询在工作线程，从而报
# "no such table"）。StaticPool 让所有线程复用同一个连接，避免这个问题。
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
