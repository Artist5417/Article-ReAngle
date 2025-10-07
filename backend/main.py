from fastapi import FastAPI, UploadFile, File, Form
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
from extractors import extract_text_from_url, extract_text_from_docx, extract_text_from_pdf
from llm_free import rewrite_text

app = FastAPI(title='Article ReAngle')

# 计算前端目录的绝对路径（避免在无服务器/不同工作目录下找不到相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))

# 添加静态文件服务
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class ProcessRequest(BaseModel):
    input_text: Optional[str] = None
    url: Optional[str] = None
    style_prompt: Optional[str] = '新闻报道'
    stance_prompt: Optional[str] = None
    strength: float = 0.6

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/', response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    try:
        with open(os.path.join(FRONTEND_DIR, 'index.html'), 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Article ReAngle</h1><p>Frontend files not found. Please check the file path.</p>", status_code=404)

@app.post('/process')
async def process(
    input_text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form('改写成新闻报道风格'),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
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
            raw_text = (await file.read()).decode('utf-8', errors='ignore')

    if not raw_text.strip():
        return JSONResponse({'error': 'Empty content after extraction'}, status_code=400)

    try:
        rewritten = await rewrite_text(raw_text, prompt, api_key=api_key)

        return {
            'original': raw_text,
            'summary': raw_text,  # 不再需要单独的summary
            'rewritten': rewritten
        }
    except Exception as e:
        print(f"❌ 处理错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        return JSONResponse({'error': f'处理失败: {str(e)}'}, status_code=500)

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open('http://localhost:8000')
    print("🌐 浏览器已自动打开: http://localhost:8000")

if __name__ == '__main__':
    print("🚀 启动 Article ReAngle 洗稿程序...")
    print("📝 正在启动服务器...")
    
    # 强制设置环境变量到当前进程
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        print(f"✅ 环境变量已设置: {api_key[:20]}...")
    else:
        print("❌ 未找到环境变量 OPENAI_API_KEY")
    
    # Render/生产环境不自动打开浏览器，仅本地开发时打开
    is_production = bool(os.getenv("PORT")) or os.getenv("RENDER") == "true"
    if not is_production:
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    print("✅ 服务器启动完成！")
    if not is_production:
        print("🌐 浏览器将自动打开...")
        print("💡 如果没有自动打开，请手动访问: http://localhost:8000")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    port = int(os.getenv('PORT', '8000'))
    # 生产环境禁用 reload，多 worker 由平台管理
    uvicorn.run('main:app', host='0.0.0.0', port=port, reload=not is_production, workers=1)
