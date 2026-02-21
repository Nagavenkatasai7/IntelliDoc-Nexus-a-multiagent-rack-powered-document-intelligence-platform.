"""
Vercel Serverless Function entry point for the FastAPI backend.
Vercel's Python runtime detects the ASGI app and serves it automatically.
"""
import sys
import os

# Add the backend directory to the Python path so 'app' package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Force environment settings suitable for serverless deployment
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "false")

from app.main import app  # noqa: E402
