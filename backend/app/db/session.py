from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# asyncpg pool params only work with postgresql, not sqlite
_engine_kwargs: dict = {"echo": settings.debug, "pool_pre_ping": True}
if settings.database_url.startswith("postgresql"):
    _engine_kwargs.update({"pool_size": 20, "max_overflow": 10})

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
