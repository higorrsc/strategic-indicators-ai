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


@pytest.mark.asyncio
async def test_should_list_contracts_and_measurements_with_filters(
    client: AsyncClient,
) -> None:
    """Verify listing contracts and measurements with query filtering."""
    # 1. Setup cost center
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "3.1", "name": "Marketing Operations", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    # 2. Setup supplier
    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Ad Agency Media",
            tax_id="55.666.777/0001-88",
        )
    )

    # 3. Create active contract
    resp_c = await client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-MKT-LIST-01",
            "supplier_id": str(supplier_id),
            "title": "Social Campaigns",
            "default_allocations": [{"cost_center_id": cc_id, "percentage": "100.00"}],
        },
    )
    assert resp_c.status_code == 201
    contract_id = resp_c.json()["id"]

    # 4. List contracts (paginated)
    resp_list_c = await client.get("/api/v1/contracts?page=1&perPage=20")
    assert resp_list_c.status_code == 200
    contracts_payload = resp_list_c.json()
    assert "data" in contracts_payload
    assert "pagination" in contracts_payload
    assert "links" in contracts_payload
    assert contracts_payload["pagination"]["page"] == 1
    assert contracts_payload["pagination"]["perPage"] == 20
    assert any(c["id"] == contract_id for c in contracts_payload["data"])

    # Filter contracts by supplier with pagination
    resp_sup_c = await client.get(
        f"/api/v1/contracts?supplier_id={supplier_id}&page=1&perPage=10"
    )
    assert resp_sup_c.status_code == 200
    sup_payload = resp_sup_c.json()
    assert all(c["supplier_id"] == str(supplier_id) for c in sup_payload["data"])
    assert (
        sup_payload["links"]["self"]
        == f"/api/v1/contracts?supplier_id={supplier_id}&page=1&perPage=10"
    )

    # 5. Submit measurements across periods
    resp_m1 = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-04",
            "description": "April Campaign",
            "gross_amount": "8000.00",
            "currency": "USD",
        },
    )
    assert resp_m1.status_code == 201
    m1_id = resp_m1.json()["id"]

    resp_m2 = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-05",
            "description": "May Campaign",
            "gross_amount": "12000.00",
            "currency": "USD",
        },
    )
    assert resp_m2.status_code == 201
    m2_id = resp_m2.json()["id"]

    # Approve m1
    await client.post(f"/api/v1/measurements/{m1_id}/approve")

    # 6. List measurements by period (paginated)
    resp_m_apr = await client.get("/api/v1/measurements?period=2026-04")
    assert resp_m_apr.status_code == 200
    apr_data = resp_m_apr.json()
    assert apr_data["pagination"]["totalItems"] >= 1
    assert any(m["id"] == m1_id for m in apr_data["data"])
    assert not any(m["id"] == m2_id for m in apr_data["data"])
    assert "period=2026-04" in apr_data["links"]["self"]

    # List measurements by state
    resp_approved = await client.get(
        f"/api/v1/measurements?contract_id={contract_id}&state=APPROVED"
    )
    assert resp_approved.status_code == 200
    approved_data = resp_approved.json()
    assert len(approved_data["data"]) == 1
    assert approved_data["data"][0]["id"] == m1_id

    # List measurements with slicing
    resp_slice = await client.get(
        f"/api/v1/measurements?contract_id={contract_id}&page=1&perPage=1"
    )
    assert resp_slice.status_code == 200
    slice_data = resp_slice.json()
    assert len(slice_data["data"]) == 1
    assert slice_data["pagination"]["totalPages"] == 2
    assert slice_data["links"]["next"] is not None

    # List measurements for non-existent period
    resp_empty = await client.get("/api/v1/measurements?period=2029-12")
    assert resp_empty.status_code == 200
    empty_payload = resp_empty.json()
    assert empty_payload["data"] == []
    assert empty_payload["pagination"]["totalItems"] == 0
    assert empty_payload["pagination"]["totalPages"] == 0
