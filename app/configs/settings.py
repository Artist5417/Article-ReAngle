"""
项目的配置和常量
"""

import os

# 项目根目录 - app文件夹地址
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 前端静态文件地址
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 小程序任务结果存放地址
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# system prompts存放地址
SYSTEMZ_PROMPTS_DIR = os.path.join(BASE_DIR, "services", "llms", "prompts")

# 准备弃用：旧版大模型调用
OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
