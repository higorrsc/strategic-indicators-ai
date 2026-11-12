"""Integration tests for Budgeting API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_should_create_root_and_child_cost_centers(
    client: AsyncClient,
) -> None:
    """Verify creation of hierarchical cost centers via HTTP."""
    # Create root cost center
    root_payload = {
        "code": "1.0",
        "name": "Executive Board",
        "parent_id": None,
    }
    resp_root = await client.post("/api/v1/cost-centers", json=root_payload)
    assert resp_root.status_code == 201
    root_data = resp_root.json()
    assert root_data["code"] == "1.0"
    assert root_data["parent_id"] is None
    root_id = root_data["id"]

    # Create child cost center
    child_payload = {
        "code": "1.1",
        "name": "Information Technology",
        "parent_id": root_id,
    }
    resp_child = await client.post("/api/v1/cost-centers", json=child_payload)
    assert resp_child.status_code == 201
    child_data = resp_child.json()
    assert child_data["code"] == "1.1"
    assert child_data["parent_id"] == root_id


@pytest.mark.asyncio
async def test_should_reject_duplicate_cost_center_code(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 409 Conflict when submitting duplicate cost center code."""
    payload = {"code": "1.0", "name": "Corporate", "parent_id": None}
    resp1 = await client.post("/api/v1/cost-centers", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/cost-centers", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_should_reject_invalid_cost_center_syntax(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 400 Bad Request when cost center code has invalid format."""
    payload = {"code": "INVALID-CODE--", "name": "Invalid", "parent_id": None}
    resp = await client.post("/api/v1/cost-centers", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_should_return_404_for_non_existent_cost_center(
    client: AsyncClient,
) -> None:
    """Ensure HTTP 404 Not Found when cost center ID does not exist."""
    resp = await client.get(f"/api/v1/cost-centers/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_should_set_budget_and_aggregate_hierarchy(
    client: AsyncClient,
) -> None:
    """Verify setting budget targets and retrieving aggregated hierarchical budget."""
    # Create parent and child centers
    resp_parent = await client.post(
        "/api/v1/cost-centers",
        json={"code": "2.0", "name": "Operations", "parent_id": None},
    )
    parent_id = resp_parent.json()["id"]

    resp_child = await client.post(
        "/api/v1/cost-centers",
        json={"code": "2.1", "name": "Logistics", "parent_id": parent_id},
    )
    child_id = resp_child.json()["id"]

    # Set budget on parent ($20,000) and child ($30,000)
    await client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": parent_id,
            "period": "2026-03",
            "category": "OPEX",
            "amount": "20000.00",
            "currency": "USD",
        },
    )
    await client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": child_id,
            "period": "2026-03",
            "category": "OPEX",
            "amount": "30000.00",
            "currency": "USD",
        },
    )

    # Query aggregated budget for parent
    resp_hierarchy = await client.get(
        f"/api/v1/cost-centers/{parent_id}/hierarchy-budget?period=2026-03"
    )
    assert resp_hierarchy.status_code == 200
    hierarchy_data = resp_hierarchy.json()
    assert hierarchy_data["direct_total"] == "20000.00"
    assert hierarchy_data["consolidated_total"] == "50000.00"


@pytest.mark.asyncio
async def test_should_reject_negative_budget_target(
    client: AsyncClient,
) -> None:
    """Ensure validation error when submitting negative budget amount."""
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "3.0", "name": "Finance", "parent_id": None},
    )
    cc_id = resp_cc.json()["id"]

    resp_budget = await client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": cc_id,
            "period": "2026-03",
            "category": "OPEX",
            "amount": "-500.00",
            "currency": "USD",
        },
    )
    assert resp_budget.status_code == 422
