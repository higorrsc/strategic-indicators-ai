"""Unit tests for pagination schemas and link builder utilities."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import Request

from src.presentation.schemas.pagination import (
    PaginatedResponse,
    PaginationLinks,
    PaginationMeta,
    build_pagination_links,
    calculate_total_pages,
)


def _mock_request(path: str, query_params: dict[str, str]) -> Request:
    mock_url = MagicMock()
    mock_url.path = path
    req = MagicMock(spec=Request)
    req.url = mock_url
    req.query_params = query_params
    return req


def test_calculate_total_pages() -> None:
    assert calculate_total_pages(0, 20) == 0
    assert calculate_total_pages(15, 20) == 1
    assert calculate_total_pages(20, 20) == 1
    assert calculate_total_pages(21, 20) == 2
    assert calculate_total_pages(150, 20) == 8


def test_should_build_pagination_links_intermediate_page() -> None:
    req = _mock_request("/api/v1/tasks", {"status": "ACTIVE"})
    links = build_pagination_links(req, page=2, per_page=20, total_pages=8)

    assert links.self == "/api/v1/tasks?status=ACTIVE&page=2&perPage=20"
    assert links.first == "/api/v1/tasks?status=ACTIVE&page=1&perPage=20"
    assert links.last == "/api/v1/tasks?status=ACTIVE&page=8&perPage=20"
    assert links.prev == "/api/v1/tasks?status=ACTIVE&page=1&perPage=20"
    assert links.next == "/api/v1/tasks?status=ACTIVE&page=3&perPage=20"


def test_should_build_pagination_links_first_page() -> None:
    req = _mock_request("/api/v1/contracts", {})
    links = build_pagination_links(req, page=1, per_page=10, total_pages=3)

    assert links.self == "/api/v1/contracts?page=1&perPage=10"
    assert links.first == "/api/v1/contracts?page=1&perPage=10"
    assert links.last == "/api/v1/contracts?page=3&perPage=10"
    assert links.prev is None
    assert links.next == "/api/v1/contracts?page=2&perPage=10"


def test_should_build_pagination_links_last_page() -> None:
    req = _mock_request("/api/v1/contracts", {})
    links = build_pagination_links(req, page=3, per_page=10, total_pages=3)

    assert links.prev == "/api/v1/contracts?page=2&perPage=10"
    assert links.next is None


def test_should_build_pagination_links_empty_collection() -> None:
    req = _mock_request("/api/v1/measurements", {"period": "2029-12"})
    links = build_pagination_links(req, page=1, per_page=20, total_pages=0)

    assert links.self == "/api/v1/measurements?period=2029-12&page=1&perPage=20"
    assert links.first == "/api/v1/measurements?period=2029-12&page=1&perPage=20"
    assert links.last == "/api/v1/measurements?period=2029-12&page=1&perPage=20"
    assert links.prev is None
    assert links.next is None


def test_paginated_response_schema_serialization() -> None:
    meta = PaginationMeta(page=1, per_page=20, total_items=150, total_pages=8)
    links = PaginationLinks(
        self="/tasks?page=1&perPage=20",
        first="/tasks?page=1&perPage=20",
        last="/tasks?page=8&perPage=20",
        next="/tasks?page=2&perPage=20",
        prev=None,
    )
    resp = PaginatedResponse[dict[str, str]](
        data=[{"id": "1", "name": "Task 1"}],
        pagination=meta,
        links=links,
    )
    dumped = resp.model_dump(by_alias=True)
    assert dumped["pagination"]["perPage"] == 20
    assert dumped["pagination"]["totalItems"] == 150
    assert dumped["pagination"]["totalPages"] == 8
    assert len(dumped["data"]) == 1
