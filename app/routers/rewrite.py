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
    InvalidInputError,
)

# 设置路由前缀和标签
rewrite_router = APIRouter(prefix="/rewrite")


@rewrite_router.post("", response_model=RewriteResponse)
async def rewrite_article(request: Request, rewrite_request: Annotated[RewriteRequest, Form()]):
    """
    改写文章/洗稿接口。
    支持文本、URL、文件（DOCX/PDF）输入。
    """
    clean_text = ""

    # 优先处理多重输入（inputs），其余作为回退
    try:
        form = await request.form()
        inputs_raw = form.get("inputs")
        if inputs_raw:
            items: List[Dict[str, Any]] = json.loads(inputs_raw)
            parts: List[str] = []
            for it in items:
                t = (it.get("type") or "").lower()
                if t == "text":
                    content = (it.get("content") or "").strip()
                    if content:
                        parts.append(f"[文本]\n{content}")
                elif t == "url":
                    url = (it.get("content") or "").strip()
                    if not url:
                        continue
                    try:
                        extracted = await extract_text_from_url(url)
                        parts.append(f"[链接]\n源: {url}\n{extracted.strip()}")
                    except Exception as e:
                        logger.warning(f"URL extraction failed in multi mode: {e}")
                        parts.append(f"[链接]\n{url}")
                elif t == "youtube":
                    yt = (it.get("content") or "").strip()
                    if yt:
                        parts.append(f"[YouTube]\n{yt}")
                elif t == "file":
                    content_key = it.get("contentKey")
                    if not content_key:
                        continue
                    upload = form.get(content_key)
                    if not upload:
                        logger.warning(f"File not found in form: {content_key}")
                        continue
                    filename = (getattr(upload, "filename", "") or "").lower()
                    try:
                        if filename.endswith(".docx"):
                            extracted = await extract_text_from_docx(upload)
                        elif filename.endswith(".pdf"):
                            extracted = await extract_text_from_pdf(upload)
                        else:
                            raw = await upload.read()
                            try:
                                extracted = raw.decode("utf-8")
                            except UnicodeDecodeError:
                                extracted = raw.decode("gbk", errors="ignore")
                        parts.append(f"[文件] {filename}\n{(extracted or '').strip()}")
                    except Exception as e:
                        logger.error(f"Multi file extraction failed for {filename}: {e}")
                        raise ContentExtractionError(f"Failed to extract content from file: {str(e)}")
                else:
                    logger.warning(f"Unknown input type: {t}")
            clean_text = "\n\n---\n\n".join([p for p in parts if p.strip()])
    except Exception as e:
        logger.exception("Multi-input processing failed")

    # 回退到旧的单源分支
    if not clean_text:
        try:
            if rewrite_request.input_type == InputType.TEXT:
                if not rewrite_request.input_text:
                    raise InvalidInputError("Input text is empty")
                clean_text = rewrite_request.input_text

            elif rewrite_request.input_type == InputType.URL:
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
                if not rewrite_request.file:
                    raise InvalidInputError("File is required")

                user_file = rewrite_request.file
                filename = (user_file.filename or "").lower()

                try:
                    if filename.endswith(".docx"):
                        clean_text = await extract_text_from_docx(user_file)
                    elif filename.endswith(".pdf"):
                        clean_text = await extract_text_from_pdf(user_file)
                    else:
                        content = await user_file.read()
                        try:
                            clean_text = content.decode("utf-8")
                        except UnicodeDecodeError:
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
