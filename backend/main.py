from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
from api import user
from db import get_db
from monitor import run_monitor

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(
    title="User Management API",
    version="1.0.0",
    description="A complete user management system with FastAPI, SQLAlchemy, and Pydantic",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


def register_api():
    # 手动注册每个路由
    routers = [
        user.router,  # 假设每个模块都有 router 实例
    ]

    for router in routers:
        app.include_router(router)
        print(f"register_router {router.prefix} success")


register_api()


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """数据库健康检查"""
    try:
        # 执行简单的数据库查询来检查连接
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# 如果直接运行此脚本，则自动启动 mitmdump
if __name__ == "__main__":
    run_monitor()
    uvicorn.run(app, host="127.0.0.1", port=8000)
