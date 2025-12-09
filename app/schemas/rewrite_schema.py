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
    MULTI = "multi"


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
    # 多重输入模式下，前端会额外提交一个 JSON 字符串字段 inputs
    # 结构示例：[{id,type,content? ,contentKey?,meta?}]
    inputs: str | None = None
    input_mode: str | None = None
    prompt: str | None = Field(default="改写成新闻报道风格")


class RewriteResponse(BaseModel):
    """
    洗稿响应模型。
    """

    original: str
    summary: str
    rewritten: str
