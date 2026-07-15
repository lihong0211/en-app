# db.py
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session,declarative_base

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_NAME = os.getenv('DB_NAME', 'english_new')

# 创建数据库引擎
engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_timeout=30,
    echo=True,
    pool_pre_ping=True,
)

# 创建线程安全的会话工厂
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(session_factory)

# 创建Base类
Base = declarative_base()


# 依赖注入函数（FastAPI风格）
def get_db():
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Session.remove()