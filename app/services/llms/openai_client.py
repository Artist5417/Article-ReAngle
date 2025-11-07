"""
调用OpenAI API洗稿
"""

import os
import yaml

from openai import OpenAI

from app.configs.settings import SYSTEMZ_PROMPTS_DIR


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
    # 从yaml文件中加载system prompt
    prompt_file = os.path.join(SYSTEMZ_PROMPTS_DIR, "openai_system_prompt.yaml")

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_data = yaml.safe_load(f)
        system_prompt = prompt_data.get("system_prompt", "")

    # 初始化OpenAI client，此处会自动获取环境变量中的“OPENAI_API_KEY”
    client = OpenAI()

    # 通过Responses创建任务，获取response对象
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

    return response
