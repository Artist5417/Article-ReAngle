from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import requests
import os
import io

# 创建FastAPI应用
app = FastAPI(title='Article ReAngle')

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def rewrite_text_with_openai(text: str, prompt: str, api_key: str) -> str:
    """使用OpenAI API重写文本"""
    try:
        if not api_key:
            return "错误：未提供OpenAI API Key"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一个文本重写工具。用户给你一段文字和一个要求，你需要把这段文字保留关键信息的同时，按照用户输入的要求重新写一遍。'
                },
                {
                    'role': 'user',
                    'content': f'原文：{text}\n\n改写要求：{prompt}'
                }
            ],
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"OpenAI API错误: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"处理错误: {str(e)}"

@app.get('/')
async def root():
    return {"message": "Article ReAngle API is running"}

@app.get('/test')
async def test():
    return {"status": "working", "message": "Test endpoint is working"}

@app.post('/process')
async def process(
    input_text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form('改写成新闻报道风格'),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        print(f"收到处理请求 - 文本: {bool(input_text)}, URL: {bool(url)}, 文件: {bool(file)}")
        
        # 获取原始文本
        raw_text = ''
        
        if input_text:
            raw_text = input_text
            print(f"使用文本输入，长度: {len(raw_text)}")
        elif url:
            print(f"正在处理URL: {url}")
            # 简单的URL处理 - 暂时返回URL作为文本
            raw_text = f"URL内容: {url}"
            print(f"URL处理结果: {raw_text}")
        elif file:
            print(f"正在处理文件: {file.filename}")
            # 简单的文件处理 - 暂时返回文件名
            raw_text = f"文件内容: {file.filename}"
            print(f"文件处理结果: {raw_text}")
        
        if not raw_text:
            return JSONResponse({'error': '没有提供有效的输入内容'}, status_code=400)
        
        # 使用OpenAI重写文本
        print("开始调用OpenAI API...")
        rewritten = rewrite_text_with_openai(raw_text, prompt, api_key)
        print(f"重写完成，结果长度: {len(rewritten)}")
        
        return {
            'original': raw_text,
            'rewritten': rewritten,
            'summary': raw_text
        }
        
    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        return JSONResponse({'error': f'处理失败: {str(e)}'}, status_code=500)