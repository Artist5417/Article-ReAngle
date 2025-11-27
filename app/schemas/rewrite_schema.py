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
    MULTI = "multi"


class LLMType(str, Enum):
    OPENAI = "gpt-5"
    GEMINI = "gemini-2.5-flash"


class RewriteRequest(BaseModel):
    input_type: InputType
    llm_type: LLMType = LLMType.OPENAI
    input_text: str | None = None
    url: str | None = None
    file: UploadFile | None = None
    # 多源输入模式下，前端会传一个 JSON 字符串数组
    # 结构示例：[{id,type,content,contentKey,meta:{filename,size}}]
    inputs: str | None = None
    input_mode: str | None = None
    prompt: str | None = Field(default="改写成新闻报道风格")


class RewriteResponse(BaseModel):
    original: str
    summary: str
    rewritten: str
