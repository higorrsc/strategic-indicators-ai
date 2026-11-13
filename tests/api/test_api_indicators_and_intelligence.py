"""Integration tests for Indicators and Strategic Intelligence API endpoints."""

from __future__ import annotations

from decimal import Decimal
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


@pytest.mark.asyncio
async def test_should_query_materiality_focus_across_dimensions_and_metrics(
    client: AsyncClient,
) -> None:
    """Verify materiality Pareto focus report across levels, metrics, and thresholds."""
    # 1. Create hierarchy of cost centers:
    # 1.0 (Tech Parent) -> 1.1 (Cloud), 1.2 (Dev)
    # 2.0 (Ops Parent) -> 2.1 (Facilities)
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

    # 2. Set Budgets for period 2026-04:
    # 10.1 = 10,000
    # 10.2 = 5,000
    # 20.1 = 5,000
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

    # 3. Create Accounting Accounts
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

    # 4. Setup Supplier & Contract
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


    # 5. Submit & Approve Measurements for 2026-04
    # Spend breakdown on $24,000 gross:
    # c1_1 (cloud): 12,000 -> 50.00%
    # c1_1 (soft):   3,000 -> 12.50%
    # c1_2 (soft):   6,000 -> 25.00%
    # c2_1 (cloud):  3,000 -> 12.50%
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


    # TEST A: Cost Center Level by Variance (Default)
    resp_cc_var = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus?level=cost_center&metric=variance"
    )
    assert resp_cc_var.status_code == 200
    data_cc_var = resp_cc_var.json()
    assert data_cc_var["aggregation_level"] == "cost_center"
    assert data_cc_var["focus_metric"] == "variance"
    assert Decimal(str(data_cc_var["total_baseline_overrun"])) == Decimal("6000.00")
    # Top item must be 10.1 (5000 overrun / 6000 = 83.33%)
    item0 = data_cc_var["items"][0]
    item1 = data_cc_var["items"][1]
    assert item0["code"] == "10.1"
    assert Decimal(str(item0["share_of_total_pct"])) == Decimal("83.33")
    assert item0["priority"] == "IMMEDIATE_ACTION"
    # Second item must be 10.2 (1000 overrun / 6000 = 16.67%)
    assert item1["code"] == "10.2"
    assert Decimal(str(item1["share_of_total_pct"])) == Decimal("16.67")

    # TEST B: Hierarchy Level by Spend
    resp_hier = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus?level=hierarchy&metric=spend"
    )
    assert resp_hier.status_code == 200
    data_hier = resp_hier.json()
    assert data_hier["aggregation_level"] == "hierarchy"
    assert data_hier["focus_metric"] == "spend"
    # Root 10.0 spend = 21,000 (87.50%). Root 20.0 spend = 3,000 (12.50%)
    hier_top = data_hier["items"][0]
    assert hier_top["code"] == "10.0"
    assert Decimal(str(hier_top["actual_spent"])) == Decimal("21000.00")
    assert Decimal(str(hier_top["share_of_total_pct"])) == Decimal("87.50")
    assert hier_top["priority"] == "IMMEDIATE_ACTION"

    # TEST C: Accounting Account Level by Spend Globally
    resp_acc_spend = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus"
        "?level=accounting_account&metric=spend"
    )
    assert resp_acc_spend.status_code == 200
    data_acc_spend = resp_acc_spend.json()
    assert data_acc_spend["aggregation_level"] == "accounting_account"
    # Cloud: 12000 + 3000 = 15,000 (62.50%). Soft: 3000 + 6000 = 9,000 (37.50%)
    acc_top = data_acc_spend["items"][0]
    acc_second = data_acc_spend["items"][1]
    assert acc_top["code"] == "3.1.10"
    assert Decimal(str(acc_top["actual_spent"])) == Decimal("15000.00")
    assert Decimal(str(acc_top["share_of_total_pct"])) == Decimal("62.50")
    assert acc_second["code"] == "3.1.20"
    assert Decimal(str(acc_second["actual_spent"])) == Decimal("9000.00")

    # TEST D: Accounting Account Level Scoped to Cost Center by Variance
    resp_acc_scoped = await client.get(
        f"/api/v1/indicators/2026-04/materiality-focus"
        f"?level=accounting_account&cost_center_id={c1_1_id}&metric=variance"
    )
    assert resp_acc_scoped.status_code == 200
    data_acc_scoped = resp_acc_scoped.json()
    assert data_acc_scoped["cost_center_scope_id"] == c1_1_id
    scoped_overrun = Decimal(str(data_acc_scoped["total_baseline_overrun"]))
    assert scoped_overrun == Decimal("5000.00")
    # In c1_1: Cloud is 12000/15000 = 80%, Soft is 3000/15000 = 20%
    scoped_item0 = data_acc_scoped["items"][0]
    scoped_item1 = data_acc_scoped["items"][1]
    assert scoped_item0["code"] == "3.1.10"
    assert Decimal(str(scoped_item0["share_of_total_pct"])) == Decimal("80.00")
    assert scoped_item1["code"] == "3.1.20"
    assert Decimal(str(scoped_item1["share_of_total_pct"])) == Decimal("20.00")


    # TEST E: Threshold Cutoff Filtering
    resp_cutoff = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus"
        "?level=cost_center&metric=variance&threshold_pct=80"
    )
    assert resp_cutoff.status_code == 200
    data_cutoff = resp_cutoff.json()
    # Only 10.1 accounts for 83.33% >= 80%, so only 10.1 is returned
    assert len(data_cutoff["items"]) == 1
    assert data_cutoff["items"][0]["code"] == "10.1"

    # TEST F: Error Cases
    # Non-existent cost center -> 404
    resp_404 = await client.get(
        f"/api/v1/indicators/2026-04/materiality-focus"
        f"?level=accounting_account&cost_center_id={uuid4()}"
    )
    assert resp_404.status_code == 404

    # Invalid level enum -> 422
    resp_invalid_level = await client.get(
        "/api/v1/indicators/2026-04/materiality-focus?level=unknown_dimension"
    )
    assert resp_invalid_level.status_code == 422

