"""
Utility functions for text processing
"""

from rapidfuzz import fuzz
import re


def calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    return fuzz.ratio(text1, text2) / 100.0


def clean_text(text: str) -> str:
    """清理文本，去除多余空白和特殊字符"""
    # 去除多余空白
    text = re.sub(r"\s+", " ", text)
    # 去除特殊字符但保留中文标点
    text = re.sub(r"[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", "", text)
    return text.strip()


def format_text_for_display(text: str, max_length: int = 1000) -> str:
    """格式化文本用于显示，限制长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
