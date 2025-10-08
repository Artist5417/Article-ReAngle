"""
OpenAI LLM服务
使用OpenAI API
"""

import httpx
import json
import os
import requests
from typing import Optional

# OpenAI配置
OPENAI_BASE_URL = "https://api.openai.com/v1"

async def call_openai(messages: list, model: str = "gpt-4o-mini", api_key: str | None = None) -> str:
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
            "Content-Type": "application/json"
        }
        
        # 智能token计算（采用api/index.py的逻辑）
        user_message = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
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
        available_tokens = max(0, model_total_window - approx_input_tokens - safety_margin)

        # 生成上限受三个因素共同约束：目标、模型生成上限、可用空间
        max_tokens = max(
            256,
            min(target_tokens, model_completion_cap, available_tokens)
        )
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
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
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            # 返回更清晰的硬上限提示
            err_text = response.text or ''
            if 'max_tokens' in err_text or 'maximum' in err_text:
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

async def call_free_llm(messages: list, model: str = "gpt-4o-mini", api_key: str = None) -> str:
    """调用OpenAI API"""
    return await call_openai(messages, model, api_key)

async def rewrite_text(text: str, user_requirement: str, api_key: str = None) -> str:
    """根据用户要求改写文本"""
    # 统一"忠实改写器"提示词
    system_prompt = (
        "你是一个\"忠实改写器\"，也是一个精准且不编造内容的文本改写引擎。\n\n"
        "【任务】\n"
        "在不新增事实、不删除关键信息的前提下，根据用户给定的\"观点/立场与表达风格\"对原文进行重写。\n\n"
        "【核心原则】\n"
        "1. 内容忠实：不得编造、夸大或引入原文没有的事实、数据、引用、时间线、人名或机构名。\n"
        "2. 信息保全：保留原文的核心要点、关键数据、结论与限定条件；如原文有不确定性或前提，必须保留。\n"
        "3. 立场与风格：严格按用户指定的观点与表达方式改写（如学术、口语、营销、中立、正向、反向），通过措辞和论证角度体现立场，而不是篡改事实。\n"
        "4. 风格控制：在语气、词汇、逻辑密度、结构上体现用户要求的风格。\n"
        "5. 可读性：结构清晰、层次分明，必要时可用小标题和段落组织内容。\n"
        "6. 引文与链接：若原文包含引用、链接、人名、机构名或数值，必须完整保留且不得歧义重写。\n"
        "7. 长度控制：若用户指定字数或篇幅，需严格遵守（允许上下浮动 10%）；未指定时保持与原文相近。\n"
        "8. 语言保持：默认保持与原文相同的语言，除非用户另有要求。\n"
        "9. 冲突兜底：若用户需求与事实冲突，应保持事实，用语气和 framing 表达立场，不得改写事实本身。\n"
        "10. 敏感与合规：避免人身攻击、仇恨或违规内容；任何情况下不得生成违法内容。\n\n"
        "【输出规则】\n"
        "- 只输出改写后的正文，不要前言、解释或步骤说明。\n"
        "- 默认使用 Markdown 格式（保留段落、列表、引用、代码块等）。"
    )

    user_prompt_template = (
        "【用户需求】\n{req}\n\n"
        "【原文】\n{src}\n\n"
        "【任务】\n请严格遵循以上规则，根据\"用户需求\"重写\"原文\"，输出完整正文。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_template.format(req=user_requirement, src=text)}
    ]
    
    return await call_free_llm(messages, api_key=api_key)
