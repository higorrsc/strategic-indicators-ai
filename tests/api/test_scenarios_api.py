"""Integration tests for What-If Scenarios API endpoints."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_simulate_whatif_scenario_with_contract_inflation(
    client: AsyncClient,
) -> None:
    """Verify in-memory What-If scenario simulation via HTTP."""
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

    # Simulate What-If Scenario with 50% inflation on contract
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
