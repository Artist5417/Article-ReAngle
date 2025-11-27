"""
处理洗稿请求的API路由
"""

from typing import Annotated, List, Dict, Any
import json
from fastapi import APIRouter, Form, Request
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
    InvalidInputError
)

# 设置路由前缀和标签
rewrite_router = APIRouter(prefix="/rewrite")


@rewrite_router.post("", response_model=RewriteResponse)
async def rewrite_article(request: Request, rewrite_request: Annotated[RewriteRequest, Form()]):
    clean_text = ""
    
    # 根据输入类型处理
    try:
        # 多源输入模式：inputs 为 JSON 字符串，且 input_type == multi
        if rewrite_request.input_type == InputType.MULTI or (rewrite_request.inputs and rewrite_request.inputs.strip()):
            try:
                form_data = await request.form()
                # 解析前端传来的 inputs JSON
                items: List[Dict[str, Any]] = json.loads(rewrite_request.inputs or "[]")
                parts: List[str] = []
                for it in items:
                    it_type = (it.get("type") or "").lower()
                    if it_type == "text":
                        content = it.get("content") or ""
                        if content.strip():
                            parts.append(f"[文本]\n{content.strip()}")
                    elif it_type == "url":
                        url = (it.get("content") or "").strip()
                        if url:
                            # 普通 URL 走提取
                            try:
                                extracted = await extract_text_from_url(url)
                                parts.append(f"[链接]\n源: {url}\n{extracted.strip()}")
                            except Exception as e:
                                logger.warning(f"URL extraction failed in multi mode: {e}")
                                # 退化为直接附上 URL 文本
                                parts.append(f"[链接]\n{url}")
                    elif it_type == "youtube":
                        # 先按“普通添加”处理：不做解析，仅作为原始链接
                        yt = (it.get("content") or "").strip()
                        if yt:
                            parts.append(f"[YouTube]\n{yt}")
                    elif it_type == "file":
                        # 文件通过动态字段名 file_{id} 上传
                        content_key = it.get("contentKey") or f"file_{it.get('id')}"
                        upload = form_data.get(content_key)
                        if not upload:
                            logger.warning(f"File with key {content_key} not found in form")
                            continue
                        filename = (upload.filename or "").lower()
                        try:
                            if filename.endswith(".docx"):
                                extracted = await extract_text_from_docx(upload)
                            elif filename.endswith(".pdf"):
                                extracted = await extract_text_from_pdf(upload)
                            else:
                                content = await upload.read()
                                try:
                                    extracted = content.decode("utf-8")
                                except UnicodeDecodeError:
                                    extracted = content.decode("gbk", errors="ignore")
                            parts.append(f"[文件] {filename}\n{(extracted or '').strip()}")
                        except Exception as e:
                            logger.error(f"Multi-mode file extraction failed for {filename}: {e}")
                            raise ContentExtractionError(f"Failed to extract content from file: {str(e)}")
                    else:
                        logger.warning(f"Unknown item type in multi inputs: {it_type}")
                clean_text = "\n\n---\n\n".join([p for p in parts if p.strip()])
            except Exception as e:
                logger.exception("Failed to process multi inputs")
                raise ContentExtractionError(f"Failed to process multi inputs: {str(e)}")

        elif rewrite_request.input_type == InputType.TEXT:
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
                raise ContentExtractionError(f"Failed to extract content from URL: {str(e)}")
                
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
                raise ContentExtractionError(f"Failed to extract content from file: {str(e)}")
    
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
