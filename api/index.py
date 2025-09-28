from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional
import requests
import os
import io
import httpx
from bs4 import BeautifulSoup
from readability import Document
import docx
import pypdf

app = FastAPI(title='Article ReAngle')

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
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
        # Use readability to extract main content
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        
        # Clean up the text
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
        
    except Exception as e:
        return f"Error extracting from URL: {str(e)}"

async def extract_text_from_docx(file: UploadFile) -> str:
    """Extract text from DOCX file"""
    try:
        content = await file.read()
        doc = docx.Document(io.BytesIO(content))
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        return '\n'.join(text_parts)
        
    except Exception as e:
        return f"Error extracting from DOCX: {str(e)}"

async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text from PDF file"""
    try:
        content = await file.read()
        pdf_reader = pypdf.PdfReader(io.BytesIO(content))
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text.strip():
                text_parts.append(text.strip())
        
        return '\n'.join(text_parts)
        
    except Exception as e:
        return f"Error extracting from PDF: {str(e)}"

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
            raw_text = await extract_text_from_url(url)
        elif file:
            if file.filename.lower().endswith('.docx'):
                raw_text = await extract_text_from_docx(file)
            elif file.filename.lower().endswith('.pdf'):
                raw_text = await extract_text_from_pdf(file)
            else:
                # 处理其他文本文件
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