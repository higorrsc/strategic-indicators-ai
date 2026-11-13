"""SQLAlchemy models for Measurements and Allocation Entries."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .accounting_account import AccountingAccountModel
    from .contract import ContractModel


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
    accounting_account_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("accounting_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)

    measurement: Mapped[MeasurementModel] = relationship(
        "MeasurementModel",
        back_populates="entries",
    )
    accounting_account: Mapped[AccountingAccountModel | None] = relationship(
        "AccountingAccountModel",
    )
