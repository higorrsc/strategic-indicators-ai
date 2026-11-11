from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import (
    AllocationShareDTO,
    ApproveMeasurementCommand,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.application.use_cases import (
    ApproveMeasurementUseCase,
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    Measurement,
    MeasurementState,
)
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import (
    InvalidAllocationPercentageError,
    InvalidMeasurementStateError,
)
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
)
from src.shared.domain.value_objects import Money, Percentage, Period


class TestExactPennyAllocator:
    def test_should_reconcile_rounding_across_three_shares(self) -> None:
        cc1, cc2, cc3 = uuid4(), uuid4(), uuid4()
        shares = [
            AllocationShare(
                cost_center_id=cc1, percentage=Percentage.from_number("33.33")
            ),
            AllocationShare(
                cost_center_id=cc2, percentage=Percentage.from_number("33.33")
            ),
            AllocationShare(
                cost_center_id=cc3, percentage=Percentage.from_number("33.34")
            ),
        ]
        gross = Money.from_float_or_int(1000, "USD")
        entries = ExactPennyAllocator.allocate(gross, shares)

        total_allocated = sum((e.amount for e in entries), Money.zero("USD"))
        assert total_allocated == gross
        assert len(entries) == 3

    def test_should_reject_shares_not_summing_to_hundred(self) -> None:
        shares = [
            AllocationShare(
                cost_center_id=uuid4(), percentage=Percentage.from_number("50.00")
            ),
            AllocationShare(
                cost_center_id=uuid4(), percentage=Percentage.from_number("45.00")
            ),
        ]
        with pytest.raises(InvalidAllocationPercentageError):
            ExactPennyAllocator.allocate(Money.from_float_or_int(100), shares)


class TestContractAndMeasurementEntities:
    def test_should_enforce_contract_default_allocation_integrity(self) -> None:
        sup_id = uuid4()
        cc1, cc2 = uuid4(), uuid4()
        valid_shares = [
            AllocationShare(
                cost_center_id=cc1, percentage=Percentage.from_number("70.00")
            ),
            AllocationShare(
                cost_center_id=cc2, percentage=Percentage.from_number("30.00")
            ),
        ]
        contract = Contract(
            code="CT-001",
            supplier_id=sup_id,
            title="Cloud Hosting",
            default_allocations=valid_shares,
        )
        assert len(contract.default_allocations) == 2

    def test_should_reject_invalid_measurement_state_transition(self) -> None:
        measurement = Measurement(
            contract_id=uuid4(),
            period=Period.from_string("2026-03"),
            description="March Hosting",
            gross_amount=Money.from_float_or_int(1000),
        )
        assert measurement.state == MeasurementState.DRAFT
        # Cannot approve while in DRAFT
        with pytest.raises(InvalidMeasurementStateError):
            measurement.approve()


@pytest.mark.asyncio
class TestAllocationUseCases:
    async def test_should_register_contract_and_submit_with_override(self) -> None:
        sup_repo = InMemorySupplierRepository()
        contract_repo = InMemoryContractRepository()
        measurement_repo = InMemoryMeasurementRepository()

        supplier = Supplier(name="Cloud Corp", tax_id="12.345.678/0001-90")
        await sup_repo.add(supplier)

        cc1, cc2, cc3 = uuid4(), uuid4(), uuid4()

        reg_contract_use_case = RegisterContractUseCase(contract_repo, sup_repo)
        contract_dto = await reg_contract_use_case.execute(
            RegisterContractCommand(
                code="CT-2026-01",
                supplier_id=supplier.id,
                title="Cloud Infrastructure",
                default_allocations=[
                    AllocationShareDTO(cost_center_id=cc1, percentage=Decimal("80.00")),
                    AllocationShareDTO(cost_center_id=cc2, percentage=Decimal("20.00")),
                ],
            )
        )
        assert contract_dto.code == "CT-2026-01"

        submit_use_case = SubmitMeasurementUseCase(measurement_repo, contract_repo)
        # Custom override: allocate 50% to cc1, 50% to cc3
        measurement_dto = await submit_use_case.execute(
            SubmitMeasurementCommand(
                contract_id=contract_dto.id,
                period="2026-03",
                description="March Cloud Bill",
                gross_amount=Decimal("15000.00"),
                custom_allocations=[
                    AllocationShareDTO(cost_center_id=cc1, percentage=Decimal("50.00")),
                    AllocationShareDTO(cost_center_id=cc3, percentage=Decimal("50.00")),
                ],
            )
        )

        assert measurement_dto.state == "SUBMITTED"
        assert len(measurement_dto.entries) == 2
        assert measurement_dto.entries[0].amount == Decimal("7500.00")
        assert measurement_dto.entries[1].amount == Decimal("7500.00")

        # Approve measurement
        approve_use_case = ApproveMeasurementUseCase(measurement_repo)
        approved_dto = await approve_use_case.execute(
            ApproveMeasurementCommand(measurement_id=measurement_dto.id)
        )
        assert approved_dto.state == "APPROVED"
