"""Integration tests for executive summary caching and scope filtering API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_executive_summary_cache_headers_and_force_refresh(
    client: AsyncClient,
) -> None:
    # 1. First call: MISS -> status MISS, is_cached False, X-Cache-Status MISS
    resp1 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br"
    )
    assert resp1.status_code == 200
    assert resp1.headers["X-Cache-Status"] == "MISS"
    data1 = resp1.json()
    assert data1["is_cached"] is False
    assert data1["cache_status"] == "MISS"

    # 2. Second call with same params: HIT -> status HIT, is_cached True
    resp2 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br"
    )
    assert resp2.status_code == 200
    assert resp2.headers["X-Cache-Status"] == "HIT"
    data2 = resp2.json()
    assert data2["is_cached"] is True
    assert data2["cache_status"] == "HIT"

    # 3. Third call with force_refresh=true: FORCED_REFRESH
    resp3 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br&force_refresh=true"
    )
    assert resp3.status_code == 200
    assert resp3.headers["X-Cache-Status"] == "FORCED_REFRESH"
    data3 = resp3.json()
    assert data3["is_cached"] is False
    assert data3["cache_status"] == "FORCED_REFRESH"


@pytest.mark.asyncio
async def test_executive_summary_pdf_cache_headers(client: AsyncClient) -> None:
    # First PDF call: MISS
    resp1 = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-11&lang=pt-br"
    )
    assert resp1.status_code == 200
    assert resp1.headers["X-Cache-Status"] == "MISS"
    assert resp1.headers["content-type"] == "application/pdf"

    # Second PDF call: HIT
    resp2 = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-11&lang=pt-br"
    )
    assert resp2.status_code == 200
    assert resp2.headers["X-Cache-Status"] == "HIT"
