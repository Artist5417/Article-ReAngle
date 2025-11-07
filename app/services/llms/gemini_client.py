"""
调用Gemini API洗稿
"""

import os
import yaml

from google import genai

from app.configs.settings import SYSTEMZ_PROMPTS_DIR


async def get_rewriting_result(
    instruction: str,
    source: str,
    model: str = "gemini-2.5-flash",
):
    """
    调用Gemini models API洗稿

    Args:
        instruction: 用户输入的洗稿方式或选择的洗稿风格预设
        source: 原始文章
        model: 模型选择，默认为gemini-2.5-flash

    Returns:
        GenerateContentResponse对象
    """
    # 从yaml文件中加载system prompt
    prompt_file = os.path.join(SYSTEMZ_PROMPTS_DIR, "gemini_system_prompt.yaml")

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_data = yaml.safe_load(f)
        system_prompt = prompt_data.get("system_prompt", "")

    # 初始化Gemini client，此处会自动获取环境变量中的“GEMINI_API_KEY”
    client = genai.Client()

    # 合并system prompt，instruction，和source
    combined_content = (
        f"{system_prompt}\n\nInstruction: {instruction}\n\nSource: {source}"
    )

    # 通过models创建任务，获取response对象
    response = client.models.generate_content(
        model=model,
        contents=combined_content,
    )

    return response
