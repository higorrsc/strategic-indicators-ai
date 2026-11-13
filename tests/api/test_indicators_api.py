"""Integration tests for Strategic Indicators API endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container


@pytest.mark.asyncio
async def test_should_compute_period_indicators_happy_path(
    client: AsyncClient,
) -> None:
    """Verify indicators computation endpoint returns planned vs actual variance."""
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

    resp_indicators = await client.get("/api/v1/indicators/2026-03")
    assert resp_indicators.status_code == 200
    ind_data = resp_indicators.json()
    assert ind_data["period"] == "2026-03"
    assert ind_data["total_budgeted"] == "50000.00"
    assert ind_data["total_actual"] == "35000.00"
    assert ind_data["total_variance"] == "-15000.00"
    assert ind_data["indicators"][0]["status"] == "NORMAL"


@pytest.mark.asyncio
async def test_should_query_materiality_focus_across_dimensions_and_metrics(
    client: AsyncClient,
) -> None:
    """Verify materiality Pareto focus report across levels, metrics, and thresholds."""
    r1 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "10.0", "name": "Tech Corp", "parent_id": None},
    )
    r1_id = r1.json()["id"]

    c1_1 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "10.1", "name": "Cloud Operations", "parent_id": r1_id},
    )
    c1_1_id = c1_1.json()["id"]

    c1_2 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "10.2", "name": "Dev Engineering", "parent_id": r1_id},
    )
    c1_2_id = c1_2.json()["id"]

    r2 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "20.0", "name": "Ops Corp", "parent_id": None},
    )
    r2_id = r2.json()["id"]

    c2_1 = await client.post(
        "/api/v1/cost-centers",
        json={"code": "20.1", "name": "Facilities Ops", "parent_id": r2_id},
    )
    c2_1_id = c2_1.json()["id"]

    targets = [
        (c1_1_id, "10000.00"),
        (c1_2_id, "5000.00"),
        (c2_1_id, "5000.00"),
    ]
    for cid, amount in targets:
        await client.post(
            "/api/v1/budgets",
            json={
                "cost_center_id": cid,
                "period": "2026-04",
                "category": "OPEX",
                "amount": amount,
                "currency": "USD",
            },
        )

    acc_cloud = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.1.10", "name": "Cloud Infra Services"},
    )
    acc_cloud_id = acc_cloud.json()["id"]

    acc_soft = await client.post(
        "/api/v1/accounting-accounts",
        json={"code": "3.1.20", "name": "Software Subscriptions"},
    )
    acc_soft_id = acc_soft.json()["id"]

    supp_id = uuid4()
    container = get_container()
    await container.supplier_repo.add(
        Supplier(
            id=supp_id,
            name="Pareto Supplier Ltd",
            tax_id=f"PAR-{uuid4().hex[:6]}",
        )
    )
    contract_resp = await client.post(
        "/api/v1/contracts",
        json={
            "code": f"CTR-MAT-{uuid4().hex[:6]}",
            "supplier_id": str(supp_id),
            "title": "Multi-center multi-account contract",
            "default_allocations": [
                {"cost_center_id": c1_1_id, "percentage": "100.00"}
            ],
        },
    )
    assert contract_resp.status_code == 201
    contract_id = contract_resp.json()["id"]

    m_resp = await client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-04",
            "description": "April consolidated billing",
            "gross_amount": "24000.00",
            "currency": "USD",
            "allocation_override": [
                {
                    "cost_center_id": c1_1_id,
                    "percentage": "50.00",
                    "accounting_account_id": acc_cloud_id,
                },
                {
                    "cost_center_id": c1_1_id,
                    "percentage": "12.50",
                    "accounting_account_id": acc_soft_id,
                },
                {
                    "cost_center_id": c1_2_id,
                    "percentage": "25.00",
                    "accounting_account_id": acc_soft_id,
                },
                {
                    "cost_center_id": c2_1_id,
                    "percentage": "12.50",
                    "accounting_account_id": acc_cloud_id,
                },
            ],
        },
    )
    assert m_resp.status_code == 201
    m_id = m_resp.json()["id"]
    await client.post(f"/api/v1/measurements/{m_id}/approve")

    # Cost Center Level by Variance
    resp_cc_var = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus?level=cost_center&metric=variance"
    )
    assert resp_cc_var.status_code == 200
    data_cc_var = resp_cc_var.json()
    assert data_cc_var["aggregation_level"] == "cost_center"
    assert Decimal(str(data_cc_var["total_baseline_overrun"])) == Decimal("6000.00")
    assert data_cc_var["items"][0]["code"] == "10.1"
    assert data_cc_var["items"][0]["priority"] == "IMMEDIATE_ACTION"

    # Hierarchy Level by Spend
    resp_hier = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus?level=hierarchy&metric=spend"
    )
    assert resp_hier.status_code == 200
    data_hier = resp_hier.json()
    assert data_hier["aggregation_level"] == "hierarchy"
    assert data_hier["items"][0]["code"] == "10.0"
    assert Decimal(str(data_hier["items"][0]["actual_spent"])) == Decimal("21000.00")

    # Threshold Cutoff
    resp_cutoff = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus"
        "?level=cost_center&metric=variance&threshold_pct=80"
    )
    assert resp_cutoff.status_code == 200
    assert len(resp_cutoff.json()["items"]) == 1

    # Error cases
    resp_404 = await client.get(
        f"/api/v1/indicators/2026-04/materiality-focus"
        f"?level=accounting_account&cost_center_id={uuid4()}"
    )
    assert resp_404.status_code == 404
