"""
项目入口文件。
配置日志、中间件、跨域、异常处理、静态文件和路由。
"""

import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError


from app.configs.settings import STATIC_DIR
from app.routers import v1_routers
from app.configs.logger import setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.core.exceptions import AppException
from app.core.handlers import (
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)


# 初始化日志
setup_logging()

# 创建FastAPI实例
app = FastAPI(title="Article ReAngle")

# 配置中间件 (FastAPI中间件按后进先出顺序执行)
# RequestLoggingMiddleware 放在最外层(最后添加)，以便捕获所有请求
app.add_middleware(RequestLoggingMiddleware)

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 注册路由
app.include_router(v1_routers)


# API 健康检查
@app.get("/")
async def health_check():
    """
    Health Check endpoint.
    Frontend is hosted separately.
    """
    return {"status": "ok", "service": "Article ReAngle API"}


if __name__ == "__main__":
    # 通过 uvicorn 运行应用
    # 在项目根目录下执行 python -m app.main
    # 或者在根目录下运行 uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    # 不要直接运行 main.py，会找不到app包名
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
