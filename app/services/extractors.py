"""
根据不同输入源提取文本
"""

import httpx
import docx
import pypdf
import io
from bs4 import BeautifulSoup
from readability import Document
from fastapi import UploadFile
from loguru import logger

from app.core.exceptions import ContentExtractionError


async def extract_text_from_url(url: str) -> str:
    """Extract main content from URL - 采用更详细的提取逻辑"""
    try:
        logger.info(f"Starting URL extraction: {url}")

        # 确保URL有协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            logger.debug(f"URL protocol added: {url}")

        async with httpx.AsyncClient() as client:
            logger.debug("Sending HTTP request...")
            response = await client.get(url, timeout=30.0)
            logger.debug(f"HTTP response status: {response.status_code}")
            response.raise_for_status()

        logger.debug("Parsing HTML content...")
        doc = Document(response.text)
        summary = doc.summary()
        logger.debug(f"Readability summary length: {len(summary)}")

        soup = BeautifulSoup(summary, "html.parser")
        text = soup.get_text()

        # 清理文本
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result = "\n".join(lines)
        logger.info(f"Extraction complete. Length: {len(result)}")

        if not result:
            raise ContentExtractionError("Extracted text is empty")

        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during extraction: {e}")
        raise ContentExtractionError(f"Failed to download URL: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error extracting from URL: {url}")
        raise ContentExtractionError(f"Error extracting from URL: {str(e)}")


async def extract_text_from_docx(file: UploadFile) -> str:
    """Extract text from DOCX file"""
    try:
        logger.info(f"Starting DOCX extraction: {file.filename}")
        content = await file.read()
        doc = docx.Document(io.BytesIO(content))

        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        result = "\n".join(text_parts)
        logger.info(f"DOCX extraction complete. Length: {len(result)}")
        return result

    except Exception as e:
        logger.exception(f"Error extracting from DOCX: {file.filename}")
        raise ContentExtractionError(f"Error extracting from DOCX: {str(e)}")


async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text from PDF file"""
    try:
        logger.info(f"Starting PDF extraction: {file.filename}")
        content = await file.read()
        pdf_reader = pypdf.PdfReader(io.BytesIO(content))

        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text and text.strip():
                text_parts.append(text.strip())
        
        result = "\n".join(text_parts)
        logger.info(f"PDF extraction complete. Length: {len(result)}")
        return result

    except Exception as e:
        logger.exception(f"Error extracting from PDF: {file.filename}")
        raise ContentExtractionError(f"Error extracting from PDF: {str(e)}")
