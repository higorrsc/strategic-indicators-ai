"""Integration tests for Accounting Accounts and Cost Center Breakdown API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_register_and_list_accounting_accounts_with_pagination(
    client: AsyncClient,
) -> None:
    """Verify registration and paginated listing of accounting accounts."""
    resp1 = await client.post(
        "/api/v1/accounting-accounts",
        json={
            "code": "3.1.01",
            "name": "Software SaaS",
            "description": "Cloud SaaS tool subscriptions",
        },
    )
    assert resp1.status_code == 201
    account1_data = resp1.json()
    assert account1_data["code"] == "3.1.01"
    assert account1_data["name"] == "Software SaaS"
    assert account1_data["is_active"] is True

    resp2 = await client.post(
        "/api/v1/accounting-accounts",
        json={
            "code": "3.1.02",
            "name": "Cloud Infrastructure",
            "description": "Compute and Storage",
        },
    )
    assert resp2.status_code == 201

    # List with pagination
    list_resp = await client.get("/api/v1/accounting-accounts?page=1&perPage=1")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert "data" in body
    assert "pagination" in body
    assert "links" in body
    assert len(body["data"]) == 1
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["perPage"] == 1
    assert body["pagination"]["totalItems"] >= 2


@pytest.mark.asyncio
async def test_should_reject_duplicate_accounting_account_code(
    client: AsyncClient,
) -> None:
    """Verify duplicate account code registration returns 409 Conflict."""
    await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.2.01", "name": "Hardware Server"},
    )

    dup_resp = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.2.01", "name": "Duplicate Server"},
    )
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["detail"]


@pytest.mark.asyncio
async def test_should_reject_invalid_accounting_account_code(
    client: AsyncClient,
) -> None:
    """Verify invalid account code syntax returns 400 Bad Request."""
    resp = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3..1", "name": "Malformed Syntax"},
    )
    assert resp.status_code == 400
    assert "invalid hierarchical syntax" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_should_submit_measurement_with_accounting_account_and_query_breakdown(
    client: AsyncClient,
) -> None:
    """Verify measurement submission with account and querying breakdown."""
    # 1. Create Cost Center
    resp_cc = await client.post(
        "/api/v1/cost-centers",
        json={"code": "1.10", "name": "Engineering Operations"},
    )
    assert resp_cc.status_code == 201
    cost_center_id = resp_cc.json()["id"]

    # 2. Register Accounting Accounts
    resp_acc1 = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.5.01", "name": "CI/CD Pipeline Compute"},
    )
    assert resp_acc1.status_code == 201
    acc1_id = resp_acc1.json()["id"]

    resp_acc2 = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.5.02", "name": "Observability & APM"},
    )
    assert resp_acc2.status_code == 201
    acc2_id = resp_acc2.json()["id"]

    # 3. Create Supplier & Contract
    supplier_id = uuid4()
    supplier = Supplier(
        id=supplier_id,
        name="DevOps Supplier",
        tax_id="44.555.666/0001-77",
    )
    container = get_container()
    await container.supplier_repo.add(supplier)

    contract_resp = await client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-DEVOPS-2026",
            "supplier_id": str(supplier_id),
            "title": "DevOps Tooling",
            "default_allocations": [
                {
                    "cost_center_id": cost_center_id,
                    "percentage": "100.00",
                    "accounting_account_id": acc1_id,
                }
            ],
        },
    )
    assert contract_resp.status_code == 201
    contract_id = contract_resp.json()["id"]

    # 4. Submit Measurement ($10,000) split between two accounting accounts
    meas_resp = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-03",
            "description": "March DevOps Infrastructure",
            "gross_amount": "10000.00",
            "currency": "USD",
            "allocation_override": [
                {
                    "cost_center_id": cost_center_id,
                    "percentage": "70.00",
                    "accounting_account_id": acc1_id,
                },
                {
                    "cost_center_id": cost_center_id,
                    "percentage": "30.00",
                    "accounting_account_id": acc2_id,
                },
            ],
        },
    )
    assert meas_resp.status_code == 201
    measurement_id = meas_resp.json()["id"]

    # 5. Approve Measurement
    appr_resp = await client.post(f"/api/v1/measurements/{measurement_id}/approve")
    assert appr_resp.status_code == 200
    assert appr_resp.json()["state"] == "APPROVED"

    # 6. Query Cost Center Accounting Breakdown
    breakdown_resp = await client.get(
        f"/api/v1/cost-centers/{cost_center_id}/accounting-breakdown?period=2026-03"
    )
    assert breakdown_resp.status_code == 200
    breakdown = breakdown_resp.json()
    assert breakdown["cost_center_id"] == cost_center_id
    assert breakdown["period"] == "2026-03"
    assert float(breakdown["total_spent"]) == 10000.00
    assert len(breakdown["accounts"]) == 2

    top_account = breakdown["accounts"][0]
    assert top_account["accounting_account_id"] == acc1_id
    assert top_account["account_code"] == "3.5.01"
    assert top_account["account_name"] == "CI/CD Pipeline Compute"
    assert float(top_account["spent_amount"]) == 7000.00
    assert float(top_account["share_pct"]) == 70.00

    second_account = breakdown["accounts"][1]
    assert second_account["accounting_account_id"] == acc2_id
    assert second_account["account_code"] == "3.5.02"
    assert float(second_account["spent_amount"]) == 3000.00
    assert float(second_account["share_pct"]) == 30.00


@pytest.mark.asyncio
async def test_should_reject_invalid_period_syntax_for_breakdown(
    client: AsyncClient,
) -> None:
    """Verify invalid period syntax returns 422 Unprocessable Entity."""
    cc_id = uuid4()
    resp = await client.get(
        f"/api/v1/cost-centers/{cc_id}/accounting-breakdown?period=invalid-period"
    )
    assert resp.status_code == 422
