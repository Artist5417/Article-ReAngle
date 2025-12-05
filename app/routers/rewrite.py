"""
处理洗稿请求的API路由
"""

from typing import Annotated
from fastapi import APIRouter, Form
from loguru import logger

from app.schemas.rewrite_schema import (
    RewriteRequest,
    RewriteResponse,
    InputType,
)
from app.services.extractors import (
    extract_text_from_url,
    extract_text_from_docx,
    extract_text_from_pdf,
)
from app.services.llms import rewriting_client
from app.core.exceptions import (
    ContentExtractionError,
    LLMProviderError,
    InvalidInputError,
)

# 设置路由前缀和标签
rewrite_router = APIRouter(prefix="/rewrite")


@rewrite_router.post("", response_model=RewriteResponse)
async def rewrite_article(rewrite_request: Annotated[RewriteRequest, Form()]):
    """
    改写文章/洗稿接口。
    支持文本、URL、文件（DOCX/PDF）输入。
    """
    clean_text = ""

    # 根据输入类型处理
    try:
        if rewrite_request.input_type == InputType.TEXT:
            # 文本输入
            if not rewrite_request.input_text:
                raise InvalidInputError("Input text is empty")
            clean_text = rewrite_request.input_text

        elif rewrite_request.input_type == InputType.URL:
            # URL输入
            if not rewrite_request.url:
                raise InvalidInputError("URL is required")
            try:
                clean_text = await extract_text_from_url(rewrite_request.url)
            except Exception as e:
                logger.error(f"URL extraction failed: {e}")
                raise ContentExtractionError(
                    f"Failed to extract content from URL: {str(e)}"
                )

        elif rewrite_request.input_type == InputType.FILE:
            # 文件上传
            if not rewrite_request.file:
                raise InvalidInputError("File is required")

            user_file = rewrite_request.file
            filename = (user_file.filename or "").lower()

            try:
                # 根据文件类型处理
                if filename.endswith(".docx"):
                    clean_text = await extract_text_from_docx(user_file)
                elif filename.endswith(".pdf"):
                    clean_text = await extract_text_from_pdf(user_file)
                else:
                    # 默认为文本文件处理
                    content = await user_file.read()
                    try:
                        clean_text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        clean_text = content.decode("gbk", errors="ignore")
            except Exception as e:
                logger.error(f"File extraction failed for {filename}: {e}")
                raise ContentExtractionError(
                    f"Failed to extract content from file: {str(e)}"
                )

    except InvalidInputError:
        raise
    except ContentExtractionError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during content processing")
        raise ContentExtractionError(f"Error processing input: {str(e)}")

    if not clean_text or not clean_text.strip():
        raise ContentExtractionError("Extracted text is empty or invalid")

    # 调用rewriting_client
    try:
        rewritten = await rewriting_client.get_rewriting_result(
            llm_type=rewrite_request.llm_type,
            instruction=rewrite_request.prompt,
            source=clean_text,
        )
    except Exception as e:
        logger.exception("LLM rewriting failed")
        raise LLMProviderError(f"Failed to generate rewrite: {str(e)}")

    # 返回响应
    return RewriteResponse(
        # 原始文本
        original=clean_text,
        # 摘要
        summary=clean_text,
        # 洗稿后的文本
        rewritten=rewritten,
    )
