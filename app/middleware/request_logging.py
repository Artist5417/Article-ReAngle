import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        
        # Bind request_id to the logger context
        with logger.contextualize(request_id=request_id):
            start_time = time.time()
            
            # Log request
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )
            
            try:
                response = await call_next(request)
                
                process_time = (time.time() - start_time) * 1000
                
                # Log response
                logger.info(
                    f"Response: {response.status_code} "
                    f"Process Time: {process_time:.2f}ms"
                )
                
                # Add X-Request-ID header to response
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                process_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Request failed: {str(e)} "
                    f"Process Time: {process_time:.2f}ms"
                )
                raise e

