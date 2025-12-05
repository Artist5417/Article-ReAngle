from typing import Optional, Dict, Any


class AppException(Exception):
    """
    应用程序异常基类。
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


class ContentExtractionError(AppException):
    """
    内容提取失败时引发的异常（如 URL, PDF, DOCX 解析失败）。
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,  # Unprocessable Entity
            code="CONTENT_EXTRACTION_ERROR",
            details=details,
        )


class LLMProviderError(AppException):
    """
    LLM 提供商调用失败时引发的异常。
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,  # Bad Gateway
            code="LLM_PROVIDER_ERROR",
            details=details,
        )


class InvalidInputError(AppException):
    """
    输入验证失败时引发的异常。
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,  # Bad Request
            code="INVALID_INPUT_ERROR",
            details=details,
        )
