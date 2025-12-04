"""
使用Qwen洗稿，通过OpenAI SDK调用
"""

import os
import yaml
from openai import OpenAI
from loguru import logger

from app.configs.settings import SYSTEM_PROMPTS_DIR
from app.core.exceptions import LLMProviderError


async def get_rewriting_result(
    instruction: str,
    source: str,
    model: str = "qwen-flash",
):
    """
    调用OpenAI Completions API洗稿

    Args:
        instruction: 用户输入的洗稿方式或选择的洗稿风格预设
        source: 原始文章
        model: 模型选择，默认为qwen-flash

    Returns:
        OpenAI Completion对象
    """
    try:
        logger.info(f"Calling Qwen API (model: {model})")

        # 从yaml文件中加载system prompt
        prompt_file = os.path.join(SYSTEM_PROMPTS_DIR, "qwen_system_prompt.yaml")

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_data = yaml.safe_load(f)
                system_prompt = prompt_data.get("system_prompt", "")
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            raise LLMProviderError(
                f"Configuration error: Failed to load system prompt: {str(e)}"
            )

        if not os.getenv("DASHSCOPE_API_KEY"):
            logger.error("DASHSCOPE_API_KEY not found in environment")
            raise LLMProviderError("Server configuration error: Missing Qwen API Key")

        # 初始化OpenAI client，此处需要从环境变量中获取‘DASHSCOPE_API_KEY’，并设定Qwen新加坡baseURL
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

        logger.debug("Sending request to Qwen...")
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    # system prompt
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    # instruction
                    "role": "user",
                    "content": instruction,
                },
                {
                    # source
                    "role": "user",
                    "content": source,
                },
            ],
        )
        logger.info("Qwen API request successful")
        return completion

    except Exception as e:
        logger.exception("Qwen API call failed")
        raise LLMProviderError(f"Qwen API error: {str(e)}")
