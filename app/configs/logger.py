"""
日志配置
"""

import logging
import sys
from pathlib import Path
from loguru import logger
from app.configs.settings import BASE_DIR

# 日志保存路径
LOG_DIR = Path(BASE_DIR).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


class InterceptHandler(logging.Handler):
    """
    拦截标准日志消息并将其重定向到Loguru
    """

    def emit(self, record):
        """
        发射日志记录。
        通过查找调用者的堆栈帧，尽可能获取日志发出的源代码位置。

        Args:
            record: 日志记录对象
        """
        # 获取对应的Loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到日志消息的来源
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """
    配置项目的日志系统。

    1. 拦截标准库 logging 的日志消息。
    2. 设置 Loguru 的格式和处理器（控制台和文件）。
    3. 配置 Uvicorn 和 FastAPI 的日志使用 Loguru。

    Returns:
        logger: 配置好的 Loguru logger 实例
    """
    # 拦截所有来自标准日志的消息
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    # 移除默认的loguru处理器
    logger.remove()

    # 设置默认的request_id
    logger.configure(extra={"request_id": "N/A"})

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[request_id]}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 添加文件处理器
    logger.add(
        str(LOG_FILE),
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} - {message}",
    )

    # Uvicorn日志
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    return logger
