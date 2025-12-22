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


class LLMResponse(BaseModel):
    """
    模型结构化输出的响应模型。
    """

    rewritten: str = Field(..., description="洗稿文章")
    summary: str = Field(..., description="洗稿概要")


class TTSRequest(BaseModel):
    """
    TTS请求模型。
    """

    text: str = Field(..., description="需要朗读的文本内容")
    model: str = Field(default="qwen3-tts-flash", description="TTS模型")
    voice: str = Field(default="Cherry", description="语音音色")


class TTSResponse(BaseModel):
    """
    TTS响应模型。
    """

    audio_url: str = Field(..., description="音频文件的URL")


class AvatarRequest(BaseModel):
    """
    数字人请求模型。
    """

    text: str = Field(..., description="数字人文本")


class AvatarResponse(BaseModel):
    """
    数字人响应模型。
    """

    video_url: str = Field(..., description="数字人视频URL")
