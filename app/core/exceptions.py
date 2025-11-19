from typing import Optional, Dict, Any

class AppException(Exception):
    """
    Base class for application exceptions.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)

class ContentExtractionError(AppException):
    """
    Raised when content extraction fails (URL, PDF, DOCX).
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,  # Unprocessable Entity
            code="CONTENT_EXTRACTION_ERROR",
            details=details
        )

class LLMProviderError(AppException):
    """
    Raised when LLM provider (OpenAI/Gemini) fails.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,  # Bad Gateway
            code="LLM_PROVIDER_ERROR",
            details=details
        )

class InvalidInputError(AppException):
    """
    Raised when input validation fails.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,  # Bad Request
            code="INVALID_INPUT_ERROR",
            details=details
        )

