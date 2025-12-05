from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppException
from app.schemas.error_response_schema import BaseErrorResponse


async def app_exception_handler(request: Request, exc: AppException):
    """
    处理自定义应用程序异常。
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseErrorResponse(
            success=False, error=exc.message, code=exc.code, details=exc.details
        ).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理 FastAPI 验证异常。
    """
    return JSONResponse(
        status_code=422,
        content=BaseErrorResponse(
            success=False,
            error="Validation Error",
            code="VALIDATION_ERROR",
            details={"errors": exc.errors()},
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    """
    处理未捕获的全局异常。
    """
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content=BaseErrorResponse(
            success=False,
            error="Internal Server Error",
            code="INTERNAL_ERROR",
            details={"path": str(request.url)},
        ).model_dump(),
    )
