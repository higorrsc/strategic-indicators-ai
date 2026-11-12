"""SQLAlchemy ORM models for Cost Allocation Bounded Context."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class SupplierModel(Base):
    """SQLAlchemy model representing a contracting supplier/vendor."""

    __tablename__ = "suppliers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    contracts: Mapped[list[ContractModel]] = relationship(
        "ContractModel",
        back_populates="supplier",
    )


class ContractModel(Base):
    """SQLAlchemy model representing a supplier agreement with default allocations."""

    __tablename__ = "contracts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier: Mapped[SupplierModel] = relationship(
        "SupplierModel",
        back_populates="contracts",
    )
    default_allocations: Mapped[list[ContractAllocationModel]] = relationship(
        "ContractAllocationModel",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    measurements: Mapped[list[MeasurementModel]] = relationship(
        "MeasurementModel",
        back_populates="contract",
    )


class ContractAllocationModel(Base):
    """SQLAlchemy model representing default allocation percentage shares."""

    __tablename__ = "contract_default_allocations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    contract_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_center_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)

    contract: Mapped[ContractModel] = relationship(
        "ContractModel",
        back_populates="default_allocations",
    )


class MeasurementModel(Base):
    """SQLAlchemy model representing financial measurements and invoice splits."""

    __tablename__ = "measurements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    contract_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("contracts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    state: Mapped[str] = mapped_column(
        String(20), default="DRAFT", nullable=False, index=True
    )

    contract: Mapped[ContractModel] = relationship(
        "ContractModel",
        back_populates="measurements",
    )
    entries: Mapped[list[AllocationEntryModel]] = relationship(
        "AllocationEntryModel",
        back_populates="measurement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AllocationEntryModel(Base):
    """SQLAlchemy model representing an allocated expense entry to a cost center."""

    __tablename__ = "measurement_allocation_entries"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    measurement_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("measurements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_center_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)

    measurement: Mapped[MeasurementModel] = relationship(
        "MeasurementModel",
        back_populates="entries",
    )
