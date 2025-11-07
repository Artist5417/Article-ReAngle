"""
调用大模型的统一接口
"""

from app.schemas.rewrite_schema import LLMType
from app.services.llms import openai_client, gemini_client


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
    # 获取模型名称
    model = llm_type.value

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

    return rewritten_text
