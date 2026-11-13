"""Use case for generating Pareto materiality and effort prioritization reports."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.indicators.application.dto import (
    GenerateMaterialImpactQuery,
    MaterialImpactReportDTO,
    MaterialityItemDTO,
)
from src.indicators.domain.models import MaterialityCandidate
from src.indicators.domain.services.materiality_analyzer import (
    MaterialityAnalyzer,
)
from src.indicators.domain.types import AggregationLevel, FocusMetric
from src.shared.domain.value_objects import Money, Period


class GenerateMaterialImpactReportUseCase:
    """Orchestrates calculation of Pareto effort prioritization across dimensions."""

    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        budget_repository: BudgetRepository,
        measurement_repository: MeasurementRepository,
        accounting_account_repository: AccountingAccountRepository,
    ) -> None:
        """Initialize use case with required domain repositories.

        Args:
            cost_center_repository: Repository for cost centers.
            budget_repository: Repository for planned budgets.
            measurement_repository: Repository for approved measurements.
            accounting_account_repository: Repository for accounting accounts.
        """
        self._cost_center_repository = cost_center_repository
        self._budget_repository = budget_repository
        self._measurement_repository = measurement_repository
        self._accounting_account_repository = accounting_account_repository

    async def execute(
        self, query: GenerateMaterialImpactQuery
    ) -> MaterialImpactReportDTO:
        """Generate the materiality and effort focus report.

        Args:
            query: Query parameters for period, aggregation level, metric, and filters.

        Returns:
            MaterialImpactReportDTO: Pareto-ranked effort prioritization report.
        """
        period = Period.from_string(query.period)
        level = AggregationLevel(query.level)
        metric = FocusMetric(query.metric)

        # Validate cost center if filter passed
        if query.cost_center_id is not None:
            cc = await self._cost_center_repository.get_by_id(query.cost_center_id)
            if cc is None or not cc.is_active:
                raise CostCenterNotFoundError(
                    f"Cost center '{query.cost_center_id}' not found."
                )

        budgets = await self._budget_repository.list_by_period(period)
        measurements = await self._measurement_repository.list_by_period(
            period=period, state=MeasurementState.APPROVED
        )

        currency = "USD"
        if budgets:
            currency = budgets[0].amount.currency
        elif measurements and measurements[0].gross_amount:
            currency = measurements[0].gross_amount.currency


        if level == AggregationLevel.COST_CENTER:
            candidates = await self._build_cost_center_candidates(
                query=query,
                budgets=budgets,
                measurements=measurements,
                currency=currency,
            )
        elif level == AggregationLevel.HIERARCHY:
            candidates = await self._build_hierarchy_candidates(
                budgets=budgets,
                measurements=measurements,
                currency=currency,
            )
        else:  # AggregationLevel.ACCOUNTING_ACCOUNT
            candidates = await self._build_accounting_account_candidates(
                query=query,
                budgets=budgets,
                measurements=measurements,
                currency=currency,
            )

        analysis = MaterialityAnalyzer.analyze(
            candidates=candidates,
            metric=metric,
            threshold_pct=query.threshold_pct,
            currency=currency,
        )

        item_dtos = [
            MaterialityItemDTO(
                entity_id=item.entity_id,
                code=item.code,
                name=item.name,
                level=item.level.value,
                planned_budget=(
                    item.planned_budget.amount if item.planned_budget else None
                ),
                actual_spent=item.actual_spent.amount,
                variance=item.variance.amount if item.variance else None,
                metric_value=item.metric_value.amount,
                share_of_total_pct=item.share_of_total_pct,
                cumulative_pct=item.cumulative_pct,
                priority=item.priority.value,
                rank=item.rank,
            )
            for item in analysis.items
        ]

        total_budget_amount: Decimal | None
        if analysis.total_baseline_budget is not None:
            total_budget_amount = analysis.total_baseline_budget.amount
        elif query.cost_center_id is not None:
            scoped_b = sum(
                (b.amount for b in budgets if b.cost_center_id == query.cost_center_id),
                start=Money.zero(currency),
            )
            total_budget_amount = scoped_b.amount
        elif budgets:
            total_budget_amount = sum(
                (b.amount for b in budgets),
                start=Money.zero(currency),
            ).amount
        else:
            total_budget_amount = None

        return MaterialImpactReportDTO(

            period=str(period),
            aggregation_level=level.value,
            focus_metric=metric.value,
            cost_center_scope_id=query.cost_center_id,
            total_baseline_budget=total_budget_amount,
            total_baseline_spent=analysis.total_baseline_spent.amount,
            total_baseline_overrun=analysis.total_baseline_overrun.amount,
            items=item_dtos,
            currency=currency,
        )

    async def _build_cost_center_candidates(
        self,
        query: GenerateMaterialImpactQuery,
        budgets: list[BudgetTarget],
        measurements: list[Measurement],
        currency: str,
    ) -> list[MaterialityCandidate]:

        if query.cost_center_id is not None:
            cc = await self._cost_center_repository.get_by_id(query.cost_center_id)
            cost_centers = [cc] if cc and cc.is_active else []
        else:
            cost_centers = await self._cost_center_repository.list_all(
                active_only=True
            )

        candidates: list[MaterialityCandidate] = []
        for cc in cost_centers:
            cc_budget = sum(
                (b.amount for b in budgets if b.cost_center_id == cc.id),
                start=Money.zero(currency),
            )
            cc_spent = sum(
                (
                    e.amount
                    for m in measurements
                    for e in m.entries
                    if e.cost_center_id == cc.id
                ),
                start=Money.zero(currency),
            )
            variance = cc_spent - cc_budget

            candidates.append(
                MaterialityCandidate(
                    entity_id=cc.id,
                    code=str(cc.code),
                    name=cc.name,
                    level=AggregationLevel.COST_CENTER,
                    planned_budget=cc_budget,
                    actual_spent=cc_spent,
                    variance=variance,
                )
            )
        return candidates

    async def _build_hierarchy_candidates(
        self,
        budgets: list[BudgetTarget],
        measurements: list[Measurement],
        currency: str,
    ) -> list[MaterialityCandidate]:

        all_ccs = await self._cost_center_repository.list_all(active_only=True)
        cc_map = {c.id: c for c in all_ccs}

        def get_root_ancestor(cc: CostCenter) -> CostCenter:
            curr = cc
            visited = set()
            while curr.parent_id is not None and curr.parent_id in cc_map:
                if curr.id in visited:
                    break
                visited.add(curr.id)
                curr = cc_map[curr.parent_id]
            return curr

        root_budgets: dict[UUID, Money] = {}
        root_spends: dict[UUID, Money] = {}
        root_entities: dict[UUID, CostCenter] = {}

        for cc in all_ccs:
            root = get_root_ancestor(cc)
            root_entities[root.id] = root

            cc_budget = sum(
                (b.amount for b in budgets if b.cost_center_id == cc.id),
                start=Money.zero(currency),
            )
            cc_spent = sum(
                (
                    e.amount
                    for m in measurements
                    for e in m.entries
                    if e.cost_center_id == cc.id
                ),
                start=Money.zero(currency),
            )

            root_budgets[root.id] = (
                root_budgets.get(root.id, Money.zero(currency)) + cc_budget
            )
            root_spends[root.id] = (
                root_spends.get(root.id, Money.zero(currency)) + cc_spent
            )

        candidates: list[MaterialityCandidate] = []
        for root_id, root in root_entities.items():
            r_spent = root_spends.get(root_id, Money.zero(currency))
            r_budget = root_budgets.get(root_id, Money.zero(currency))
            variance = r_spent - r_budget

            candidates.append(
                MaterialityCandidate(
                    entity_id=root.id,
                    code=str(root.code),
                    name=root.name,
                    level=AggregationLevel.HIERARCHY,
                    planned_budget=r_budget,
                    actual_spent=r_spent,
                    variance=variance,
                )
            )
        return candidates

    async def _build_accounting_account_candidates(
        self,
        query: GenerateMaterialImpactQuery,
        budgets: list[BudgetTarget],
        measurements: list[Measurement],
        currency: str,
    ) -> list[MaterialityCandidate]:

        if query.cost_center_id is not None:
            target_cc_id = query.cost_center_id
            cc_budget = sum(
                (b.amount for b in budgets if b.cost_center_id == target_cc_id),
                start=Money.zero(currency),
            )
            cc_entries = [
                e
                for m in measurements
                for e in m.entries
                if e.cost_center_id == target_cc_id
            ]
            cc_spent = sum(
                (e.amount for e in cc_entries),
                start=Money.zero(currency),
            )
            cc_overrun = (
                cc_spent - cc_budget
                if (cc_spent - cc_budget).amount > Decimal("0.00")
                else Money.zero(currency)
            )

            acc_spends: dict[UUID | None, Money] = {}
            for e in cc_entries:
                acc_id = e.accounting_account_id
                acc_spends[acc_id] = (
                    acc_spends.get(acc_id, Money.zero(currency)) + e.amount
                )

            candidates: list[MaterialityCandidate] = []
            for acc_id, spent in acc_spends.items():
                acc_code, acc_name = await self._resolve_account(acc_id)
                has_positive_overrun = (
                    cc_spent.amount > Decimal("0.00")
                    and cc_overrun.amount > Decimal("0.00")
                )
                if has_positive_overrun:
                    ratio = spent.amount / cc_spent.amount
                    acc_variance = Money(
                        (cc_overrun.amount * ratio).quantize(Decimal("0.01")),
                        currency,
                    )
                else:
                    acc_variance = Money.zero(currency)


                candidates.append(
                    MaterialityCandidate(
                        entity_id=acc_id,
                        code=acc_code,
                        name=acc_name,
                        level=AggregationLevel.ACCOUNTING_ACCOUNT,
                        planned_budget=None,
                        actual_spent=spent,
                        variance=acc_variance,
                    )
                )
            return candidates

        # Global accounting account aggregation
        cc_budgets: dict[UUID, Money] = {}
        for b in budgets:
            cc_budgets[b.cost_center_id] = (
                cc_budgets.get(b.cost_center_id, Money.zero(currency)) + b.amount
            )

        cc_spends: dict[UUID, Money] = {}
        acc_spends: dict[UUID | None, Money] = {}
        entries_by_cc: dict[UUID, list[AllocationEntry]] = {}

        for m in measurements:
            for e in m.entries:
                cc_spends[e.cost_center_id] = (
                    cc_spends.get(e.cost_center_id, Money.zero(currency)) + e.amount
                )
                acc_spends[e.accounting_account_id] = (
                    acc_spends.get(e.accounting_account_id, Money.zero(currency))
                    + e.amount
                )
                entries_by_cc.setdefault(e.cost_center_id, []).append(e)

        acc_overruns: dict[UUID | None, Money] = {}
        for c_id, c_spent in cc_spends.items():
            c_budget = cc_budgets.get(c_id, Money.zero(currency))
            c_overrun = (
                c_spent - c_budget
                if (c_spent - c_budget).amount > Decimal("0.00")
                else Money.zero(currency)
            )
            if c_spent.amount > Decimal("0.00") and c_overrun.amount > Decimal("0.00"):
                for e in entries_by_cc.get(c_id, []):
                    acc_id = e.accounting_account_id
                    ratio = e.amount.amount / c_spent.amount
                    contrib = (c_overrun.amount * ratio).quantize(Decimal("0.01"))
                    acc_overruns[acc_id] = (
                        acc_overruns.get(acc_id, Money.zero(currency))
                        + Money(contrib, currency)
                    )

        candidates = []
        for acc_id, spent in acc_spends.items():
            acc_code, acc_name = await self._resolve_account(acc_id)
            variance = acc_overruns.get(acc_id, Money.zero(currency))
            candidates.append(
                MaterialityCandidate(
                    entity_id=acc_id,
                    code=acc_code,
                    name=acc_name,
                    level=AggregationLevel.ACCOUNTING_ACCOUNT,
                    planned_budget=None,
                    actual_spent=spent,
                    variance=variance,
                )
            )
        return candidates

    async def _resolve_account(self, acc_id: UUID | None) -> tuple[str, str]:
        if acc_id is None:
            return ("UNASSIGNED", "Não Classificado")
        account = await self._accounting_account_repository.get_by_id(acc_id)
        if account is not None:
            return (str(account.code), account.name)
        return ("UNKNOWN", "Conta Desconhecida")
