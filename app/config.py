"""
Configuration and constants for Article ReAngle
"""

import os

# Base directory - app folder location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Static files directory (frontend)
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Results directory for storing generated content
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# OpenAI Configuration
OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
