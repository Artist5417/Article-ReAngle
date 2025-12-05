import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件。
    记录请求的详细信息，包括请求ID、处理时间、状态码等。
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())

        # 将 request_id 绑定到日志上下文
        with logger.contextualize(request_id=request_id):
            start_time = time.time()

            # 记录请求信息
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )

            try:
                response = await call_next(request)

                process_time = (time.time() - start_time) * 1000

                # 记录响应信息
                logger.info(
                    f"Response: {response.status_code} "
                    f"Process Time: {process_time:.2f}ms"
                )

                # 添加 X-Request-ID 响应头
                response.headers["X-Request-ID"] = request_id

                return response

            except Exception as e:
                process_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Request failed: {str(e)} " f"Process Time: {process_time:.2f}ms"
                )
                raise e
