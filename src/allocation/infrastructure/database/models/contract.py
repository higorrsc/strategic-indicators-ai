"""SQLAlchemy models for Contracts and default allocations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .accounting_account import AccountingAccountModel
    from .measurement import MeasurementModel
    from .supplier import SupplierModel


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
    accounting_account_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("accounting_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)

    contract: Mapped[ContractModel] = relationship(
        "ContractModel",
        back_populates="default_allocations",
    )
    accounting_account: Mapped[AccountingAccountModel | None] = relationship(
        "AccountingAccountModel",
    )
