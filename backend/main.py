from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import Optional

import uvicorn
import os
import webbrowser
import threading
import time
import sys
import uuid
import json

# ensure Python can find and import modules from the same directory as main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractors import (
    extract_text_from_url,
    extract_text_from_docx,
    extract_text_from_pdf,
)
from llm import rewrite_text, call_openai


app = FastAPI(title="Article ReAngle")

# 计算前端目录与结果目录的绝对路径（避免在无服务器/不同工作目录下找不到相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 添加静态文件服务
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRequest(BaseModel):
    input_text: Optional[str] = None
    url: Optional[str] = None
    style_prompt: Optional[str] = "新闻报道"
    stance_prompt: Optional[str] = None
    strength: float = 0.6


def extract_story_params_from_payload(payload: dict) -> dict:
    """统一解析请求 JSON 中的字段，支持顶层/keywords/default 三种位置。"""
    default_obj = payload.get("default") or {}
    keywords = payload.get("keywords") or {}
    client = payload.get("client") or {}

    text = payload.get("text") or default_obj.get("content") or ""
    json_prompt = payload.get("prompt") or ""

    title_hint = payload.get("title") or keywords.get("title") or default_obj.get("title")
    langs = payload.get("langs") or keywords.get("langs") or default_obj.get("langs")
    length = payload.get("length") or keywords.get("length") or default_obj.get("length")
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
    provided_json_key = (payload.get("api_key") or "").strip()
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    return provided_json_key or env_key


def build_story_output_body(story_obj: dict, title_hint: str | None, length: str | None, age: str | None, theme: str | None, client: dict) -> dict:
    return {
        "success": True,
        "rewritten_text": story_obj.get("rewritten_text", ""),
        "title": story_obj.get("title") or (title_hint or ""),
        "length": story_obj.get("length") or (length or ""),
        "age": story_obj.get("age") or (age or ""),
        "theme": story_obj.get("theme") or (theme or ""),
        "client": client,
    }


def write_result_file(job_id: str, data: dict) -> None:
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    try:
        with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Article ReAngle</h1><p>Frontend files not found. Please check the file path.</p>",
            status_code=404,
        )


@app.post("/process")
async def process(
    request: Request,
    input_text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form("改写成新闻报道风格"),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    多态入口：
    - application/json: 睡前故事生成（根据关键词与提示生成，并返回 jobId 与 resultUrl）
    - multipart/form-data: 兼容旧前端的洗稿流程
    """

    content_type = request.headers.get("content-type", "").lower()

    # JSON 模式：睡前故事生成
    if content_type.startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        params = extract_story_params_from_payload(payload)
        default_obj = params["default_obj"]
        keywords = params["keywords"]
        client = params["client"]
        text = params["text"]
        json_prompt = params["json_prompt"]
        title_hint = params["title_hint"]
        langs = params["langs"]
        length = params["length"]
        age = params["age"]
        theme = params["theme"]

        # API Key 兼容：允许在 JSON 中传入（不覆盖已有环境变量）
        final_api_key = get_api_key_from_payload(payload)
        if not final_api_key:
            return JSONResponse({"error": "未提供 OpenAI API Key"}, status_code=400)

        # 生成故事
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

        # 写入结果文件
        job_id = uuid.uuid4().hex
        result_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
        result_url = str(request.base_url) + f"results/{job_id}.json"

        output = {
            "success": True,
            "jobId": job_id,
            "resultUrl": result_url,
        }

        # 合并故事结果与客户端信息
        output_body = build_story_output_body(
            story_obj=story_obj,
            title_hint=title_hint,
            length=length,
            age=age,
            theme=theme,
            client=client,
        )

        try:
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(output_body, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return JSONResponse({"error": f"写入结果失败: {str(e)}"}, status_code=500)

        return output

    # 旧表单模式：继续支持
    if not any([input_text, url, file]):
        return JSONResponse({"error": "No input provided"}, status_code=400)

    raw_text = ""
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
        return JSONResponse({"error": "Empty content after extraction"}, status_code=400)

    try:
        provided = (api_key or "").strip()
        env_key = os.getenv("OPENAI_API_KEY", "").strip()
        final_api_key = provided or env_key
        if not final_api_key:
            return JSONResponse({"error": "未提供 OpenAI API Key (既没有界面输入，也没有环境变量 OPENAI_API_KEY)。"}, status_code=400)

        rewritten = await rewrite_text(raw_text, prompt, api_key=final_api_key)
        return {"original": raw_text, "summary": raw_text, "rewritten": rewritten}
    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        return JSONResponse({"error": f"处理失败: {str(e)}"}, status_code=500)


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
        "请直接返回一个JSON对象，形如：{\"title\":\"...\",\"rewritten_text\":\"...\"}"
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


@app.get("/results/{job_id}.json")
async def get_result(job_id: str):
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        return JSONResponse({"error": "Result not found"}, status_code=404)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": f"读取结果失败: {str(e)}"}, status_code=500)


@app.get("/generate")
async def generate_sample():
    """返回一个空模板，便于前端对齐字段名称与结构。"""
    return {
        "default": {
            "title": "",
            "content": "",
            "length": "",
            "age": "",
            "theme": "",
            "langs": ""
        }
    }


@app.post("/generate")
async def generate_post(request: Request):
    """接受 JSON 需求，生成故事并直接返回结果 JSON（同步）。"""
    content_type = request.headers.get("content-type", "").lower()
    if not content_type.startswith("application/json"):
        return JSONResponse({"error": "Content-Type must be application/json"}, status_code=400)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    params = extract_story_params_from_payload(payload)
    default_obj = params["default_obj"]
    keywords = params["keywords"]
    client = params["client"]
    text = params["text"]
    json_prompt = params["json_prompt"]
    title_hint = params["title_hint"]
    langs = params["langs"]
    length = params["length"]
    age = params["age"]
    theme = params["theme"]

    final_api_key = get_api_key_from_payload(payload)
    if not final_api_key:
        return JSONResponse({"error": "未提供 OpenAI API Key"}, status_code=400)

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

    # 写入结果文件（可选，便于后续GET查询）
    job_id = uuid.uuid4().hex
    result_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    try:
        write_result_file(job_id, build_story_output_body(
            story_obj=story_obj,
            title_hint=title_hint,
            length=length,
            age=age,
            theme=theme,
            client=client,
        ))
    except Exception:
        pass

    # 直接同步返回故事 JSON
    return build_story_output_body(
        story_obj=story_obj,
        title_hint=title_hint,
        length=length,
        age=age,
        theme=theme,
        client=client,
    )


def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open("http://localhost:8000")
    print("🌐 浏览器已自动打开: http://localhost:8000")


if __name__ == "__main__":
    print("启动 Article ReAngle 洗稿程序...")
    print("正在启动服务器...")

    # Render/生产环境不自动打开浏览器，仅本地开发时打开
    is_production = bool(os.getenv("PORT")) or os.getenv("RENDER") == "true"
    if not is_production:
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

    print("服务器启动完成！")
    if not is_production:
        print("浏览器将自动打开...")
        print("如果没有自动打开，请手动访问: http://localhost:8000")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)

    port = int(os.getenv("PORT", "8000"))
    # 直接传入 app 实例，避免因模块名不同导致的 'Could not import module "main"'
    uvicorn.run(app, host="0.0.0.0", port=port, reload=not is_production, workers=1)
