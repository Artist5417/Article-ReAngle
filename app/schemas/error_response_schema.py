from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class BaseErrorResponse(BaseModel):
    """
    标准错误响应模式。
    """

    success: bool = Field(default=False, description="指示失败")
    error: str = Field(..., description="错误信息")
    code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="额外的错误详情")
