"""
LLM services for text rewriting and generation
Uses OpenAI API
"""

import os
import requests
from typing import Optional

from app.config import OPENAI_BASE_URL, DEFAULT_MODEL


async def call_openai(
    messages: list, model: str = DEFAULT_MODEL, api_key: str | None = None
) -> str:
    """使用OpenAI API"""
    # 兼容：优先使用传入的 api_key；若为空，则回退到环境变量
    key_from_env = os.getenv("OPENAI_API_KEY", "").strip()
    key_to_use = (api_key or "").strip() or key_from_env
    if not key_to_use:
        return "错误：未提供 OpenAI API Key（既没有界面输入，也没有环境变量 OPENAI_API_KEY）。"

    try:
        # 使用requests库作为备用方案
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json",
        }

        # 智能token计算（采用api/index.py的逻辑）
        user_message = next(
            (msg["content"] for msg in messages if msg["role"] == "user"), ""
        )
        text_length = len(user_message)

        # 目标生成长度：原文约110%，以保证不变短；保底1000
        target_tokens = max(1000, int(text_length * 1.1))
        # 经验上限：gpt-4o-mini 总窗口约 20000，生成上限≈16000
        model_total_window = 20000
        model_completion_cap = 16000
        # 估算输入token（粗略按4字符≈1token），并为系统/提示保留额外预算
        system_and_overhead_tokens = 300
        approx_input_tokens = int(len(user_message) / 4) + system_and_overhead_tokens

        # 可用生成空间 = 总窗口 - 输入 - 安全余量
        safety_margin = 500
        available_tokens = max(
            0, model_total_window - approx_input_tokens - safety_margin
        )

        # 生成上限受三个因素共同约束：目标、模型生成上限、可用空间
        max_tokens = max(
            256, min(target_tokens, model_completion_cap, available_tokens)
        )

        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        # 超限前置校验：若无可用生成空间则直接报错
        if available_tokens < 256:
            return (
                f"错误：输入过长超出模型窗口。估算输入tokens约 {approx_input_tokens}，"
                f"模型总窗口 {model_total_window}，安全余量 {safety_margin}，可用生成空间 {available_tokens}。"
                f"请缩短输入或改用分段重写。"
            )

        # 使用requests库发送请求
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=request_data,
            timeout=60,
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            # 返回更清晰的硬上限提示
            err_text = response.text or ""
            if "max_tokens" in err_text or "maximum" in err_text:
                return (
                    "OpenAI API错误: 请求超出模型限制。"
                    f"输入估算 {approx_input_tokens} tokens，max_tokens 请求 {max_tokens}，"
                    f"模型生成上限约 {model_completion_cap}，总窗口 {model_total_window}，"
                    f"可用生成空间 {available_tokens}。请缩短输入或采用分段重写。\n原始错误：{err_text}"
                )
            return f"OpenAI API错误: {response.status_code} - {response.text}"

    except Exception as e:
        print(f"❌ 详细错误信息: {str(e)}")
        print(f"错误类型: {type(e)}")
        return f"OpenAI连接错误: {str(e)}"


async def call_free_llm(
    messages: list, model: str = DEFAULT_MODEL, api_key: str = None
) -> str:
    """调用OpenAI API"""
    return await call_openai(messages, model, api_key)


async def rewrite_text(text: str, user_requirement: str, api_key: str = None) -> str:
    """根据用户要求改写文本"""
    # 统一"忠实改写器"提示词
    system_prompt = (
        '你是一名"忠实改写器"。\n'
        "你的任务是根据用户提供的【观点/立场】与【表达风格】，对原文进行风格化重写。\n"
        "避免逐句同义替换；仅在有助于可读性或风格匹配时，可适度调整句式、语序或段落结构。\n\n"
        "改写原则：\n\n"
        "1. 立场与风格\n"
        "严格按用户要求的语气与表达方式改写（如学术 / 新闻 / 口语 / 营销 / 中立 / 正向 / 反向）。\n"
        "可自由调整句式、语序与用词，使语言更自然流畅、符合所需风格。\n\n"
        "2. 内容忠实\n"
        "可在原意基础上扩写、润色或重组表达，但不得编造不存在的事实、数据、时间线或人名。\n"
        "改写后的文章应逻辑自洽、信息表达完整，并在语气与整体表达方式上与原文有所区分。\n\n"
        "3. 可读性\n"
        "保持结构清晰、层次分明；\n"
        "必要时可添加小标题、过渡句或段落分隔来增强流畅性。\n\n"
        "4. 长度控制\n"
        "在不损失关键信息的前提下，篇幅可与原文相近（±10%）或依用户要求。\n\n"
        "5. 输出要求\n"
        "直接输出改写后的正文。\n"
        "不要解释过程、不要罗列步骤、不要添加任何说明性文字。"
    )

    user_prompt_template = (
        "【用户需求】\n{req}\n\n"
        "【原文】\n{src}\n\n"
        '【任务】\n请严格遵循以上规则，根据"用户需求"重写"原文"，输出完整正文。'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": user_prompt_template.format(req=user_requirement, src=text),
        },
    ]

    return await call_free_llm(messages, api_key=api_key)
