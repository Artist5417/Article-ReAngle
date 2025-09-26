from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional
import requests
import os

app = FastAPI(title='Article ReAngle')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/')
def read_root():
    """返回主页面"""
    try:
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
            try:
                response = requests.get(url, timeout=30)
                raw_text = response.text
            except:
                return JSONResponse({'error': 'Failed to fetch URL content'}, status_code=400)
        elif file:
            content = await file.read()
            raw_text = content.decode('utf-8', errors='ignore')

        if not raw_text.strip():
            return JSONResponse({'error': 'Empty content after extraction'}, status_code=400)

        # 调用OpenAI API重写文本
        if not api_key or api_key.strip() == "":
            return JSONResponse({'error': '未提供OpenAI API Key'}, status_code=400)

        # 调用OpenAI API
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "content": "你是一个文本重写工具。用户给你一段文字和一个要求，你需要把这段文字保留关键信息的同时，按照用户输入的要求重新写一遍。"
            },
            {
                "role": "user",
                "content": f"要求：{prompt}\n\n把下面这段文字按要求重写：\n\n{raw_text}"
            }
        ]
        
        request_data = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            rewritten = result['choices'][0]['message']['content']
        else:
            return JSONResponse({'error': f'OpenAI API错误: {response.status_code} - {response.text}'}, status_code=500)

        return {
            'original': raw_text,
            'summary': raw_text,
            'rewritten': rewritten
        }
        
    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        return JSONResponse({'error': f'处理失败: {str(e)}'}, status_code=500)

# Vercel Python runtime will look for a module-level variable named `app`