import os

# Set test environment BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./test.db"
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.session import Base, get_db
from app.main import app
from app.api.deps import get_current_user_id

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_test = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def override_get_user_id() -> uuid.UUID:
    return TEST_USER_ID


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_user_id


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        yield session
