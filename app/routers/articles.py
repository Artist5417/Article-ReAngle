"""
Article rewriting endpoints
"""

import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse

from app.services.extractors import (
    extract_text_from_url,
    extract_text_from_docx,
    extract_text_from_pdf,
)
from app.services.llms.llm import rewrite_text

router = APIRouter(
    prefix="",
    tags=["articles"],
)


@router.post("/process")
async def process_article(
    request: Request,
    input_text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form("改写成新闻报道风格"),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Process and rewrite articles from multiple sources:
    - Direct text input
    - URL extraction
    - File upload (DOCX, PDF, TXT)

    Supports multipart/form-data for legacy frontend compatibility
    """

    # Check if at least one input source is provided
    if not any([input_text, url, file]):
        return JSONResponse({"error": "No input provided"}, status_code=400)

    raw_text = ""

    # Extract text from the provided source
    if input_text:
        raw_text = input_text
    elif url:
        raw_text = await extract_text_from_url(url)
    elif file:
        if file.filename.lower().endswith(".docx"):
            raw_text = await extract_text_from_docx(file)
        elif file.filename.lower().endswith(".pdf"):
            raw_text = await extract_text_from_pdf(file)
        else:
            raw_text = (await file.read()).decode("utf-8", errors="ignore")

    if not raw_text.strip():
        return JSONResponse(
            {"error": "Empty content after extraction"}, status_code=400
        )

    # Get API key from form or environment
    try:
        provided = (api_key or "").strip()
        env_key = os.getenv("OPENAI_API_KEY", "").strip()
        final_api_key = provided or env_key

        if not final_api_key:
            return JSONResponse(
                {
                    "error": "未提供 OpenAI API Key (既没有界面输入，也没有环境变量 OPENAI_API_KEY)。"
                },
                status_code=400,
            )

        # Rewrite the text
        rewritten = await rewrite_text(raw_text, prompt, api_key=final_api_key)

        return {
            "original": raw_text,
            "summary": raw_text,
            "rewritten": rewritten,
        }

    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        return JSONResponse(
            {"error": f"处理失败: {str(e)}"},
            status_code=500,
        )
