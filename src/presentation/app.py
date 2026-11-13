"""FastAPI application factory and middleware configuration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.presentation.api.v1 import (
    accounting_router,
    allocation_router,
    budgeting_router,
    indicators_router,
    intelligence_router,
)
from src.presentation.dependencies import get_container
from src.presentation.exception_handlers import register_exception_handlers
from src.shared.config.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional configuration settings instance.

    Returns:
        FastAPI: Configured application instance.
    """
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        container = get_container()
        if not container.use_database and app_settings.DATABASE_URL:
            await container.init_database(
                app_settings.DATABASE_URL,
                echo=app_settings.DATABASE_ECHO,
            )
        yield
        if container.use_database:
            await container.close_database()

    app = FastAPI(
        title=app_settings.APP_NAME,
        description=(
            "Strategic Budget Indicators API with Exact Penny Cost Allocation, "
            "In-Memory What-If Simulations, Anomaly Detection, and Multi-Provider AI."
        ),
        version="0.1.0",
        debug=app_settings.DEBUG,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"], summary="Health check probe")
    async def health_check() -> dict[str, str]:
        """Health check endpoint for container probes and monitoring."""
        return {"status": "ok", "app": app_settings.APP_NAME}

    app.include_router(budgeting_router)
    app.include_router(allocation_router)
    app.include_router(accounting_router)
    app.include_router(indicators_router)
    app.include_router(intelligence_router)

    return app
