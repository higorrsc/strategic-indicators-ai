"""Pagination DTO for allocation application layer."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaginatedResultDTO[T]:
    """Application DTO holding paginated slice items and total count."""

    items: list[T]
    total_items: int
    page: int
    per_page: int
