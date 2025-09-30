from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import requests
import os
import io
import httpx
from bs4 import BeautifulSoup
from readability import Document
import docx
import pypdf

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

async def extract_text_from_url(url: str) -> str:
    """Extract main content from URL"""
    try:
        print(f"开始提取URL内容: {url}")
        
        # 确保URL有协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"添加协议后的URL: {url}")
        
        async with httpx.AsyncClient() as client:
            print("发送HTTP请求...")
            response = await client.get(url, timeout=30.0)
            print(f"HTTP响应状态: {response.status_code}")
            response.raise_for_status()
        
        print("开始解析HTML内容...")
        doc = Document(response.text)
        summary = doc.summary()
        print(f"Readability提取的摘要长度: {len(summary)}")
        
        soup = BeautifulSoup(summary, 'html.parser')
        text = soup.get_text()
        
        # 清理文本
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        result = '\n'.join(lines)
        print(f"最终提取的文本长度: {len(result)}")
        
        return result
        
    except Exception as e:
        print(f"URL提取错误: {str(e)}")
        return f"Error extracting from URL: {str(e)}"

async def extract_text_from_docx(file: UploadFile) -> str:
    """Extract text from DOCX file"""
    try:
        content = await file.read()
        doc = docx.Document(io.BytesIO(content))
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        return f"Error extracting from DOCX: {str(e)}"

async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text from PDF file"""
    try:
        content = await file.read()
        pdf_reader = pypdf.PdfReader(io.BytesIO(content))
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        return '\n'.join(text)
    except Exception as e:
        return f"Error extracting from PDF: {str(e)}"

def rewrite_text_with_openai(text: str, prompt: str, api_key: str) -> str:
    """使用OpenAI API重写文本"""
    try:
        if not api_key:
            return "错误：未提供OpenAI API Key"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 根据原文长度动态设置max_tokens
        text_length = len(text)
        max_tokens = max(4000, int(text_length * 1.5))  # 至少4000，或原文长度的1.5倍
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一个专业的文本重写工具。你的任务是：1. 保持原文的详细程度和长度 2. 保留所有重要信息和细节 3. 按照用户要求改变表达方式和观点 4. 确保重写后的文章长度与原文相近。请完整重写，不要省略内容。'
                },
                {
                    'role': 'user',
                    'content': f'请重写以下文章，要求：{prompt}\n\n原文：\n{text}\n\n请保持原文的详细程度和长度，完整重写：'
                }
            ],
            'max_tokens': max_tokens,
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
            raw_text = await extract_text_from_url(url)
            print(f"URL提取结果长度: {len(raw_text)}")
            print(f"URL提取结果前100字符: {raw_text[:100]}")
        elif file:
            print(f"正在处理文件: {file.filename}")
            if file.filename.lower().endswith('.docx'):
                raw_text = await extract_text_from_docx(file)
            elif file.filename.lower().endswith('.pdf'):
                raw_text = await extract_text_from_pdf(file)
            else:  # 处理TXT和其他文本文件
                content = await file.read()
                raw_text = content.decode('utf-8', errors='ignore')
            print(f"文件提取结果长度: {len(raw_text)}")
        
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