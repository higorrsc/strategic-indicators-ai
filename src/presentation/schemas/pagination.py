"""Pydantic schemas and generic envelopes for paginated API responses."""

from __future__ import annotations

import math
from urllib.parse import urlencode

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field


class PaginationMeta(BaseModel):
    """Metadata detailing pagination position and collection totals."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    page: int = Field(description="Current page index (1-based).")
    per_page: int = Field(alias="perPage", description="Number of items per page.")
    total_items: int = Field(alias="totalItems", description="Total number of items.")
    total_pages: int = Field(alias="totalPages", description="Total number of pages.")


class PaginationLinks(BaseModel):
    """HATEOAS navigation links for paginated collection traversal."""

    model_config = ConfigDict(frozen=True)

    self: str = Field(description="URL to the current page.")
    first: str = Field(description="URL to the first page.")
    last: str = Field(description="URL to the last page.")
    next: str | None = Field(default=None, description="URL to next page, or null.")
    prev: str | None = Field(default=None, description="URL to previous page, or null.")


class PaginatedResponse[T](BaseModel):
    """Generic envelope wrapping paginated collection data, metadata, and links."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    data: list[T] = Field(description="List of records for the current page.")
    pagination: PaginationMeta = Field(description="Pagination indicators and totals.")
    links: PaginationLinks = Field(description="Hypermedia navigation links.")


def calculate_total_pages(total_items: int, per_page: int) -> int:
    """Calculate the total number of pages based on item count and page size.

    Args:
        total_items: Total count of items.
        per_page: Items per page.

    Returns:
        int: Total number of pages (0 if total_items is 0).
    """
    if total_items <= 0 or per_page <= 0:
        return 0
    return math.ceil(total_items / per_page)


def build_pagination_links(
    request: Request,
    page: int,
    per_page: int,
    total_pages: int,
) -> PaginationLinks:
    """Build HATEOAS navigation links preserving any existing query parameters.

    Args:
        request: Incoming FastAPI Request object.
        page: Current page number (1-based).
        per_page: Items per page.
        total_pages: Total number of calculated pages.

    Returns:
        PaginationLinks: Structured navigation URLs.
    """
    path = request.url.path
    query_params = dict(request.query_params)

    def _make_url(target_page: int) -> str:
        params = {**query_params, "page": str(target_page), "perPage": str(per_page)}
        return f"{path}?{urlencode(params)}"

    last_page = max(total_pages, 1)

    self_url = _make_url(page)
    first_url = _make_url(1)
    last_url = _make_url(last_page)

    prev_url = _make_url(page - 1) if page > 1 and total_pages > 0 else None
    next_url = _make_url(page + 1) if page < total_pages else None

    return PaginationLinks(
        self=self_url,
        first=first_url,
        last=last_url,
        next=next_url,
        prev=prev_url,
    )
