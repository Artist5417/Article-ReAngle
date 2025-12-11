"""
洗稿请求和响应的schema
"""

from enum import Enum
from pydantic import BaseModel, Field


class LLMType(str, Enum):
    """
    支持的大模型类型。
    """

    OPENAI = "gpt-5"
    GEMINI = "gemini-2.5-flash"
    QWEN = "qwen-flash"


class RewriteRequest(BaseModel):
    """
    洗稿请求模型（仅多重输入）。
    """

    llm_type: LLMType = LLMType.OPENAI
    # 前端提交的输入清单（JSON 字符串），结构：[{id,type,content?,contentKey?,meta?}, ...]
    inputs: str = Field(..., description="多源输入清单（JSON 字符串）")
    prompt: str = Field(default="改写成新闻报道风格")


class RewriteResponse(BaseModel):
    """
    洗稿响应模型。
    """

    original: str
    summary: str
    rewritten: str
