"""
Vercel serverless function entry point
"""
import os
import sys
import json
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional

# Create FastAPI app
app = FastAPI(title='Article ReAngle')

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# OpenAI configuration
OPENAI_BASE_URL = "https://api.openai.com/v1"

async def call_openai(messages: list, model: str = "gpt-4o-mini", api_key: str = None) -> str:
    """使用OpenAI API"""
    # 检查API Key是否有效
    if not api_key or api_key.strip() == "":
        return "错误：未提供OpenAI API Key。请在界面中输入API Key。"
    
    # 清理API Key，移除可能的空白字符
    key_to_use = api_key.strip()
    
    try:
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"OpenAI API错误: {response.status_code} - {response.text}"
                
    except Exception as e:
        print(f"❌ 详细错误信息: {str(e)}")
        return f"OpenAI连接错误: {str(e)}"

async def rewrite_text(text: str, user_requirement: str, api_key: str = None) -> str:
    """根据用户要求改写文本"""
    messages = [
        {
            "role": "system",
            "content": "你是一个文本重写工具。用户给你一段文字和一个要求，你需要把这段文字保留关键信息的同时，按照用户输入的要求重新写一遍。"
        },
        {
            "role": "user",
            "content": f"要求：{user_requirement}\n\n把下面这段文字按要求重写：\n\n{text}"
        }
    ]
    
    return await call_openai(messages, api_key=api_key)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/', response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    try:
        # 读取前端HTML文件
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        with open(frontend_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Article ReAngle</h1><p>Frontend files not found.</p>", status_code=404)

@app.post('/process')
async def process(
    input_text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form('改写成新闻报道风格'),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """处理文本重写请求"""
    try:
        if not any([input_text, url, file]):
            return JSONResponse({'error': 'No input provided'}, status_code=400)

        raw_text = ''
        if input_text:
            raw_text = input_text
        elif url:
            # 简单的URL文本提取
            try:
                response = requests.get(url, timeout=30)
                raw_text = response.text
            except:
                return JSONResponse({'error': 'Failed to fetch URL content'}, status_code=400)
        elif file:
            # 简单的文件处理
            content = await file.read()
            raw_text = content.decode('utf-8', errors='ignore')

        if not raw_text.strip():
            return JSONResponse({'error': 'Empty content after extraction'}, status_code=400)

        # 调用OpenAI API重写文本
        rewritten = await rewrite_text(raw_text, prompt, api_key=api_key)

        return {
            'original': raw_text,
            'summary': raw_text,
            'rewritten': rewritten
        }
        
    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        return JSONResponse({'error': f'处理失败: {str(e)}'}, status_code=500)

# Vercel Python runtime will look for a module-level variable named `app`