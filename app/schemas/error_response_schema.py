from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class BaseErrorResponse(BaseModel):
    """
    Standard error response schema.
    """
    success: bool = Field(default=False, description="Indicates failure")
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

