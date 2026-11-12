"""Pytest fixtures for API testing with async SQLite database."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.presentation.app import create_app
from src.presentation.dependencies import get_container
from src.shared.config.settings import Settings
from src.shared.infrastructure.database.base import Base


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database() -> AsyncIterator[None]:
    """Initialize in-memory SQLite database and tables for API tests.

    Yields:
        None: When test database is prepared.
    """
    container = get_container()
    container.settings = Settings(AI_PROVIDER="fake")
    await container.init_database("sqlite+aiosqlite:///:memory:")

    if container.engine is not None:
        async with container.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    if container.engine is not None:
        async with container.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await container.close_database()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an asynchronous HTTP test client bound to FastAPI application.

    Yields:
        AsyncClient: Test HTTP client.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
