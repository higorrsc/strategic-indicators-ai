"""Integration tests for Indicators and Strategic Intelligence API endpoints."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_compute_indicators_and_simulate_scenario(
    client: AsyncClient,
) -> None:
    """Verify indicators computation and what-if simulation via HTTP."""
    # Setup cost center
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.1", "name": "IT Core", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    # Set budget $50,000 for period 2026-03
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

    # Setup supplier & contract
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

    # Submit and approve measurement with $35,000 (70% execution rate -> NORMAL)
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

    # 1. Fetch indicators
    resp_indicators = await client.get("/api/v1/indicators/2026-03")
    assert resp_indicators.status_code == 200
    ind_data = resp_indicators.json()
    assert ind_data["period"] == "2026-03"
    assert ind_data["total_budgeted"] == "50000.00"
    assert ind_data["total_actual"] == "35000.00"
    assert ind_data["total_variance"] == "-15000.00"
    assert ind_data["indicators"][0]["status"] == "NORMAL"

    # 2. Simulate What-If Scenario with 50% inflation on contract
    # (35,000 * 1.5 = 52,500 -> overrun!)
    empty_shifts: list[dict[str, Any]] = []
    sim_payload = {
        "name": "50% Cloud Inflation",
        "period": "2026-03",
        "contract_inflation": {contract_id: "50.00"},
        "allocation_shifts": empty_shifts,
    }
    resp_sim = await client.post("/api/v1/scenarios/simulate", json=sim_payload)
    assert resp_sim.status_code == 200
    sim_data = resp_sim.json()
    assert sim_data["scenario_name"] == "50% Cloud Inflation"
    assert sim_data["new_overruns_count"] == 1
    assert sim_data["impacts"][0]["new_overrun"] is True
    assert sim_data["impacts"][0]["simulated_actual"] == "52500.00"

    # 3. Request AI Executive Summary (default pt-br, explicit en-us,
    # and rejection of invalid)
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

    resp_summary_en = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-03&lang=en-us"
    )
    assert resp_summary_en.status_code == 200
    summary_en = resp_summary_en.json()
    assert summary_en["language"] == "en-us"
    assert "balanced budget execution" in summary_en["executive_summary"]

    resp_summary_invalid = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-03&lang=fr-fr"
    )
    assert resp_summary_invalid.status_code == 422

    # 4. Check anomalies endpoint
    resp_anomalies = await client.get(f"/api/v1/intelligence/anomalies/{m_id}")
    assert resp_anomalies.status_code == 200
    assert isinstance(resp_anomalies.json(), list)

    # 5. Download Executive Summary PDF (default pt-br and explicit en-us)
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

    # 6. Reject invalid period format and invalid language for PDF download
    resp_invalid_pdf = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-13"
    )
    assert resp_invalid_pdf.status_code == 422

    resp_invalid_pdf_lang = await client.get(
        "/api/v1/intelligence/executive-summary/pdf?period=2026-03&lang=es-es"
    )
    assert resp_invalid_pdf_lang.status_code == 422
