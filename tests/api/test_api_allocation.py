"""Integration tests for Cost Allocation API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_register_contract_and_submit_measurement(
    client: AsyncClient,
) -> None:
    """Verify contract registration, measurement submission, and exact penny split."""
    # Setup cost centers
    resp_cc1 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.1", "name": "IT Core", "parent_id": None},
    )
    cc1_id = resp_cc1.json()["id"]

    resp_cc2 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.2", "name": "IT Infrastructure", "parent_id": None},
    )
    cc2_id = resp_cc2.json()["id"]

    resp_cc3 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.3", "name": "IT Security", "parent_id": None},
    )
    cc3_id = resp_cc3.json()["id"]

    # Setup supplier in repo
    supplier_id = uuid4()
    supplier = Supplier(
        id=supplier_id,
        name="Cloud Corp",
        tax_id="12.345.678/0001-90",
    )
    container = get_container()
    await container.supplier_repo.add(supplier)

    # Register contract with 33.34%, 33.33%, 33.33% default allocations
    contract_payload = {
        "code": "CT-2026-001",
        "supplier_id": str(supplier_id),
        "title": "Cloud Platform Hosting",
        "default_allocations": [
            {"cost_center_id": cc1_id, "percentage": "33.34"},
            {"cost_center_id": cc2_id, "percentage": "33.33"},
            {"cost_center_id": cc3_id, "percentage": "33.33"},
        ],
    }
    resp_contract = await client.post("/api/v1/contracts", json=contract_payload)
    assert resp_contract.status_code == 201
    contract_id = resp_contract.json()["id"]

    # Submit measurement with $1,000.00
    measurement_payload = {
        "contract_id": contract_id,
        "period": "2026-03",
        "description": "March Hosting Services",
        "gross_amount": "1000.00",
        "currency": "USD",
        "allocation_override": None,
    }
    resp_m = await client.post("/api/v1/measurements", json=measurement_payload)
    assert resp_m.status_code == 201
    m_data = resp_m.json()
    assert m_data["state"] == "SUBMITTED"
    assert len(m_data["entries"]) == 3

    # Exact split check: 333.40 + 333.30 + 333.30 == 1000.00
    amounts = [e["amount"] for e in m_data["entries"]]
    assert "333.40" in amounts
    assert amounts.count("333.30") == 2
    measurement_id = m_data["id"]

    # Approve measurement
    resp_approve = await client.post(f"/api/v1/measurements/{measurement_id}/approve")
    assert resp_approve.status_code == 200
    assert resp_approve.json()["state"] == "APPROVED"


@pytest.mark.asyncio
async def test_should_reject_measurement_allocation_exceeding_100_percent(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 400 Bad Request when custom allocation exceeds 100%."""
    # Setup cost center
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "2.1", "name": "Operations", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Fast Logistics",
            tax_id="99.888.777/0001-11",
        )
    )

    resp_contract = await client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-LOG-001",
            "supplier_id": str(supplier_id),
            "title": "Logistics Services",
            "default_allocations": [{"cost_center_id": cc_id, "percentage": "100.00"}],
        },
    )
    contract_id = resp_contract.json()["id"]

    # Submit measurement with 110% allocation override
    resp_m = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-03",
            "description": "Logistics March",
            "gross_amount": "5000.00",
            "currency": "USD",
            "allocation_override": [{"cost_center_id": cc_id, "percentage": "110.00"}],
        },
    )
    # Pydantic validates le=100 on AllocationShareSchema
    assert resp_m.status_code == 422
