import os
import httpx
from typing import Optional

# 支持多种LLM配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

async def call_llm(messages: list, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    """调用LLM的通用函数"""
    if OPENAI_API_KEY:
        return await call_openai(messages, model, temperature)
    else:
        return await call_ollama(messages, model, temperature)

async def call_openai(messages: list, model: str, temperature: float) -> str:
    """调用OpenAI API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenAI API错误: {str(e)}"

async def call_ollama(messages: list, model: str, temperature: float) -> str:
    """调用本地Ollama"""
    try:
        # 将messages转换为Ollama格式
        prompt = messages[-1]['content']
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '无响应')
    except Exception as e:
        return f"Ollama错误: {str(e)}"

async def summarize_text(text: str) -> str:
    """总结文本，提取核心要点"""
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的文本分析师。请对给定的文章进行客观总结，提取核心信息和主要观点，保持中立立场。"
        },
        {
            "role": "user", 
            "content": f"请总结以下文章的核心内容：\n\n{text[:3000]}"  # 限制长度避免token过多
        }
    ]
    
    return await call_llm(messages)

async def rewrite_with_style(
    summary: str, 
    prompt: str = "改写成新闻报道风格"
) -> str:
    """根据用户提示词重写文章"""
    
    # 构建重写提示词
    rewrite_instruction = f"请根据以下要求改写文章：\n{prompt}"
    
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的文章改写专家。请根据用户的要求，在保留原文核心信息的基础上，按照指定的风格和立场重新组织表达。"
        },
        {
            "role": "user",
            "content": f"{rewrite_instruction}\n\n原文要点：\n{summary}"
        }
    ]
    
    return await call_llm(messages, temperature=0.8)
