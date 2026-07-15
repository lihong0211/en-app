from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api import users, words
from monitor import run_monitor

app = FastAPI(
    title="API",
    version="1.0.0",
    description="A complete API system with FastAPI, SQLAlchemy, and Pydantic",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def register_api():
    # 手动注册每个路由
    routers = [
        users.router,
        words.router,
    ]

    for router in routers:
        app.include_router(router)
        print(f"register_router {router.prefix} success")

register_api()

# 如果直接运行此脚本，则自动启动 mitmdump
if __name__ == "__main__":
    run_monitor()
    uvicorn.run(app, host="127.0.0.1", port=8000)
