"""SQLAlchemy model for Suppliers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .contract import ContractModel


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
