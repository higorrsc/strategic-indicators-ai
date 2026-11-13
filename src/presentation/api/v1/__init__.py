"""API v1 routers."""

from .accounting_router import router as accounting_router
from .allocation_router import router as allocation_router
from .budgeting_router import router as budgeting_router
from .indicators_router import router as indicators_router
from .intelligence_router import router as intelligence_router

__all__ = [
    "accounting_router",
    "allocation_router",
    "budgeting_router",
    "indicators_router",
    "intelligence_router",
]
