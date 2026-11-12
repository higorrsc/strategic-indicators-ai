"""API v1 routers."""

from src.presentation.api.v1.allocation_router import (
    router as allocation_router,
)
from src.presentation.api.v1.budgeting_router import (
    router as budgeting_router,
)
from src.presentation.api.v1.indicators_router import (
    router as indicators_router,
)
from src.presentation.api.v1.intelligence_router import (
    router as intelligence_router,
)

__all__ = [
    "allocation_router",
    "budgeting_router",
    "indicators_router",
    "intelligence_router",
]
