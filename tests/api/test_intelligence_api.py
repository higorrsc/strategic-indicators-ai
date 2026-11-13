"""Integration tests for Strategic Intelligence API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_generate_ai_executive_summary_and_respect_languages(
    client: AsyncClient,
) -> None:
    """Verify AI Executive Summary generation with language negotiation
    and validation.
    """
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.1", "name": "IT Core", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    await client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": cc_id,
            "period": "2026-03",
            "category": "OPEX",
            "amount": "50000.00",
            "currency": "USD",
        },
    )

    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Cloud Vendor",
            tax_id="11.222.333/0001-44",
        )
    )

    resp_contract = await client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-CLOUD-001",
            "supplier_id": str(supplier_id),
            "title": "Cloud Services",
            "default_allocations": [{"cost_center_id": cc_id, "percentage": "100.00"}],
        },
    )
    contract_id = resp_contract.json()["id"]

    resp_m = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-03",
            "description": "March Cloud Invoice",
            "gross_amount": "35000.00",
            "currency": "USD",
        },
    )
    m_id = resp_m.json()["id"]
    await client.post(f"/api/v1/measurements/{m_id}/approve")

    # Default pt-br
    resp_summary = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-03"
    )
    assert resp_summary.status_code == 200
    summary_data = resp_summary.json()
    assert summary_data["period"] == "2026-03"
    assert summary_data["financial_health_status"] == "HEALTHY"
    assert summary_data["language"] == "pt-br"
    assert "execução orçamentária equilibrada" in summary_data["executive_summary"]
    assert len(summary_data["strategic_recommendations"]) >= 1

    # Explicit en-us
    resp_summary_en = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-03&lang=en-us"
    )
    assert resp_summary_en.status_code == 200
    summary_en = resp_summary_en.json()
    assert summary_en["language"] == "en-us"
    assert "balanced budget execution" in summary_en["executive_summary"]

    # Invalid language -> 422
    resp_summary_invalid = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-03&lang=fr-fr"
    )
    assert resp_summary_invalid.status_code == 422

    # Check anomalies endpoint
    resp_anomalies = await client.get(f"/api/v1/intelligence/anomalies/{m_id}")
    assert resp_anomalies.status_code == 200
    assert isinstance(resp_anomalies.json(), list)


@pytest.mark.asyncio
async def test_should_download_executive_summary_pdf(client: AsyncClient) -> None:
    """Verify PDF executive report generation and language options."""
    resp_pdf_pt = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-03"
    )
    assert resp_pdf_pt.status_code == 200
    assert resp_pdf_pt.headers["content-type"] == "application/pdf"
    assert (
        'attachment; filename="sumario-executivo-2026-03-pt-br.pdf"'
        in resp_pdf_pt.headers["content-disposition"]
    )
    assert resp_pdf_pt.content.startswith(b"%PDF")
    assert len(resp_pdf_pt.content) > 1000

    resp_pdf_en = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-03&lang=en-us"
    )
    assert resp_pdf_en.status_code == 200
    assert (
        'attachment; filename="executive-summary-2026-03-en-us.pdf"'
        in resp_pdf_en.headers["content-disposition"]
    )
    assert resp_pdf_en.content.startswith(b"%PDF")

    # Reject invalid period format and invalid language for PDF download
    resp_invalid_pdf = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-13"
    )
    assert resp_invalid_pdf.status_code == 422

    resp_invalid_pdf_lang = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-03&lang=es-es"
    )
    assert resp_invalid_pdf_lang.status_code == 422


@pytest.mark.asyncio
async def test_executive_summary_cache_headers_and_force_refresh(
    client: AsyncClient,
) -> None:
    """Verify X-Cache-Status headers and cache invalidation behavior."""
    # 1. First call: MISS
    resp1 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br"
    )
    assert resp1.status_code == 200
    assert resp1.headers["X-Cache-Status"] == "MISS"
    data1 = resp1.json()
    assert data1["is_cached"] is False
    assert data1["cache_status"] == "MISS"

    # 2. Second call with same params: HIT
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
    """Verify PDF cache status tracking headers."""
    resp1 = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-11&lang=pt-br"
    )
    assert resp1.status_code == 200
    assert resp1.headers["X-Cache-Status"] == "MISS"
    assert resp1.headers["content-type"] == "application/pdf"

    resp2 = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-11&lang=pt-br"
    )
    assert resp2.status_code == 200
    assert resp2.headers["X-Cache-Status"] == "HIT"
