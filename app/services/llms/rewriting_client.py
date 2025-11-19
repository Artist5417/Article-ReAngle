"""
调用大模型的统一接口
"""

from loguru import logger
from app.schemas.rewrite_schema import LLMType
from app.services.llms import openai_client, gemini_client
from app.core.exceptions import LLMProviderError


async def get_rewriting_result(
    llm_type: LLMType,
    instruction: str,
    source: str,
) -> str:
    """
    根据用户选择模型调用对应client，并处理response结果

    Args:
        llm_type: 模型选择
        instruction: 用户输入的洗稿方式或选择的洗稿风格预设
        source: 原始文章

    Returns:
        从response中提取洗稿结果文本
    """
    try:
        # 获取模型名称
        model = llm_type.value
        logger.info(f"Processing rewrite request with provider: {llm_type.name}, model: {model}")

        # 根据模型选择调用对应client
        if llm_type == LLMType.OPENAI:
            response = await openai_client.get_rewriting_result(
                instruction=instruction,
                source=source,
                model=model,
            )
            # 从Response对象中提取文本
            # TODO: 后期从metadata中分析token用量等
            rewritten_text = response.output_text
            
        elif llm_type == LLMType.GEMINI:
            response = await gemini_client.get_rewriting_result(
                instruction=instruction,
                source=source,
                model=model,
            )
            # 从GenerateContentResponse对象中提取文本
            # TODO: 后期从metadata中分析token用量等
            rewritten_text = response.text
        
        if not rewritten_text:
            logger.warning(f"Provider {llm_type.name} returned empty text")
            raise LLMProviderError(f"Received empty response from {llm_type.name}")

        logger.info(f"Rewrite completed successfully. Output length: {len(rewritten_text)}")
        return rewritten_text

    except LLMProviderError:
        raise
    except Exception as e:
        logger.exception(f"Error in rewriting client using {llm_type.name}")
        raise LLMProviderError(f"Unexpected error during rewriting: {str(e)}")
