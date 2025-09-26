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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # 优先使用环境变量，如果没有则使用用户输入的API Key
OPENAI_BASE_URL = "https://api.openai.com/v1"

# 如果环境变量为空，尝试从系统环境变量重新读取
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

async def call_openai(messages: list, model: str = "gpt-4o-mini", api_key: str = None) -> str:
    """使用OpenAI API"""
    # 检查API Key是否有效
    if not api_key or api_key.strip() == "":
        return "错误：未提供OpenAI API Key。请在界面中输入API Key。"
    
    # 清理API Key，移除可能的空白字符
    key_to_use = api_key.strip()
    
    try:
        # 使用requests库作为备用方案
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": model,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
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
    messages = [
        {
            "role": "system",
            "content": "你是一个文本重写工具。用户给你一段文字和一个要求，你需要把这段文字保留关键信息的同时，按照用户输入的要求重新写一遍。"
        },
        {
            "role": "user",
            "content": f"要求：{user_requirement}\n\n把下面这段文字按要求重写：\n\n{text}"
        }
    ]
    
    return await call_free_llm(messages, api_key=api_key)
