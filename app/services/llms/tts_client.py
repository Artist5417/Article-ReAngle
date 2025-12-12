import os
import logging
import dashscope
from app.core.exceptions import LLMProviderError

# 设置 Dashscope API 的基础 URL
dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

# 配置日志记录器
logger = logging.getLogger(__name__)


async def get_tts_result(
    text: str,
    voice: str = "Cherry",
    model: str = "qwen3-tts-flash",
) -> str:
    """
    调用阿里云 Dashscope 服务进行语音合成 (TTS)。

    Args:
        text (str): 需要转换的文本内容。
        voice (str): 语音角色 ID, 默认为 "Cherry"。
        model (str): 使用的模型名称, 默认为 "qwen3-tts-flash"。

    Returns:
        str: 生成的音频文件的 URL 地址。

    Raises:
        LLMProviderError: 当 API Key 缺失、调用失败或响应格式错误时抛出。
    """

    # 验证环境变量中是否存在 API Key
    if not os.getenv("DASHSCOPE_API_KEY"):
        logger.error("未在环境变量中找到 DASHSCOPE_API_KEY")
        raise LLMProviderError("Server configuration error: Missing Qwen API Key")

    try:
        # 记录请求开始日志
        logger.info(
            f"开始 TTS 请求 - 模型: {model}, 语音: {voice}, 文本长度: {len(text)}"
        )

        # 调用 Dashscope 的 MultiModalConversation 接口
        response = dashscope.MultiModalConversation.call(
            model=model,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            text=text,
            voice=voice,
            language_type="Chinese",
        )

        # 检查 API 响应状态码
        if response.status_code == 200:
            # 验证响应输出中是否包含音频 URL
            if (
                hasattr(response, "output")
                and hasattr(response.output, "audio")
                and hasattr(response.output.audio, "url")
            ):
                logger.info("TTS 生成成功，获取到音频 URL")
                return response.output.audio.url
            else:
                logger.error(f"TTS 响应格式错误: 缺少音频 URL。完整响应: {response}")
                raise LLMProviderError(
                    "TTS provider returned invalid response format (missing audio url)"
                )
        else:
            # 记录具体的 API 错误信息
            logger.error(
                f"TTS API 调用失败: Code={response.code}, Message={response.message}"
            )
            raise LLMProviderError(f"TTS provider error: {response.message}")

    except Exception as e:
        # 捕获并记录未预期的异常
        logger.exception("TTS 处理过程中发生未预期的错误")
        if isinstance(e, LLMProviderError):
            raise
        raise LLMProviderError(f"Unexpected error during TTS: {str(e)}")
