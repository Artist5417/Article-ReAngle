"""
调用大模型的统一接口
"""

from loguru import logger
from app.schemas.rewrite_schema import LLMType, LLMResponse
from app.services.llms import openai_client, gemini_client, qwen_client
from app.core.exceptions import LLMProviderError


async def get_rewriting_result(
    llm_type: LLMType,
    instruction: str,
    source: str,
) -> LLMResponse:
    """
    根据用户选择模型调用对应client，并处理response结果。
    Args:
        llm_type: 模型选择
        instruction: 用户输入的洗稿方式或选择的洗稿风格预设
        source: 原始文章
    Returns:
        LLMResponse: 包含洗稿结果和摘要的对象
    """
    try:
        # 获取模型名称
        model = llm_type.value
        logger.info(
            f"Processing rewrite request with provider: {llm_type.name}, model: {model}"
        )

        # 根据模型选择调用对应client
        if llm_type == LLMType.OPENAI:
            return await openai_client.get_rewriting_result(
                instruction=instruction,
                source=source,
                model=model,
            )

        elif llm_type == LLMType.GEMINI:
            return await gemini_client.get_rewriting_result(
                instruction=instruction,
                source=source,
                model=model,
            )

        elif llm_type == LLMType.QWEN:
            return await qwen_client.get_rewriting_result(
                instruction=instruction,
                source=source,
                model=model,
            )

        raise LLMProviderError(f"Unsupported LLM type: {llm_type.name}")

    except LLMProviderError:
        raise
    except Exception as e:
        logger.exception(f"Error in rewriting client using {llm_type.name}")
        raise LLMProviderError(f"Unexpected error during rewriting: {str(e)}")
