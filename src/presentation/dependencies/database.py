"""Database session dependency providers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .container import get_container


async def get_db_session() -> AsyncGenerator[AsyncSession | None]:
    """Yield an active asynchronous database session per request if configured.

    Yields:
        AsyncSession | None: Active session or None when using in-memory mode.
    """
    container = get_container()
    if container.use_database and container.session_factory is not None:
        async with container.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    else:
        yield None
