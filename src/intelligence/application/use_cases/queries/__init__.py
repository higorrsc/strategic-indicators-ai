"""Intelligence application queries package."""

from .analyze_allocation_anomalies import AnalyzeAllocationAnomaliesUseCase
from .generate_executive_summary import GenerateExecutiveSummaryUseCase

__all__ = [
    "AnalyzeAllocationAnomaliesUseCase",
    "GenerateExecutiveSummaryUseCase",
]
