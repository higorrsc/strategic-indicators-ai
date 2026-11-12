"""Pytest fixtures for BDD testing."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.presentation.app import create_app
from src.presentation.dependencies import get_container
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def reset_container() -> None:
    """Reset dependency container state with fake AI provider for BDD tests."""
    container = get_container()
    container.settings = Settings(AI_PROVIDER="fake")
    container.reset()


@pytest.fixture
def client() -> TestClient:
    """Provide a synchronous HTTP test client for BDD steps.

    Returns:
        TestClient: Synchronous test HTTP client.
    """
    app = create_app()
    return TestClient(app)
