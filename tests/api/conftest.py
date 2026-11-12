"""Pytest fixtures for API testing."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.presentation.app import create_app
from src.presentation.dependencies import get_container
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def reset_container() -> None:
    """Reset dependency container state between tests."""
    container = get_container()
    container.settings = Settings(AI_PROVIDER="fake")
    container.reset()


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
