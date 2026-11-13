"""Integration tests for Contracts API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_register_contract_and_retrieve_details(
    client: AsyncClient,
) -> None:
    """Verify contract registration and retrieval by ID."""
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.1", "name": "IT Infrastructure", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

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
            {"cost_center_id": cc_id, "percentage": "100.00"},
        ],
    }
    resp = await client.post("/api/v1/contracts", json=contract_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "CT-2026-001"
    assert data["title"] == "Cloud Platform Hosting"
    assert data["is_active"] is True
    contract_id = data["id"]

    resp_get = await client.get(f"/api/v1/contracts/{contract_id}")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert get_data["id"] == contract_id
    assert get_data["code"] == "CT-2026-001"


@pytest.mark.asyncio
async def test_should_return_404_when_contract_not_found(client: AsyncClient) -> None:
    """Ensure HTTP 404 when querying a non-existent contract ID."""
    non_existent_id = uuid4()
    resp = await client.get(f"/api/v1/contracts/{non_existent_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_should_list_contracts_with_filters_and_pagination(
    client: AsyncClient,
) -> None:
    """Verify listing contracts with query filtering and pagination."""
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "3.1", "name": "Marketing Operations", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    supplier_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supplier_id,
            name="Ad Agency Media",
            tax_id="55.666.777/0001-88",
        )
    )

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

    resp_list = await client.get("/api/v1/contracts?page=1&perPage=20")
    assert resp_list.status_code == 200
    contracts_payload = resp_list.json()
    assert "data" in contracts_payload
    assert "pagination" in contracts_payload
    assert "links" in contracts_payload
    assert contracts_payload["pagination"]["page"] == 1
    assert contracts_payload["pagination"]["perPage"] == 20
    assert any(c["id"] == contract_id for c in contracts_payload["data"])

    resp_filtered = await client.get(
        f"/api/v1/contracts?supplier_id={supplier_id}&page=1&perPage=10"
    )
    assert resp_filtered.status_code == 200
    filtered_payload = resp_filtered.json()
    assert all(c["supplier_id"] == str(supplier_id) for c in filtered_payload["data"])
    assert (
        filtered_payload["links"]["self"]
        == f"/api/v1/contracts?supplier_id={supplier_id}&page=1&perPage=10"
    )
