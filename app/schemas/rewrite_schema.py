"""
洗稿请求和响应的schema
"""

from enum import Enum
from fastapi import UploadFile
from pydantic import BaseModel, Field


class InputType(str, Enum):
    TEXT = "text"
    URL = "url"
    FILE = "file"


class LLMType(str, Enum):
    OPENAI = "gpt-5"
    GEMINI = "gemini-2.5-flash"
    QWEN = "qwen-flash"


class RewriteRequest(BaseModel):
    input_type: InputType
    llm_type: LLMType = LLMType.OPENAI
    input_text: str | None = None
    url: str | None = None
    file: UploadFile | None = None
    prompt: str | None = Field(default="改写成新闻报道风格")


class RewriteResponse(BaseModel):
    original: str
    summary: str
    rewritten: str
