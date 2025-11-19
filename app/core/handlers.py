from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppException
from app.schemas.error_response_schema import BaseErrorResponse

async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle custom application exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseErrorResponse(
            success=False,
            error=exc.message,
            code=exc.code,
            details=exc.details
        ).model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle FastAPI validation exceptions.
    """
    return JSONResponse(
        status_code=422,
        content=BaseErrorResponse(
            success=False,
            error="Validation Error",
            code="VALIDATION_ERROR",
            details={"errors": exc.errors()}
        ).model_dump()
    )

async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled exceptions.
    """
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content=BaseErrorResponse(
            success=False,
            error="Internal Server Error",
            code="INTERNAL_ERROR",
            details={"path": str(request.url)}
        ).model_dump()
    )

