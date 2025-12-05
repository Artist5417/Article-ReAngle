"""
洗稿请求和响应的schema
"""

from enum import Enum
from fastapi import UploadFile
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """
    输入类型枚举。
    """

    TEXT = "text"
    URL = "url"
    FILE = "file"


class LLMType(str, Enum):
    """
    支持的大模型类型。
    """

    OPENAI = "gpt-5"
    GEMINI = "gemini-2.5-flash"
    QWEN = "qwen-flash"


class RewriteRequest(BaseModel):
    """
    洗稿请求模型。
    """

    input_type: InputType
    llm_type: LLMType = LLMType.OPENAI
    input_text: str | None = None
    url: str | None = None
    file: UploadFile | None = None
    prompt: str | None = Field(default="改写成新闻报道风格")


class RewriteResponse(BaseModel):
    """
    洗稿响应模型。
    """

    original: str
    summary: str
    rewritten: str
