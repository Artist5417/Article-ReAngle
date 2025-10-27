"""
Bedtime story generation endpoints
Handles JSON-based story generation with structured output
"""

import json
import uuid
import os
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.configs.settings import RESULTS_DIR
from app.services.llms.llm import call_openai

router = APIRouter(
    prefix="/generate",
    tags=["stories"],
)


# Helper functions for story parameter processing
def extract_story_params_from_payload(payload: dict) -> dict:
    """统一解析请求 JSON 中的字段，支持顶层/keywords/default 三种位置。"""
    default_obj = payload.get("default") or {}
    keywords = payload.get("keywords") or {}
    client = payload.get("client") or {}

    text = payload.get("text") or default_obj.get("content") or ""
    json_prompt = payload.get("prompt") or ""

    title_hint = (
        payload.get("title") or keywords.get("title") or default_obj.get("title")
    )
    langs = payload.get("langs") or keywords.get("langs") or default_obj.get("langs")
    length = (
        payload.get("length") or keywords.get("length") or default_obj.get("length")
    )
    age = payload.get("age") or keywords.get("age") or default_obj.get("age")
    theme = payload.get("theme") or keywords.get("theme") or default_obj.get("theme")

    return {
        "default_obj": default_obj,
        "keywords": keywords,
        "client": client,
        "text": text,
        "json_prompt": json_prompt,
        "title_hint": title_hint,
        "langs": langs,
        "length": length,
        "age": age,
        "theme": theme,
    }


def get_api_key_from_payload(payload: dict) -> str:
    """Extract API key from payload or environment variable"""
    provided_json_key = (payload.get("api_key") or "").strip()
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    return provided_json_key or env_key


def build_story_output_body(
    story_obj: dict,
    title_hint: str | None,
    length: str | None,
    age: str | None,
    theme: str | None,
    client: dict,
) -> dict:
    """Build standardized story output response"""
    return {
        "success": True,
        "rewritten_text": story_obj.get("rewritten_text", ""),
        "title": story_obj.get("title") or (title_hint or ""),
        "length": story_obj.get("length") or (length or ""),
        "age": story_obj.get("age") or (age or ""),
        "theme": story_obj.get("theme") or (theme or ""),
        "client": client,
    }


async def generate_story(
    keywords: dict,
    user_prompt: Optional[str],
    base_text: Optional[str],
    length: Optional[str],
    age: Optional[str],
    theme: Optional[str],
    title_hint: Optional[str],
    langs: Optional[str],
    api_key: Optional[str],
) -> dict:
    """调用 LLM 生成睡前故事，并尽量返回结构化信息。"""
    material = (
        keywords.get("material")
        or keywords.get("内容")
        or keywords.get("topic")
        or "动物友谊"
    )
    requirement = (
        keywords.get("requirement")
        or keywords.get("备注")
        or keywords.get("style")
        or "幼儿可理解、温柔、安全入睡"
    )

    sys_prompt = (
        "你是一名睡前故事创作者。请用自然、温暖、安全的中文写一个睡前故事。\n"
        "如果提供了语言(langs)，请使用对应语言；默认中文。\n"
        "若提供了标题提示(title_hint)，可据此拟定更贴切的标题。\n"
        "面向年龄段：{age}；主题：{theme}；篇幅：{length}。\n"
        "务必返回JSON，字段：title（标题）、rewritten_text（正文）。"
    ).format(
        age=age or "",
        theme=theme or material or "",
        length=length or "",
    )

    user_content = (
        "【素材】{material}\n"
        "【需求】{requirement}\n"
        "【标题提示】{title_hint}\n"
        "【语言】{langs}\n"
        "【附加提示】{extra}\n"
        "【可选原文】{base_text}\n"
        '请直接返回一个JSON对象，形如：{"title":"...","rewritten_text":"..."}'
    ).format(
        material=material or "",
        requirement=requirement or "",
        title_hint=title_hint or "",
        langs=langs or "",
        extra=(user_prompt or ""),
        base_text=(base_text or ""),
    )

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content},
    ]

    content = await call_openai(messages, api_key=api_key)

    # 优先解析为JSON
    try:
        data = json.loads(content)
        title = str(data.get("title") or (title_hint or "")).strip()
        body = str(data.get("rewritten_text") or data.get("content") or content).strip()
    except Exception:
        # 回退：将LLM输出作为正文
        title = (title_hint or "").strip()
        body = str(content).strip()

    return {
        "title": title.strip(),
        "rewritten_text": body.strip(),
        "length": length or "",
        "age": age or "",
        "theme": theme or material or "",
    }


def write_result_file(job_id: str, data: dict) -> None:
    """Write result data to file"""
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("")
async def generate_sample():
    """返回一个空模板，便于前端对齐字段名称与结构。"""
    return {
        "default": {
            "title": "",
            "content": "",
            "length": "",
            "age": "",
            "theme": "",
            "langs": "",
        }
    }


@router.post("")
async def generate_story_post(request: Request):
    """
    Generate bedtime story based on JSON request
    Returns story content directly (synchronous response)
    """
    content_type = request.headers.get("content-type", "").lower()
    if not content_type.startswith("application/json"):
        return JSONResponse(
            {"error": "Content-Type must be application/json"},
            status_code=400,
        )

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    # Extract parameters from payload
    params = extract_story_params_from_payload(payload)
    keywords = params["keywords"]
    client = params["client"]
    text = params["text"]
    json_prompt = params["json_prompt"]
    title_hint = params["title_hint"]
    langs = params["langs"]
    length = params["length"]
    age = params["age"]
    theme = params["theme"]

    # Get API key
    final_api_key = get_api_key_from_payload(payload)
    if not final_api_key:
        return JSONResponse({"error": "未提供 OpenAI API Key"}, status_code=400)

    # Generate story
    try:
        story_obj = await generate_story(
            keywords=keywords,
            user_prompt=json_prompt,
            base_text=text,
            length=length,
            age=age,
            theme=theme,
            title_hint=title_hint,
            langs=langs,
            api_key=final_api_key,
        )
    except Exception as e:
        return JSONResponse({"error": f"生成失败: {str(e)}"}, status_code=500)

    # Write result file (optional, for later GET queries)
    job_id = uuid.uuid4().hex
    try:
        write_result_file(
            job_id,
            build_story_output_body(
                story_obj=story_obj,
                title_hint=title_hint,
                length=length,
                age=age,
                theme=theme,
                client=client,
            ),
        )
    except Exception:
        pass

    # Return story directly
    return build_story_output_body(
        story_obj=story_obj,
        title_hint=title_hint,
        length=length,
        age=age,
        theme=theme,
        client=client,
    )
