"""Step definitions for Strategic Budget Indicators BDD acceptance tests."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from src.allocation.domain.entities.supplier import Supplier
from src.presentation.dependencies import get_container

scenarios("../features/strategic_budget_indicators.feature")


@pytest.fixture
def bdd_context() -> dict[str, Any]:
    """Shared context dictionary across scenario steps."""
    return {}


# --- Scenario 1: Hierarchical Cost Center & Budget Aggregation ---


@given(parsers.parse('a root cost center with code "{code}" and name "{name}"'))
def create_root_cost_center(
    client: TestClient,
    bdd_context: dict[str, Any],
    code: str,
    name: str,
) -> None:
    """Create a root cost center via presentation endpoint."""
    resp = client.post(
        "/api/v1/cost-centers",
        json={"code": code, "name": name, "parent_id": None},
    )
    assert resp.status_code == 201
    bdd_context[f"cc_{code}"] = resp.json()["id"]


@given(
    parsers.parse(
        'a child cost center with code "{code}" and name "{name}" under "{parent_code}"'
    )
)
def create_child_cost_center(
    client: TestClient,
    bdd_context: dict[str, Any],
    code: str,
    name: str,
    parent_code: str,
) -> None:
    """Create a child cost center linked to parent."""
    parent_id = bdd_context[f"cc_{parent_code}"]
    resp = client.post(
        "/api/v1/cost-centers",
        json={"code": code, "name": name, "parent_id": parent_id},
    )
    assert resp.status_code == 201
    bdd_context[f"cc_{code}"] = resp.json()["id"]


@when(
    parsers.parse(
        "planned budget of {amount:f} is set for cost center "
        '"{code}" in period "{period}"'
    )
)
def set_cost_center_budget(
    client: TestClient,
    bdd_context: dict[str, Any],
    amount: float,
    code: str,
    period: str,
) -> None:
    """Register budget target for cost center."""
    cc_id = bdd_context[f"cc_{code}"]
    resp = client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": cc_id,
            "period": period,
            "category": "OPEX",
            "amount": f"{amount:.2f}",
            "currency": "USD",
        },
    )
    assert resp.status_code == 201


@then(
    parsers.parse(
        'the consolidated hierarchical budget for cost center "{code}" in '
        'period "{period}" is {expected_total:f}'
    )
)
def verify_consolidated_budget(
    client: TestClient,
    bdd_context: dict[str, Any],
    code: str,
    period: str,
    expected_total: float,
) -> None:
    """Verify aggregated budget total for cost center subtree."""
    cc_id = bdd_context[f"cc_{code}"]
    resp = client.get(f"/api/v1/cost-centers/{cc_id}/hierarchy-budget?period={period}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["consolidated_total"] == f"{expected_total:.2f}"


# --- Scenario 2: Contract Registration & Exact Penny Split ---


@given(parsers.parse('active cost centers "{c1}", "{c2}", and "{c3}"'))
def setup_three_cost_centers(
    client: TestClient,
    bdd_context: dict[str, Any],
    c1: str,
    c2: str,
    c3: str,
) -> None:
    """Register three active cost centers."""
    for code in (c1, c2, c3):
        resp = client.post(
            "/api/v1/cost-centers",
            json={"code": code, "name": f"Center {code}", "parent_id": None},
        )
        assert resp.status_code == 201
        bdd_context[f"cc_{code}"] = resp.json()["id"]


@given(
    parsers.parse(
        'a registered vendor contract "{contract_code}" with default split '
        "33.34%, 33.33%, and 33.33%"
    )
)
def register_contract_split(
    client: TestClient,
    bdd_context: dict[str, Any],
    contract_code: str,
) -> None:
    """Register a contract with three default allocation shares."""
    supplier_id = uuid4()
    container = get_container()
    asyncio.run(
        container.supplier_repo.add(
            Supplier(
                id=supplier_id,
                name="Vendor Corp",
                tax_id="00.111.222/0001-33",
            )
        )
    )

    cc1 = bdd_context["cc_1.1"]
    cc2 = bdd_context["cc_1.2"]
    cc3 = bdd_context["cc_1.3"]

    resp = client.post(
        "/api/v1/contracts",
        json={
            "code": contract_code,
            "supplier_id": str(supplier_id),
            "title": "Platform Infrastructure",
            "default_allocations": [
                {"cost_center_id": cc1, "percentage": "33.34"},
                {"cost_center_id": cc2, "percentage": "33.33"},
                {"cost_center_id": cc3, "percentage": "33.33"},
            ],
        },
    )
    assert resp.status_code == 201
    bdd_context["contract_id"] = resp.json()["id"]


@when(
    parsers.parse(
        "a measurement with gross amount {gross_amount:f} is submitted "
        'for period "{period}"'
    )
)
def submit_measurement_step(
    client: TestClient,
    bdd_context: dict[str, Any],
    gross_amount: float,
    period: str,
) -> None:
    """Submit a measurement expense."""
    contract_id = bdd_context["contract_id"]
    resp = client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": period,
            "description": "Monthly Invoice",
            "gross_amount": f"{gross_amount:.2f}",
            "currency": "USD",
        },
    )
    assert resp.status_code == 201
    bdd_context["measurement"] = resp.json()
    bdd_context["period"] = period


@then(parsers.parse('the measurement is in "{expected_state}" state'))
@then(parsers.parse('the measurement transitions to "{expected_state}" state'))
def verify_measurement_state(bdd_context: dict[str, Any], expected_state: str) -> None:
    """Check measurement state."""
    assert bdd_context["measurement"]["state"] == expected_state


@then(
    parsers.parse(
        "the allocation entries reconcile to exact amounts {a1:f}, {a2:f}, and {a3:f}"
    )
)
def verify_allocation_entries_amounts(
    bdd_context: dict[str, Any],
    a1: float,
    a2: float,
    a3: float,
) -> None:
    """Verify exact penny allocation values."""
    entries = bdd_context["measurement"]["entries"]
    amounts = [e["amount"] for e in entries]
    assert f"{a1:.2f}" in amounts
    assert f"{a2:.2f}" in amounts
    assert f"{a3:.2f}" in amounts


@when("the measurement is approved")
def approve_measurement_step(
    client: TestClient,
    bdd_context: dict[str, Any],
) -> None:
    """Approve submitted measurement."""
    m_id = bdd_context["measurement"]["id"]
    resp = client.post(f"/api/v1/measurements/{m_id}/approve")
    assert resp.status_code == 200
    bdd_context["measurement"] = resp.json()


# --- Scenario 3: Deterministic Budget Variance ---


@given(
    parsers.parse(
        'cost center "{code}" has a budget target of {budget:f} in period "{period}"'
    )
)
def setup_budget_target_for_indicators(
    client: TestClient,
    bdd_context: dict[str, Any],
    code: str,
    budget: float,
    period: str,
) -> None:
    """Ensure cost center exists and set budget target."""
    if f"cc_{code}" not in bdd_context:
        resp = client.post(
            "/api/v1/cost-centers",
            json={"code": code, "name": f"Center {code}", "parent_id": None},
        )
        assert resp.status_code == 201
        bdd_context[f"cc_{code}"] = resp.json()["id"]

    cc_id = bdd_context[f"cc_{code}"]
    resp_budget = client.post(
        "/api/v1/budgets",
        json={
            "cost_center_id": cc_id,
            "period": period,
            "category": "OPEX",
            "amount": f"{budget:.2f}",
            "currency": "USD",
        },
    )
    assert resp_budget.status_code == 201
    bdd_context["period"] = period


@given(
    parsers.parse(
        'approved allocation measurements totaling {actual:f} for period "{period}"'
    )
)
def setup_approved_measurement(
    client: TestClient,
    bdd_context: dict[str, Any],
    actual: float,
    period: str,
) -> None:
    """Create contract and approved measurement."""
    cc_id = bdd_context["cc_1.1"]
    supplier_id = uuid4()
    container = get_container()
    asyncio.run(
        container.supplier_repo.add(
            Supplier(
                id=supplier_id,
                name="Supplier BDD",
                tax_id="33.444.555/0001-66",
            )
        )
    )

    resp_c = client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-BDD-001",
            "supplier_id": str(supplier_id),
            "title": "BDD Contract",
            "default_allocations": [{"cost_center_id": cc_id, "percentage": "100.00"}],
        },
    )
    contract_id = resp_c.json()["id"]
    bdd_context["contract_id"] = contract_id

    resp_m = client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": period,
            "description": "Invoice",
            "gross_amount": f"{actual:.2f}",
            "currency": "USD",
        },
    )
    m_id = resp_m.json()["id"]
    client.post(f"/api/v1/measurements/{m_id}/approve")
    bdd_context["measurement_id"] = m_id


@when(parsers.parse('period indicators are computed for period "{period}"'))
def compute_indicators_step(
    client: TestClient,
    bdd_context: dict[str, Any],
    period: str,
) -> None:
    """Fetch period indicators."""
    resp = client.get(f"/api/v1/indicators/{period}")
    assert resp.status_code == 200
    bdd_context["indicators"] = resp.json()


@then(parsers.parse('cost center "{code}" has actual expenditure {expected_actual:f}'))
def verify_actual_expenditure(
    bdd_context: dict[str, Any],
    code: str,
    expected_actual: float,
) -> None:
    """Check actual allocated expenditure."""
    ind = next(
        i
        for i in bdd_context["indicators"]["indicators"]
        if i["cost_center_code"] == code
    )
    assert ind["actual_amount"] == f"{expected_actual:.2f}"


@then(parsers.parse("the variance is {variance:f} with execution rate {rate:f}%"))
def verify_variance_and_rate(
    bdd_context: dict[str, Any],
    variance: float,
    rate: float,
) -> None:
    """Check variance and execution rate."""
    ind = bdd_context["indicators"]["indicators"][0]
    assert ind["variance_amount"] == f"{variance:.2f}"
    assert ind["execution_rate"] == f"{rate:.2f}"


@then(parsers.parse('the indicator status is "{expected_status}"'))
def verify_indicator_status(bdd_context: dict[str, Any], expected_status: str) -> None:
    """Check indicator health status."""
    ind = bdd_context["indicators"]["indicators"][0]
    assert ind["status"] == expected_status


# --- Scenario 4: What-If Simulation ---


@given(
    parsers.parse(
        'cost center "{code}" with budget {budget:f} and actual baseline '
        "expenditure {actual:f}"
    )
)
def setup_simulation_baseline(
    client: TestClient,
    bdd_context: dict[str, Any],
    code: str,
    budget: float,
    actual: float,
) -> None:
    """Setup baseline for simulation."""
    period = "2026-03"
    setup_budget_target_for_indicators(client, bdd_context, code, budget, period)
    setup_approved_measurement(client, bdd_context, actual, period)


@when(
    parsers.parse(
        "a what-if scenario is simulated with {pct}% inflation on "
        'contract "{contract_code}"'
    )
)
def simulate_inflation_step(
    client: TestClient,
    bdd_context: dict[str, Any],
    pct: str,
    contract_code: str,
) -> None:
    """Simulate inflation scenario."""
    inflation_val = float(pct)
    contract_id = bdd_context["contract_id"]
    period = bdd_context["period"]
    resp = client.post(
        "/api/v1/scenarios/simulate",
        json={
            "name": f"{pct}% Inflation",
            "period": period,
            "contract_inflation": {contract_id: f"{inflation_val:.2f}"},
            "allocation_shifts": [],
        },
    )
    assert resp.status_code == 200
    bdd_context["simulation"] = resp.json()


@then(
    parsers.parse(
        'the simulated actual expenditure for cost center "{code}" becomes '
        "{simulated:f}"
    )
)
def verify_simulated_actual(
    bdd_context: dict[str, Any],
    code: str,
    simulated: float,
) -> None:
    """Check simulated actual amount."""
    impact = next(
        imp
        for imp in bdd_context["simulation"]["impacts"]
        if imp["cost_center_code"] == code
    )
    assert impact["simulated_actual"] == f"{simulated:.2f}"


@then("a new budget overrun is identified")
def verify_new_overrun(bdd_context: dict[str, Any]) -> None:
    """Check that new budget overrun was detected."""
    assert bdd_context["simulation"]["new_overruns_count"] >= 1
    assert any(imp["new_overrun"] for imp in bdd_context["simulation"]["impacts"])


# --- Scenario 5: Anomaly Detection & AI Executive Summary ---


@given(
    parsers.parse(
        "a contract with historical average allocation of {hist_pct}% "
        'to cost center "{code}"'
    )
)
def setup_historical_measurements(
    client: TestClient,
    bdd_context: dict[str, Any],
    hist_pct: str,
    code: str,
) -> None:
    """Create approved historical measurements establishing baseline."""
    hist_float = float(hist_pct)
    # Ensure cost center
    if f"cc_{code}" not in bdd_context:
        resp = client.post(
            "/api/v1/cost-centers",
            json={"code": code, "name": f"Center {code}", "parent_id": None},
        )
        bdd_context[f"cc_{code}"] = resp.json()["id"]

    # Also second center
    resp_other = client.post(
        "/api/v1/cost-centers",
        json={"code": "9.9", "name": "Other Center", "parent_id": None},
    )
    bdd_context["cc_9.9"] = resp_other.json()["id"]

    cc_id = bdd_context[f"cc_{code}"]
    cc_other = bdd_context["cc_9.9"]

    supplier_id = uuid4()
    container = get_container()
    asyncio.run(
        container.supplier_repo.add(
            Supplier(
                id=supplier_id,
                name="Anomaly Supplier",
                tax_id="88.777.666/0001-55",
            )
        )
    )

    resp_c = client.post(
        "/api/v1/contracts",
        json={
            "code": "CT-ANOMALY-001",
            "supplier_id": str(supplier_id),
            "title": "Anomaly Contract",
            "default_allocations": [
                {"cost_center_id": cc_id, "percentage": f"{hist_float:.2f}"},
                {
                    "cost_center_id": cc_other,
                    "percentage": f"{100 - hist_float:.2f}",
                },
            ],
        },
    )
    contract_id = resp_c.json()["id"]
    bdd_context["contract_id"] = contract_id

    # Create 2 approved past measurements
    for period in ("2026-01", "2026-02"):
        resp_m = client.post(
            "/api/v1/measurements",
            json={
                "contract_id": contract_id,
                "period": period,
                "description": f"Invoice {period}",
                "gross_amount": "10000.00",
                "currency": "USD",
            },
        )
        m_id = resp_m.json()["id"]
        client.post(f"/api/v1/measurements/{m_id}/approve")


@when(
    parsers.parse(
        "a new measurement is submitted with a {curr_pct}% allocation share "
        'to cost center "{code}"'
    )
)
def submit_spiked_measurement(
    client: TestClient,
    bdd_context: dict[str, Any],
    curr_pct: str,
    code: str,
) -> None:
    """Submit measurement with spiked allocation override."""
    curr_float = float(curr_pct)
    cc_id = bdd_context[f"cc_{code}"]
    cc_other = bdd_context["cc_9.9"]
    contract_id = bdd_context["contract_id"]

    resp = client.post(
        "/api/v1/measurements",
        json={
            "contract_id": contract_id,
            "period": "2026-03",
            "description": "Spike Invoice March",
            "gross_amount": "10000.00",
            "currency": "USD",
            "allocation_override": [
                {"cost_center_id": cc_id, "percentage": f"{curr_float:.2f}"},
                {
                    "cost_center_id": cc_other,
                    "percentage": f"{100 - curr_float:.2f}",
                },
            ],
        },
    )
    assert resp.status_code == 201
    bdd_context["measurement"] = resp.json()


@then(
    parsers.parse(
        'the system flags an "{anomaly_type}" anomaly with "{severity}" severity'
    )
)
def verify_anomaly_detected(
    client: TestClient,
    bdd_context: dict[str, Any],
    anomaly_type: str,
    severity: str,
) -> None:
    """Verify anomaly detection endpoint detects the spike."""
    m_id = bdd_context["measurement"]["id"]
    resp = client.get(f"/api/v1/intelligence/anomalies/{m_id}")
    assert resp.status_code == 200
    anomalies = resp.json()
    assert len(anomalies) >= 1
    match = next(a for a in anomalies if a["anomaly_type"] == anomaly_type)
    assert match["severity"] == severity


@when("an executive summary is generated for the period")
def generate_executive_summary_bdd(
    client: TestClient,
    bdd_context: dict[str, Any],
) -> None:
    """Generate executive summary for period."""
    resp = client.get("/api/v1/intelligence/executive-summary?period=2026-03")
    assert resp.status_code == 200
    bdd_context["executive_summary"] = resp.json()


@then("the summary report identifies root causes and strategic recommendations")
def verify_executive_summary_contents(bdd_context: dict[str, Any]) -> None:
    """Verify that executive summary contains actionable insights."""
    report = bdd_context["executive_summary"]
    assert len(report["root_causes"]) >= 1
    assert len(report["strategic_recommendations"]) >= 1
