"""Pytest fixtures for BDD testing with async SQLite database."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.presentation.app import create_app
from src.presentation.dependencies import get_container
from src.shared.config.settings import Settings
from src.shared.infrastructure.database.base import Base


@pytest.fixture(autouse=True)
def setup_test_database() -> Iterator[None]:
    """Initialize in-memory SQLite database and tables for BDD tests.

    Yields:
        None: When test database is prepared.
    """
    container = get_container()
    container.settings = Settings(AI_PROVIDER="fake")
    asyncio.run(container.init_database("sqlite+aiosqlite:///:memory:"))

    async def _init_tables() -> None:
        if container.engine is not None:
            async with container.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_tables())

    yield

    async def _drop_tables() -> None:
        if container.engine is not None:
            async with container.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        await container.close_database()

    asyncio.run(_drop_tables())


@pytest.fixture
def client() -> TestClient:
    """Provide a synchronous HTTP test client for BDD steps.

    Returns:
        TestClient: Synchronous test HTTP client.
    """
    app = create_app()
    return TestClient(app)
