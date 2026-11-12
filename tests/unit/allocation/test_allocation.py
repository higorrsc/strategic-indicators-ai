from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import (
    AllocationShareDTO,
    ApproveMeasurementCommand,
    ListContractsQuery,
    ListMeasurementsQuery,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.application.use_cases import (
    ApproveMeasurementUseCase,
    ListContractsUseCase,
    ListMeasurementsUseCase,
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
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


class TestInMemoryMeasurementRepositoryFind:
    @pytest.mark.asyncio
    async def test_should_filter_measurements_by_criteria(self) -> None:
        repo = InMemoryMeasurementRepository()
        ct1, ct2 = uuid4(), uuid4()
        cc_id = uuid4()

        m1 = Measurement(
            contract_id=ct1,
            period=Period(2026, 4),
            description="M1",
            gross_amount=Money(Decimal("100.00")),
        )
        m1.set_entries(
            [
                AllocationEntry(
                    cost_center_id=cc_id,
                    amount=Money(Decimal("100.00")),
                    percentage=Percentage(Decimal("100.00")),
                )
            ]
        )
        m1.submit()
        m1.approve()
        await repo.add(m1)

        m2 = Measurement(
            contract_id=ct1,
            period=Period(2026, 4),
            description="M2",
            gross_amount=Money(Decimal("200.00")),
        )
        m2.set_entries(
            [
                AllocationEntry(
                    cost_center_id=cc_id,
                    amount=Money(Decimal("200.00")),
                    percentage=Percentage(Decimal("100.00")),
                )
            ]
        )
        m2.submit()
        await repo.add(m2)

        m3 = Measurement(
            contract_id=ct2,
            period=Period(2026, 5),
            description="M3",
            gross_amount=Money(Decimal("300.00")),
        )
        await repo.add(m3)

        assert len(await repo.find(period=Period(2026, 4))) == 2
        assert (
            len(await repo.find(contract_id=ct1, state=MeasurementState.APPROVED)) == 1
        )
        assert len(await repo.find(period=Period(2026, 5))) == 1
        assert len(await repo.find(contract_id=uuid4())) == 0


class TestListContractsUseCase:
    @pytest.mark.asyncio
    async def test_should_list_contracts_with_filters(self) -> None:
        repo = InMemoryContractRepository()
        sup1, sup2 = uuid4(), uuid4()

        c1 = Contract(
            code="CT-01", supplier_id=sup1, title="Active Sup1", is_active=True
        )
        c2 = Contract(
            code="CT-02", supplier_id=sup1, title="Inactive Sup1", is_active=False
        )
        c3 = Contract(
            code="CT-03", supplier_id=sup2, title="Active Sup2", is_active=True
        )
        await repo.add(c1)
        await repo.add(c2)
        await repo.add(c3)

        use_case = ListContractsUseCase(repo)

        # Default: active only
        active = await use_case.execute()
        assert len(active.items) == 2
        assert active.total_items == 2
        assert active.page == 1
        assert active.per_page == 20

        # All contracts
        all_contracts = await use_case.execute(ListContractsQuery(active_only=False))
        assert len(all_contracts.items) == 3
        assert all_contracts.total_items == 3

        # Filter by supplier
        sup1_active = await use_case.execute(
            ListContractsQuery(supplier_id=sup1, active_only=True)
        )
        assert len(sup1_active.items) == 1
        assert sup1_active.items[0].code == "CT-01"

        # Pagination slicing
        paginated = await use_case.execute(
            ListContractsQuery(active_only=False, page=1, per_page=2)
        )
        assert len(paginated.items) == 2
        assert paginated.total_items == 3
        assert paginated.page == 1
        assert paginated.per_page == 2


class TestListMeasurementsUseCase:
    @pytest.mark.asyncio
    async def test_should_list_measurements_with_filters(self) -> None:
        repo = InMemoryMeasurementRepository()
        ct1 = uuid4()
        cc_id = uuid4()

        m1 = Measurement(
            contract_id=ct1,
            period=Period(2026, 3),
            description="March Bill",
            gross_amount=Money(Decimal("1000.00")),
        )
        m1.set_entries(
            [
                AllocationEntry(
                    cost_center_id=cc_id,
                    amount=Money(Decimal("1000.00")),
                    percentage=Percentage(Decimal("100.00")),
                )
            ]
        )
        m1.submit()
        m1.approve()
        await repo.add(m1)

        use_case = ListMeasurementsUseCase(repo)

        res = await use_case.execute(ListMeasurementsQuery(period="2026-03"))
        assert len(res.items) == 1
        assert res.total_items == 1
        assert res.page == 1
        assert res.per_page == 20
        assert res.items[0].description == "March Bill"
        assert res.items[0].state == "APPROVED"
        assert len(res.items[0].entries) == 1
