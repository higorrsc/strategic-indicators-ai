"""Integration tests for Measurements API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_submit_measurement_and_calculate_exact_penny_allocations(
    client: AsyncClient,
) -> None:
    """Verify measurement submission with exact penny allocation across 3 centers."""
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

    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Cloud Corp",
            tax_id="12.345.678/0001-90",
        )
    )

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

    # Get measurement details
    resp_get = await client.get(f"/api/v1/measurements/{measurement_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == measurement_id


@pytest.mark.asyncio
async def test_should_return_404_when_measurement_not_found(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 404 when querying a non-existent measurement ID."""
    non_existent_id = uuid4()
    resp = await client.get(f"/api/v1/measurements/{non_existent_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_should_reject_measurement_allocation_exceeding_100_percent(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 422 Unprocessable Entity when custom allocation exceeds 100%."""
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
    assert resp_m.status_code == 422


@pytest.mark.asyncio
async def test_should_list_measurements_with_filters_and_pagination(
    client: AsyncClient,
) -> None:
    """Verify listing measurements with query filtering and pagination."""
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "4.1", "name": "Supply Chain", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Logistics Partner",
            tax_id="11.444.777/0001-22",
        )
    )

    resp_c = await client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-SC-01",
            "supplier_id": str(supplier_id),
            "title": "Freight Services",
            "default_allocations": [{"cost_center_id": cc_id, "percentage": "100.00"}],
        },
    )
    contract_id = resp_c.json()["id"]

    resp_m1 = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-04",
            "description": "April Freight",
            "gross_amount": "8000.00",
            "currency": "USD",
        },
    )
    m1_id = resp_m1.json()["id"]

    resp_m2 = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-05",
            "description": "May Freight",
            "gross_amount": "12000.00",
            "currency": "USD",
        },
    )
    m2_id = resp_m2.json()["id"]

    await client.post(f"/api/v1/measurements/{m1_id}/approve")

    # Filter by period
    resp_period = await client.get("/api/v1/measurements?period=2026-04")
    assert resp_period.status_code == 200
    data_period = resp_period.json()
    assert any(m["id"] == m1_id for m in data_period["data"])
    assert not any(m["id"] == m2_id for m in data_period["data"])

    # Filter by state
    resp_state = await client.get(
        f"/api/v1/measurements?contract_id={contract_id}&state=APPROVED"
    )
    assert resp_state.status_code == 200
    data_state = resp_state.json()
    assert len(data_state["data"]) == 1
    assert data_state["data"][0]["id"] == m1_id
