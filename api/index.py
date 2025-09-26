import os
import sys

# Ensure backend package is importable on Vercel
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import FastAPI app from backend
from main import app  # noqa: F401

# Vercel Python runtime will look for a module-level variable named `app`
# which is an ASGI application (FastAPI is ASGI-compatible).


