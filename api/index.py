"""
Vercel Serverless Function entry point for the FastAPI backend.
Vercel's Python runtime detects the ASGI app and serves it automatically.
"""
import sys
import os
import asyncio

# Add the backend directory to the Python path so 'app' package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Force environment settings suitable for serverless deployment
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "false")

from app.main import app  # noqa: E402

# In serverless, the ASGI lifespan may not trigger.
# Create database tables synchronously at import time to ensure they exist.
from app.db.session import engine, Base  # noqa: E402


async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If there's already a running loop, schedule the coroutine
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(asyncio.run, _create_tables()).result()
    else:
        loop.run_until_complete(_create_tables())
except RuntimeError:
    asyncio.run(_create_tables())
