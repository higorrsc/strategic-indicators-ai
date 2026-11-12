"""Asynchronous SQLAlchemy engine and session factory management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool


def create_database_engine(
    url: str,
    echo: bool = False,
    **kwargs: Any,
) -> AsyncEngine:
    """Create and configure an asynchronous SQLAlchemy engine.

    Args:
        url: The database connection URL.
        echo: Whether to log generated SQL statements.
        **kwargs: Additional parameters passed to `create_async_engine`.

    Returns:
        AsyncEngine: The configured asynchronous database engine.
    """
    engine_kwargs: dict[str, Any] = {"echo": echo, **kwargs}

    if url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["poolclass"] = NullPool

    return create_async_engine(url, **engine_kwargs)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create an asynchronous sessionmaker factory bound to the given engine.

    Args:
        engine: The target asynchronous database engine.

    Returns:
        async_sessionmaker[AsyncSession]: The configured session factory.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_async_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Yield an asynchronous database session with automated rollback on error.

    Args:
        session_factory: The configured sessionmaker factory.

    Yields:
        AsyncSession: An active database session.
    """
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
