"""
调用OpenAI API洗稿
"""

import os
import yaml
from openai import OpenAI
from loguru import logger

from app.configs.settings import SYSTEMZ_PROMPTS_DIR
from app.core.exceptions import LLMProviderError


async def get_rewriting_result(
    instruction: str,
    source: str,
    model: str = "gpt-5",
):
    """
    调用OpenAI Responses API洗稿

    Args:
        instruction: 用户输入的洗稿方式或选择的洗稿风格预设
        source: 原始文章
        model: 模型选择，默认为gpt-5

    Returns:
        OpenAI Response对象
    """
    try:
        logger.info(f"Calling OpenAI API (model: {model})")
        
        # 从yaml文件中加载system prompt
        prompt_file = os.path.join(SYSTEMZ_PROMPTS_DIR, "openai_system_prompt.yaml")

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_data = yaml.safe_load(f)
                system_prompt = prompt_data.get("system_prompt", "")
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            # Use a fallback or re-raise? Raising seems safer.
            raise LLMProviderError(f"Configuration error: Failed to load system prompt: {str(e)}")

        # 初始化OpenAI client，此处会自动获取环境变量中的“OPENAI_API_KEY”
        # Note: OpenAI client initialization usually doesn't make network calls, but checking key existence is good.
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment")
            raise LLMProviderError("Server configuration error: Missing OpenAI API Key")

        client = OpenAI()

        # 通过Responses创建任务，获取response对象
        logger.debug("Sending request to OpenAI...")
        response = client.responses.create(
            model=model,
            input=[
                {
                    # system prompt
                    "role": "developer",
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
        logger.info("OpenAI API request successful")
        return response

    except Exception as e:
        logger.exception("OpenAI API call failed")
        raise LLMProviderError(f"OpenAI API error: {str(e)}")
