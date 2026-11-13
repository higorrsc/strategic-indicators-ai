"""API v1 routers."""

from .accounting_router import router as accounting_router
from .budgeting_router import router as budgeting_router
from .contracts_router import router as contracts_router
from .indicators_router import router as indicators_router
from .intelligence_router import router as intelligence_router
from .measurements_router import router as measurements_router

__all__ = [
    "accounting_router",
    "budgeting_router",
    "contracts_router",
    "indicators_router",
    "intelligence_router",
    "measurements_router",
]
