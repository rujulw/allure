from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def build_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or get_settings().database_url
    return create_async_engine(url, future=True)


def build_session_factory(engine_instance: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine_instance, expire_on_commit=False)


async def init_engine() -> None:
    global engine, SessionLocal
    if engine is None:
        engine = build_engine()
        SessionLocal = build_session_factory(engine)


async def close_engine() -> None:
    global engine, SessionLocal
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await init_engine()
    if SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")

    async with SessionLocal() as session:
        yield session
