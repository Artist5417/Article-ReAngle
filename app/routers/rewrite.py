"""
处理洗稿请求的API路由
"""

from typing import Annotated
from fastapi import APIRouter, Form
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

# 设置路由前缀和标签
rewrite_router = APIRouter(prefix="/rewrite")


@rewrite_router.post("", response_model=RewriteResponse)
async def rewrite_article(rewrite_request: Annotated[RewriteRequest, Form()]):
    # 根据输入类型处理
    if rewrite_request.input_type == InputType.TEXT:
        # 文本输入
        clean_text = rewrite_request.input_text
    elif rewrite_request.input_type == InputType.URL:
        # URL输入
        clean_text = await extract_text_from_url(rewrite_request.url)
    elif rewrite_request.input_type == InputType.FILE:
        # 文件上传
        user_file = rewrite_request.file
        filename = (user_file.filename or "").lower()
        # 根据文件类型处理
        if filename.endswith(".docx"):
            clean_text = await extract_text_from_docx(user_file)
        elif filename.endswith(".pdf"):
            clean_text = await extract_text_from_pdf(user_file)
        else:
            clean_text = (await user_file.read()).decode("utf-8", errors="ignore")

    # 调用rewriting_client
    rewritten = await rewriting_client.get_rewriting_result(
        llm_type=rewrite_request.llm_type,
        instruction=rewrite_request.prompt,
        source=clean_text,
    )

    # 返回响应
    return RewriteResponse(
        # 原始文本
        original=clean_text,
        # 摘要
        summary=clean_text,
        # 洗稿后的文本
        rewritten=rewritten,
    )
