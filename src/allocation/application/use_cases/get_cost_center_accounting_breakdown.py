"""Use case for retrieving cost center expenditures broken down by account."""

from decimal import Decimal
from uuid import UUID

from src.allocation.application.dto import (
    CostCenterAccountingBreakdownDTO,
    CostCenterAccountSpendDTO,
)
from src.allocation.domain.entities.measurement import MeasurementState
from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.shared.domain.value_objects import Period


class GetCostCenterAccountingBreakdownUseCase:
    """Calculates expenditure breakdown by account for a cost center in a period."""

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        accounting_account_repository: AccountingAccountRepository,
    ) -> None:
        """Initialize use case with measurement and accounting account repositories.

        Args:
            measurement_repository: Repository to fetch approved measurements.
            accounting_account_repository: Repository to resolve accounting accounts.
        """
        self._measurement_repository = measurement_repository
        self._accounting_account_repository = accounting_account_repository

    async def execute(
        self, cost_center_id: UUID, period_str: str
    ) -> CostCenterAccountingBreakdownDTO:
        """Execute calculation of accounting account breakdown for a cost center.

        Args:
            cost_center_id: Target Cost Center UUID.
            period_str: Fiscal period string (e.g. "2026-03").

        Returns:
            CostCenterAccountingBreakdownDTO: Aggregated account breakdown.
        """
        period = Period.from_string(period_str)
        measurements = await self._measurement_repository.list_by_period(
            period=period, state=MeasurementState.APPROVED
        )

        # Aggregate amounts by accounting_account_id for the target cost center
        grouped_amounts: dict[UUID | None, Decimal] = {}
        total_spent = Decimal("0.00")

        for m in measurements:
            for entry in m.entries:
                if entry.cost_center_id == cost_center_id:
                    amt = entry.amount.amount
                    total_spent += amt
                    acc_id = entry.accounting_account_id
                    current = grouped_amounts.get(acc_id, Decimal("0.00"))
                    grouped_amounts[acc_id] = current + amt

        account_dtos: list[CostCenterAccountSpendDTO] = []
        for acc_id, spent in grouped_amounts.items():
            acc_code: str | None = None
            acc_name: str | None = None

            if acc_id is not None:
                account = await self._accounting_account_repository.get_by_id(acc_id)
                if account is not None:
                    acc_code = str(account.code)
                    acc_name = account.name
                else:
                    acc_code = "UNKNOWN"
                    acc_name = "Conta Desconhecida"
            else:
                acc_code = "UNASSIGNED"
                acc_name = "Não Classificado"

            share_pct = (
                (spent / total_spent * Decimal("100.00")).quantize(Decimal("0.01"))
                if total_spent > Decimal("0.00")
                else Decimal("0.00")
            )

            account_dtos.append(
                CostCenterAccountSpendDTO(
                    accounting_account_id=acc_id,
                    account_code=acc_code,
                    account_name=acc_name,
                    spent_amount=spent,
                    share_pct=share_pct,
                )
            )

        # Sort accounts descending by spent amount
        account_dtos.sort(key=lambda a: a.spent_amount, reverse=True)

        return CostCenterAccountingBreakdownDTO(
            cost_center_id=cost_center_id,
            period=str(period),
            total_spent=total_spent,
            accounts=account_dtos,
        )
