"""
项目的API路由
"""

from fastapi import APIRouter
from .rewrite import rewrite_router
from .miniprogram import miniprogram_router

v1_routers = APIRouter(prefix="/api/v1", tags=["v1"])
v1_routers.include_router(rewrite_router)
v1_routers.include_router(miniprogram_router)
