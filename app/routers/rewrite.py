"""
处理洗稿请求的API路由
"""

from typing import Annotated, List, Dict, Any
from uuid import uuid4
import time
import json
from fastapi import APIRouter, Form, Request
from loguru import logger

from app.schemas.rewrite_schema import (
    RewriteRequest,
    RewriteResponse,
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
    改写文章/洗稿接口（添加到队列的多重输入）。
    """
    clean_text = ""
    # 贯穿整个请求的 request_id 与耗时统计
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    t0 = time.perf_counter()

    # 支持添加到队列的多重输入（inputs）
    form = await request.form()
    inputs_raw = rewrite_request.inputs
    if not inputs_raw:
        raise InvalidInputError(
            "inputs is required; please add items to the queue before submitting.",
            details={"request_id": request_id},
        )
    try:
        t_parse_start = time.perf_counter()
        items: List[Dict[str, Any]] = json.loads(inputs_raw)
        t_parse_end = time.perf_counter()
    except Exception as e:
        logger.error(
            "[rewrite] invalid inputs json | request_id={} | reason={}",
            request_id,
            e,
        )
        raise ContentExtractionError(
            "Invalid inputs format", details={"request_id": request_id, "reason": str(e)}
        )
    # 入参概要日志
    type_counts = {"text": 0, "url": 0, "file": 0, "youtube": 0}
    est_chars = 0
    for it in items:
        t = (it.get("type") or "").lower()
        if t in type_counts:
            type_counts[t] += 1
        if t in ("text", "url", "youtube"):
            est_chars += len((it.get("content") or ""))
    logger.info(
        "[rewrite] inputs summary | request_id={} | total={} | text={} | url={} | file={} | youtube={} | est_chars={}",
        request_id,
        len(items),
        type_counts["text"],
        type_counts["url"],
        type_counts["file"],
        type_counts["youtube"],
        est_chars,
    )
    parts: List[str] = []
    t_extract_start = time.perf_counter()
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
                logger.warning(
                    "[rewrite] url extraction failed | request_id={} | url={} | reason={}",
                    request_id,
                    url,
                    e,
                )
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
                logger.warning(
                    "[rewrite] file not found in form | request_id={} | content_key={}",
                    request_id,
                    content_key,
                )
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
                logger.error(
                    "[rewrite] file extraction failed | request_id={} | filename={} | reason={}",
                    request_id,
                    filename,
                    e,
                )
                raise ContentExtractionError(
                    f"Failed to extract content from file: {str(e)}",
                    details={"request_id": request_id, "filename": filename, "reason": str(e)},
                )
        else:
            logger.warning(f"Unknown input type: {t}")
    t_extract_end = time.perf_counter()
    t_merge_start = time.perf_counter()
    clean_text = "\n\n---\n\n".join([p for p in parts if p.strip()])
    t_merge_end = time.perf_counter()
    if not clean_text or not clean_text.strip():
        raise ContentExtractionError(
            "Extracted text is empty or invalid", details={"request_id": request_id}
        )

    # 调用rewriting_client
    try:
        prompt_len = len(rewrite_request.prompt or "")
        source_len = len(clean_text or "")
        logger.info(
            "[rewrite] llm call start | request_id={} | provider={} | prompt_len={} | source_len={}",
            request_id,
            rewrite_request.llm_type,
            prompt_len,
            source_len,
        )
        t_llm_start = time.perf_counter()
        rewritten = await rewriting_client.get_rewriting_result(
            llm_type=rewrite_request.llm_type,
            instruction=rewrite_request.prompt,
            source=clean_text,
        )
        t_llm_end = time.perf_counter()
        logger.info(
            "[rewrite] done | request_id={} | parse_ms={:.1f} | extract_ms={:.1f} | merge_ms={:.1f} | llm_ms={:.1f} | total_ms={:.1f}",
            request_id,
            (t_parse_end - t_parse_start) * 1000,
            (t_extract_end - t_extract_start) * 1000,
            (t_merge_end - t_merge_start) * 1000,
            (t_llm_end - t_llm_start) * 1000,
            (time.perf_counter() - t0) * 1000,
        )
    except Exception as e:
        logger.exception("[rewrite] llm rewriting failed | request_id={}", request_id)
        raise LLMProviderError(
            f"Failed to generate rewrite: {str(e)}",
            details={
                "request_id": request_id,
                "provider": str(rewrite_request.llm_type),
                "prompt_len": len(rewrite_request.prompt or ""),
                "source_len": len(clean_text or ""),
            },
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
