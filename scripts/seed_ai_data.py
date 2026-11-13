"""Seed script populating realistic enterprise financial data.

This script seeds:
1. Hierarchical cost centers (Board -> IT [Cloud, Software], Operations, Marketing).
2. Hierarchical chart of accounts (Accounting Accounts).
3. Historical and current budget targets across multiple fiscal periods.
4. Vendor contracts with default allocation shares and accounting account mappings.
5. Historical measurements establishing baseline allocation patterns and
   account breakdown.
6. Target period measurements with intentional budget overruns and shift anomalies.
7. Verification of cost center accounting account breakdown.
8. Execution of the AI Executive Summary Use Case to verify agent analysis.
"""

from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from uuid import UUID, uuid4

from src.allocation.application.use_cases.get_cost_center_accounting_breakdown import (
    GetCostCenterAccountingBreakdownUseCase,
)
from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import Measurement
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.indicators.application.use_cases.compute_period_indicators import (
    ComputePeriodIndicatorsUseCase,
)
from src.intelligence.application.dto import ExecutiveSummaryDTO
from src.intelligence.application.use_cases.analyze_allocation_anomalies import (
    AnalyzeAllocationAnomaliesUseCase,
)
from src.intelligence.application.use_cases.generate_executive_summary import (
    GenerateExecutiveSummaryUseCase,
)
from src.presentation.dependencies import DependencyContainer
from src.shared.config.settings import get_settings
from src.shared.domain.value_objects import (
    AccountCode,
    CostCenterCode,
    Money,
    Percentage,
    Period,
)
from src.shared.infrastructure.database.base import Base


async def seed_data(
    container: DependencyContainer,
    clean: bool = False,
    run_ai: bool = True,
    target_period_str: str = "2026-03",
) -> ExecutiveSummaryDTO | None:
    """Populate enterprise financial data and optionally invoke the AI agent.

    Args:
        container: Wired DependencyContainer instance.
        clean: Whether to reset database tables before seeding.
        run_ai: Whether to run the AI Executive Summary use case after seeding.
        target_period_str: Target period for the financial anomaly analysis.

    Returns:
        ExecutiveSummaryDTO | None: Generated executive summary if run_ai is True.
    """
    target_period = Period.from_string(target_period_str)
    period_jan = Period.from_string("2026-01")
    period_feb = Period.from_string("2026-02")

    if clean and container.engine is not None:
        print("🧹 Cleaning database tables...")
        async with container.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables recreated.")

    print("\n🏢 Step 1: Seeding Cost Centers Hierarchy...")
    # 1.0 Executive Board / Corporate (Root)
    cc_corp = await _get_or_create_cost_center(
        container, "1.0", "Executive Board & Corporate", parent_id=None
    )
    # 1.1 IT
    cc_it = await _get_or_create_cost_center(
        container, "1.1", "Information Technology", parent_id=cc_corp.id
    )
    # 1.1.1 Cloud Infrastructure
    cc_cloud = await _get_or_create_cost_center(
        container, "1.1.1", "Cloud Infrastructure", parent_id=cc_it.id
    )
    # 1.1.2 Software Engineering
    cc_software = await _get_or_create_cost_center(
        container, "1.1.2", "Software Engineering", parent_id=cc_it.id
    )
    # 1.2 Operations & Logistics
    cc_ops = await _get_or_create_cost_center(
        container, "1.2", "Operations & Logistics", parent_id=cc_corp.id
    )
    # 1.3 Marketing & Growth
    cc_mkt = await _get_or_create_cost_center(
        container, "1.3", "Marketing & Growth", parent_id=cc_corp.id
    )
    print("  - Created/Verified Cost Centers: 1.0, 1.1, 1.1.1, 1.1.2, 1.2, 1.3")

    print("\n📚 Step 2: Seeding Chart of Accounts (Accounting Accounts)...")
    acc_cloud = await _get_or_create_accounting_account(
        container,
        code_str="3.1.01",
        name="Infraestrutura Cloud & Hosting",
        description="Serviços de computação, armazenamento e instâncias em nuvem",
    )
    acc_software = await _get_or_create_accounting_account(
        container,
        code_str="3.1.02",
        name="Licenciamento de Software & Ferramentas SaaS",
        description="Licenças de software para engenharia, ferramentas CI/CD e SaaS",
    )
    acc_consulting = await _get_or_create_accounting_account(
        container,
        code_str="3.1.03",
        name="Consultoria Técnica & Serviços Especializados",
        description="Serviços profissionais e consultoria especializada de TI",
    )
    acc_logistics = await _get_or_create_accounting_account(
        container,
        code_str="3.2.01",
        name="Serviços de Logística e Fretes",
        description="Distribuição regional, frota dedicada e fretes operacionais",
    )
    acc_marketing = await _get_or_create_accounting_account(
        container,
        code_str="3.3.01",
        name="Publicidade, Campanhas e Mídia",
        description="Veiculação de mídia digital e publicidade de crescimento",
    )
    print(
        "  - Created/Verified Accounting Accounts: "
        "3.1.01, 3.1.02, 3.1.03, 3.2.01, 3.3.01"
    )

    print("\n💰 Step 3: Seeding Budget Targets...")
    budget_specs = [
        # Cloud: $100,000 / month
        (cc_cloud.id, period_jan, "100000.00"),
        (cc_cloud.id, period_feb, "100000.00"),
        (cc_cloud.id, target_period, "100000.00"),
        # Software: $60,000 / month
        (cc_software.id, period_jan, "60000.00"),
        (cc_software.id, period_feb, "60000.00"),
        (cc_software.id, target_period, "60000.00"),
        # Operations: $80,000 / month
        (cc_ops.id, period_jan, "80000.00"),
        (cc_ops.id, period_feb, "80000.00"),
        (cc_ops.id, target_period, "80000.00"),
        # Marketing: $40,000 / month
        (cc_mkt.id, period_jan, "40000.00"),
        (cc_mkt.id, period_feb, "40000.00"),
        (cc_mkt.id, target_period, "40000.00"),
    ]
    for cc_id, per, amount_str in budget_specs:
        existing = await container.budget_repo.get_by_cost_center_and_period(cc_id, per)
        if not existing:
            target = BudgetTarget(
                id=uuid4(),
                cost_center_id=cc_id,
                period=per,
                category="OPEX",
                amount=Money(Decimal(amount_str)),
            )
            await container.budget_repo.add(target)
    print(f"  - Configured budget targets across {len(budget_specs)} slots.")

    print("\n🤝 Step 4: Seeding Suppliers & Vendor Contracts...")
    # Supplier 1: AWS
    sp_aws = await _get_or_create_supplier(
        container, "Amazon Web Services Inc.", "12.345.678/0001-90"
    )
    # Supplier 2: Global Logistics
    sp_log = await _get_or_create_supplier(
        container, "Global Logistics Partners", "98.765.432/0001-10"
    )
    # Supplier 3: Acme Creative Studio
    sp_mkt = await _get_or_create_supplier(
        container, "Acme Creative Studio", "44.555.666/0001-22"
    )
    # Supplier 4: TechConsult Architecture Partners
    sp_consult = await _get_or_create_supplier(
        container, "TechConsult Architecture Partners", "55.666.777/0001-33"
    )

    # Contracts
    ct_aws = await _get_or_create_contract(
        container=container,
        code="CT-AWS-2026",
        supplier_id=sp_aws.id,
        title="Enterprise Cloud Hosting & Compute Services",
        default_allocations=[
            AllocationShare(
                cost_center_id=cc_cloud.id,
                percentage=Percentage.from_number(60.0),
                accounting_account_id=acc_cloud.id,
            ),
            AllocationShare(
                cost_center_id=cc_software.id,
                percentage=Percentage.from_number(40.0),
                accounting_account_id=acc_software.id,
            ),
        ],
    )

    ct_log = await _get_or_create_contract(
        container=container,
        code="CT-LOG-2026",
        supplier_id=sp_log.id,
        title="Fleet & Warehouse Regional Distribution",
        default_allocations=[
            AllocationShare(
                cost_center_id=cc_ops.id,
                percentage=Percentage.from_number(100.0),
                accounting_account_id=acc_logistics.id,
            ),
        ],
    )

    ct_mkt = await _get_or_create_contract(
        container=container,
        code="CT-MKT-2026",
        supplier_id=sp_mkt.id,
        title="Omnichannel Growth & Media Campaigns",
        default_allocations=[
            AllocationShare(
                cost_center_id=cc_mkt.id,
                percentage=Percentage.from_number(100.0),
                accounting_account_id=acc_marketing.id,
            ),
        ],
    )

    ct_consult = await _get_or_create_contract(
        container=container,
        code="CT-CONSULT-2026",
        supplier_id=sp_consult.id,
        title="Specialized Software Architecture & DevOps Consulting",
        default_allocations=[
            AllocationShare(
                cost_center_id=cc_software.id,
                percentage=Percentage.from_number(100.0),
                accounting_account_id=acc_consulting.id,
            ),
        ],
    )
    print(
        "  - Registered Contracts: "
        "CT-AWS-2026, CT-LOG-2026, CT-MKT-2026, CT-CONSULT-2026"
    )

    print("\n📊 Step 5: Seeding Historical & Current Period Measurements...")
    # Baseline 2026-01
    await _create_and_approve_measurement(
        container=container,
        contract=ct_aws,
        period=period_jan,
        gross_amount=Money(Decimal("85000.00")),
        description="January Cloud Infrastructure Invoice",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_consult,
        period=period_jan,
        gross_amount=Money(Decimal("15000.00")),
        description="January Software Architecture Advisory",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_log,
        period=period_jan,
        gross_amount=Money(Decimal("70000.00")),
        description="January Distribution Logistics",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_mkt,
        period=period_jan,
        gross_amount=Money(Decimal("32000.00")),
        description="January Brand Awareness Campaign",
    )

    # Baseline 2026-02
    await _create_and_approve_measurement(
        container=container,
        contract=ct_aws,
        period=period_feb,
        gross_amount=Money(Decimal("88000.00")),
        description="February Cloud Infrastructure Invoice",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_consult,
        period=period_feb,
        gross_amount=Money(Decimal("15000.00")),
        description="February Cloud Migration Consulting",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_log,
        period=period_feb,
        gross_amount=Money(Decimal("74000.00")),
        description="February Distribution Logistics",
    )
    await _create_and_approve_measurement(
        container=container,
        contract=ct_mkt,
        period=period_feb,
        gross_amount=Money(Decimal("36000.00")),
        description="February Lead Generation Campaign",
    )

    # Target Period 2026-03 (Engineered Scenario for AI Agent!)
    # 1. AWS Overrun + Abrupt Shift:
    # Baseline was 60% Cloud, 40% Software.
    # Gross amount surges to $130,000.00.
    # Allocation override: 90% Cloud ($117k vs $100k) & 10% Software ($13k).
    # Jump from 60% -> 90% is +30% (Threshold: 25% -> Anomaly Triggered!).
    aws_override = [
        AllocationShare(
            cost_center_id=cc_cloud.id,
            percentage=Percentage.from_number(90.0),
            accounting_account_id=acc_cloud.id,
        ),
        AllocationShare(
            cost_center_id=cc_software.id,
            percentage=Percentage.from_number(10.0),
            accounting_account_id=acc_software.id,
        ),
    ]
    await _create_and_approve_measurement(
        container=container,
        contract=ct_aws,
        period=target_period,
        gross_amount=Money(Decimal("130000.00")),
        description="March Cloud Surge (Overrun & Shift Anomaly)",
        allocation_override=aws_override,
    )

    # 2. Marketing Overrun:
    # Gross amount $43,000.00 (Exceeds $40k budget -> 107.5% Critical Overrun)
    await _create_and_approve_measurement(
        container=container,
        contract=ct_mkt,
        period=target_period,
        gross_amount=Money(Decimal("43000.00")),
        description="March Product Launch Media Spend",
    )

    # 3. Operations Healthy:
    # Gross amount $72,000.00 (Within $80k budget -> 90% Normal)
    await _create_and_approve_measurement(
        container=container,
        contract=ct_log,
        period=target_period,
        gross_amount=Money(Decimal("72000.00")),
        description="March Routine Transport & Warehouse",
    )
    print("  - Successfully seeded measurements across 2026-01, 2026-02, and 2026-03.")

    print("\n📑 Step 6: Verifying Cost Center Accounting Breakdown...")
    breakdown_uc = GetCostCenterAccountingBreakdownUseCase(
        measurement_repository=container.measurement_repo,
        accounting_account_repository=container.accounting_account_repo,
    )
    breakdown_jan_software = await breakdown_uc.execute(cc_software.id, "2026-01")
    print(f"  - Cost Center 1.1.2 ({cc_software.name}) Period 2026-01 Breakdown:")
    for acc in breakdown_jan_software.accounts:
        print(
            f"    • [{acc.account_code}] {acc.account_name}: "
            f"${acc.spent_amount} ({acc.share_pct}%)"
        )

    breakdown_mar_cloud = await breakdown_uc.execute(cc_cloud.id, target_period_str)
    print(
        f"  - Cost Center 1.1.1 ({cc_cloud.name}) Period {target_period_str} Breakdown:"
    )
    for acc in breakdown_mar_cloud.accounts:
        print(
            f"    • [{acc.account_code}] {acc.account_name}: "
            f"${acc.spent_amount} ({acc.share_pct}%)"
        )

    summary_result: ExecutiveSummaryDTO | None = None
    if run_ai:
        print(f"\n🧠 Step 7: Executing AI Executive Summary for {target_period}...")
        indicators_uc = ComputePeriodIndicatorsUseCase(
            cost_center_repository=container.cost_center_repo,
            budget_repository=container.budget_repo,
            measurement_repository=container.measurement_repo,
        )
        anomalies_uc = AnalyzeAllocationAnomaliesUseCase(
            measurement_repository=container.measurement_repo,
            indicators_use_case=indicators_uc,
        )
        summary_uc = GenerateExecutiveSummaryUseCase(
            indicators_use_case=indicators_uc,
            anomalies_use_case=anomalies_uc,
            ai_port=container.ai_port,
            settings=container.settings,
        )
        summary_result = await summary_uc.execute(target_period)
        _print_executive_briefing(summary_result)

    return summary_result


async def _get_or_create_cost_center(
    container: DependencyContainer,
    code_str: str,
    name: str,
    parent_id: UUID | None,
) -> CostCenter:
    code = CostCenterCode(code_str)
    existing = await container.cost_center_repo.get_by_code(code)
    if existing:
        return existing
    cc = CostCenter(id=uuid4(), code=code, name=name, parent_id=parent_id)
    await container.cost_center_repo.add(cc)
    return cc


async def _get_or_create_accounting_account(
    container: DependencyContainer,
    code_str: str,
    name: str,
    description: str = "",
) -> AccountingAccount:
    code = AccountCode(code_str)
    existing = await container.accounting_account_repo.get_by_code(code)
    if existing:
        return existing
    account = AccountingAccount(
        id=uuid4(),
        code=code,
        name=name,
        description=description,
    )
    await container.accounting_account_repo.save(account)
    return account


async def _get_or_create_supplier(
    container: DependencyContainer, name: str, tax_id: str
) -> Supplier:
    all_suppliers = await container.supplier_repo.list_all()
    for s in all_suppliers:
        if s.tax_id == tax_id or s.name == name:
            return s
    sp = Supplier(id=uuid4(), name=name, tax_id=tax_id)
    await container.supplier_repo.add(sp)
    return sp


async def _get_or_create_contract(
    container: DependencyContainer,
    code: str,
    supplier_id: UUID,
    title: str,
    default_allocations: list[AllocationShare],
) -> Contract:
    existing = await container.contract_repo.get_by_code(code)
    if existing:
        return existing
    ct = Contract(
        id=uuid4(),
        code=code,
        supplier_id=supplier_id,
        title=title,
        default_allocations=default_allocations,
    )
    await container.contract_repo.add(ct)
    return ct


async def _create_and_approve_measurement(
    container: DependencyContainer,
    contract: Contract,
    period: Period,
    gross_amount: Money,
    description: str,
    allocation_override: list[AllocationShare] | None = None,
) -> Measurement:
    existing_list = await container.measurement_repo.list_by_contract(contract.id)
    for m in existing_list:
        if m.period == period and m.description == description:
            return m

    shares = allocation_override or contract.default_allocations
    entries = ExactPennyAllocator.allocate(
        gross_amount=gross_amount,
        shares=shares,
    )
    measurement = Measurement(
        id=uuid4(),
        contract_id=contract.id,
        period=period,
        description=description,
        gross_amount=gross_amount,
        entries=entries,
    )
    measurement.submit()
    measurement.approve()
    await container.measurement_repo.add(measurement)
    return measurement


def _print_executive_briefing(summary: ExecutiveSummaryDTO) -> None:
    """Print an executive briefing to stdout."""
    status_icon = "🚨" if summary.financial_health_status == "CRITICAL" else "⚠️"
    print("\n" + "=" * 78)
    print(
        f" {status_icon} STRATEGIC FINANCIAL EXECUTIVE BRIEFING "
        f"— PERIOD {summary.period}"
    )
    print("=" * 78)
    print(f"\n[Financial Health Status]: {summary.financial_health_status}")
    print(f"[AI Provider]: {summary.ai_provider} (Fallback: {summary.is_fallback})")

    print("\n[Executive Synthesis]:")
    print(f"  {summary.executive_summary}")

    print("\n[Identified Root Causes]:")
    for idx, rc in enumerate(summary.root_causes, 1):
        print(f"  {idx}. {rc}")

    print("\n[Strategic Action Recommendations]:")
    for idx, rec in enumerate(summary.strategic_recommendations, 1):
        print(f"  {idx}. {rec}")

    print("\n[Detected Allocation Anomalies]:")
    if summary.anomalies:
        for idx, a in enumerate(summary.anomalies, 1):
            print(
                f"  {idx}. [{a.anomaly_type}] Cost Center: "
                f"{a.cost_center_id} — {a.description}"
            )
    else:
        print("  None detected.")

    print("\n[Planned vs. Actual Indicators Summary]:")
    print(
        f"  Total Budgeted: ${summary.indicators_summary.total_budgeted} | "
        f"Total Actual: ${summary.indicators_summary.total_actual} | "
        f"Net Variance: ${summary.indicators_summary.total_variance}"
    )
    print("  " + "-" * 74)
    print(
        f"  {'Cost Center':<14} | {'Budgeted':<14} | {'Actual':<14} | "
        f"{'Rate':<8} | {'Status'}"
    )
    print("  " + "-" * 74)
    for ind in summary.indicators_summary.indicators:
        print(
            f"  {ind.cost_center_code:<14} | "
            f"${ind.budgeted_amount:<13} | "
            f"${ind.actual_amount:<13} | "
            f"{ind.execution_rate:>6.1f}% | "
            f"{ind.status}"
        )
    print("=" * 78 + "\n")


async def main() -> None:
    """CLI entrypoint for data seeding."""
    parser = argparse.ArgumentParser(
        description="Seed financial test data for AI Agent analysis."
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database connection URL (defaults to Settings.DATABASE_URL).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Reset and recreate database tables before seeding.",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip running the AI Executive Summary use case.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="2026-03",
        help="Fiscal period for anomaly evaluation (default: '2026-03').",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQL logging.",
    )
    args = parser.parse_args()

    settings = get_settings()
    url = args.database_url or settings.DATABASE_URL

    container = DependencyContainer()
    print(f"🔌 Connecting to database: {url}")
    await container.init_database(database_url=url, echo=args.echo)

    try:
        await seed_data(
            container=container,
            clean=args.clean,
            run_ai=not args.no_ai,
            target_period_str=args.period,
        )
    finally:
        await container.close_database()
        print("🔒 Database connection pool closed.")


if __name__ == "__main__":
    asyncio.run(main())
