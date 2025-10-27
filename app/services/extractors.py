"""
Text extraction services for various input sources
"""

import httpx
import docx
import pypdf
import io
from bs4 import BeautifulSoup
from readability import Document
from fastapi import UploadFile


async def extract_text_from_url(url: str) -> str:
    """Extract main content from URL - 采用更详细的提取逻辑"""
    try:
        print(f"开始提取URL内容: {url}")

        # 确保URL有协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
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

        soup = BeautifulSoup(summary, "html.parser")
        text = soup.get_text()

        # 清理文本
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result = "\n".join(lines)
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

        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())

        return "\n".join(text_parts)

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

        return "\n".join(text_parts)

    except Exception as e:
        return f"Error extracting from PDF: {str(e)}"
