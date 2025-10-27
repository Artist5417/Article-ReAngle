"""
Results retrieval endpoints
Handles fetching stored generation results
"""

import os
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import RESULTS_DIR

router = APIRouter(
    prefix="/results",
    tags=["results"],
)


@router.get("/{job_id}.json")
async def get_result(job_id: str):
    """
    Retrieve a previously generated result by job ID
    """
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")

    if not os.path.exists(path):
        return JSONResponse({"error": "Result not found"}, status_code=404)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse(
            {"error": f"读取结果失败: {str(e)}"},
            status_code=500,
        )
